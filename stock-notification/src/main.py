#!/usr/bin/env python3
"""
股票分析 Agent - 主入口

功能：
1. 实时监控财经新闻，分析利好板块
2. 监控板块主力资金流入情况
3. 推荐龙头股
4. 生成投资报告

⚠️ 免责声明：仅供学习研究，不构成投资建议
"""
import os
import sys
import yaml
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

# 添加 src 到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from news_monitor import NewsMonitor
from capital_flow import CapitalFlowAnalyzer
from stock_selector import StockSelector
from stock_monitor import StockMonitor
from report_generator import ReportGenerator
from tushare_source import TushareSource
from akshare_source import AKShareSource
from enhanced_data_source import EnhancedDataSource
from tushare_pro_source import TushareProSource


class StockAgent:
    """股票分析 Agent 主类"""
    
    def __init__(self, config_path: str = '../config.yaml'):
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 初始化各模块
        self.news_monitor = NewsMonitor(self.config.get('news_keywords', {}))
        
        # 初始化 AKShare（优先使用，免费无需 Token）
        akshare_config = self.config.get('akshare', {})
        if akshare_config.get('enabled', True):
            try:
                cache_dir = akshare_config.get('cache_dir')
                cache_ttl = akshare_config.get('cache_ttl', 300)
                max_retries = akshare_config.get('max_retries', 3)
                self.akshare_source = AKShareSource(
                    cache_dir=cache_dir,
                    cache_ttl=cache_ttl,
                    max_retries=max_retries
                )
                print(f"[AKShare] ✅ 已初始化 - 缓存 TTL: {cache_ttl}s, 重试：{max_retries}")
            except ImportError as e:
                self.akshare_source = None
                print(f"[AKShare] ⚠️ 未安装：{e}")
                print("[AKShare] 请运行：pip install akshare")
        else:
            self.akshare_source = None
            print("[AKShare] 已禁用")
        
        # 初始化资金流分析器（支持 AKShare + 缓存）
        self.capital_analyzer = CapitalFlowAnalyzer(
            cache_dir=akshare_config.get('cache_dir') if self.akshare_source else None,
            cache_ttl=akshare_config.get('cache_ttl', 300),
            max_retries=akshare_config.get('max_retries', 3)
        )
        
        # 初始化增强数据源（ETF、北向资金、宏观数据等）
        try:
            self.enhanced = EnhancedDataSource(
                cache_dir=akshare_config.get('cache_dir'),
                cache_ttl=akshare_config.get('cache_ttl', 300)
            )
            print(f"[增强数据源] ✅ 已初始化 - ETF/北向/宏观数据可用")
        except ImportError as e:
            self.enhanced = None
            print(f"[增强数据源] ⚠️ 未启用：{e}")
        
        self.stock_selector = StockSelector()
        
        # 初始化股票监控器（用于个股重点监控）
        self.stock_monitor = StockMonitor(
            cache_dir=akshare_config.get('cache_dir'),
            cache_ttl=akshare_config.get('cache_ttl', 300)
        )
        print(f"[股票监控] ✅ 已初始化 - 支持日 K/分时/新闻/资金博弈分析")
        
        # 初始化 Tushare Pro（600 积分 - 主要数据源）
        tushare_config = self.config.get('tushare', {})
        if tushare_config.get('enabled', True):
            token = tushare_config.get('token') or os.getenv('TUSHARE_TOKEN')
            if token:
                try:
                    cache_dir = tushare_config.get('cache', {}).get('enabled', True) and akshare_config.get('cache_dir')
                    cache_ttl = tushare_config.get('cache', {}).get('ttl_seconds', 300)
                    self.tushare_pro = TushareProSource(
                        token=token,
                        cache_dir=cache_dir,
                        cache_ttl=cache_ttl
                    )
                    print(f"[Tushare Pro] ✅ 已连接 - 积分：{self.tushare_pro.token_info.get('total_points', 'N/A')} (VIP: {self.tushare_pro.token_info.get('vip_level', 'N/A')})")
                except Exception as e:
                    self.tushare_pro = None
                    print(f"[Tushare Pro] ⚠️ 初始化失败：{e}")
            else:
                self.tushare_pro = None
                print("[Tushare Pro] ⚠️ 未配置 Token")
        else:
            self.tushare_pro = None
        
        # 初始化 Tushare（备用，旧版）
        if not self.tushare_pro and tushare_config.get('enabled', False):
            token = tushare_config.get('token') or os.getenv('TUSHARE_TOKEN')
            if token:
                self.tushare_source = TushareSource(token)
                token_info = self.tushare_source.get_token_info()
                if token_info:
                    print(f"[Tushare] ✅ 已连接 - 积分：{token_info['total_points']} (VIP: {token_info['vip_level']})")
            else:
                self.tushare_source = None
                print("[Tushare] ⚠️ 未配置 Token")
        else:
            self.tushare_source = None
        
        # 使用绝对路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(script_dir)
        self.report_generator = ReportGenerator(
            output_dir=os.path.join(project_dir, 'data', 'reports')
        )
        
        # 确保输出目录存在
        os.makedirs(os.path.join(project_dir, 'data', 'reports'), exist_ok=True)
        os.makedirs(os.path.join(project_dir, 'logs'), exist_ok=True)
        
        print("=" * 60)
        print("🚀 股票分析 Agent 已启动")
        print("=" * 60)
        
        # 显示数据源优先级
        # 注：东方财富 (连接失败)、新浪财经 (403 错误) 已禁用 - 2026-03-16
        sources = []
        if self.tushare_pro:
            sources.append("Tushare Pro (主)")
        if self.akshare_source:
            sources.append("AKShare(免费)")
        if self.tushare_source:
            sources.append("Tushare")
        sources.extend(["腾讯财经", "同花顺"])
        
        print(f"数据源优先级：{' > '.join(sources)}")
        print(f"缓存：已启用 (TTL: {akshare_config.get('cache_ttl', 300)}s)")
        print(f"重试：{akshare_config.get('max_retries', 3)}次")
        print(f"已禁用：东方财富 (连接失败), 新浪财经 (403 错误)")
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        try:
            # 尝试相对路径
            config_file = Path(config_path)
            if not config_file.exists():
                # 尝试相对于脚本目录
                script_dir = Path(__file__).parent
                config_file = script_dir / config_path
            
            if not config_file.exists():
                print(f"[配置] 未找到配置文件，使用默认配置")
                return {}
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            print(f"[配置] 已加载：{config_file}")
            return config
            
        except Exception as e:
            print(f"[配置] 加载失败：{e}")
            return {}
    
    def _get_news_from_akshare(self) -> dict:
        """从 AKShare 获取新闻并转换为内部格式"""
        if not self.akshare_source:
            return {}
        
        try:
            today = datetime.now().strftime('%Y%m%d')
            news_list = self.akshare_source.get_news(start_date=today, end_date=today)
            
            if not news_list:
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
                news_list = self.akshare_source.get_news(start_date=yesterday, end_date=yesterday)
            
            if not news_list:
                return {}
            
            sector_news = self.news_monitor.extract_sectors(news_list)
            result = self.news_monitor.get_sector_sentiment(sector_news)
            
            print(f"[AKShare] 新闻分析完成，覆盖 {len(result)} 个板块")
            return result
            
        except Exception as e:
            print(f"[AKShare] 新闻分析失败：{e}")
            return {}
    
    def _get_news_from_tushare(self) -> dict:
        """从 Tushare 获取新闻并转换为内部格式（备用）"""
        if not self.tushare_source:
            return {}
        
        try:
            today = datetime.now().strftime('%Y%m%d')
            news_list = self.tushare_source.get_news(start_date=today, end_date=today, src='sina')
            
            if not news_list:
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
                news_list = self.tushare_source.get_news(start_date=yesterday, end_date=yesterday, src='sina')
            
            if not news_list:
                return {}
            
            sector_news = self.news_monitor.extract_sectors(news_list)
            result = self.news_monitor.get_sector_sentiment(sector_news)
            
            print(f"[Tushare] 新闻分析完成，覆盖 {len(result)} 个板块")
            return result
            
        except Exception as e:
            print(f"[Tushare] 新闻分析失败：{e}")
            return {}
    
    def _get_flow_from_tushare_pro(self, sectors: List[str], threshold: int = 5000) -> Dict:
        """从 Tushare Pro 获取资金流数据"""
        if not self.tushare_pro:
            return {}
        
        from capital_flow import CapitalFlowAnalyzer
        
        print(f"[Tushare Pro] 分析 {len(sectors)} 个板块资金流...")
        
        results = {}
        successful = []
        failed = []
        
        today = datetime.now().strftime('%Y%m%d')
        
        for sector in sectors:
            try:
                # 获取板块成分股（需要手动映射或使用行业指数）
                # 这里简化处理，使用资金流分析器的本地成分股
                sector_stocks = self.capital_analyzer.get_sector_stocks(sector)
                
                if not sector_stocks:
                    failed.append(sector)
                    continue
                
                # 获取每只股票的资金流
                total_inflow = 0
                total_outflow = 0
                stocks_with_flow = []
                
                for stock in sector_stocks[:10]:  # 限制每板块 10 只
                    ts_code = stock.get('ts_code', '')
                    if ts_code:
                        flow = self.tushare_pro.get_moneyflow(ts_code=ts_code, trade_date=today)
                        if flow:
                            net = flow.get('net_mf_amount', 0)
                            if net > 0:
                                total_inflow += net
                            else:
                                total_outflow += abs(net)
                            stocks_with_flow.append({
                                **stock,
                                'net_mf_amount': net
                            })
                
                net_flow = total_inflow - total_outflow
                
                # 排序找出龙头
                stocks_with_flow.sort(key=lambda x: x.get('net_mf_amount', 0), reverse=True)
                
                results[sector] = {
                    'flow': {
                        'sector': sector,
                        'stock_count': len(sector_stocks),
                        'stocks_with_flow': len(stocks_with_flow),
                        'total_inflow': total_inflow,
                        'total_outflow': total_outflow,
                        'net_flow': net_flow,
                        'trend': '流入' if net_flow > 0 else '流出',
                        'update_time': datetime.now().isoformat()
                    },
                    'leader': stocks_with_flow[0] if stocks_with_flow else None
                }
                
                successful.append(sector)
                print(f"   ✅ {sector}: 净流入 {net_flow/10000:.1f}万")
                
            except Exception as e:
                print(f"   ❌ {sector}: {e}")
                failed.append(sector)
        
        return {
            'sector_analysis': results,
            'top_inflow_sectors': sorted(
                [{'sector': s, 'net_flow': r['flow']['net_flow']} for s, r in results.items()],
                key=lambda x: x['net_flow'],
                reverse=True
            ),
            'successful_sectors': successful,
            'failed_sectors': failed,
            'update_time': datetime.now().isoformat()
        }
    
    def run_analysis(self) -> dict:
        """执行一次完整分析（Tushare Pro 增强版）"""
        print(f"\n{'='*60}")
        print(f"📊 开始分析 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        try:
            sectors = self.config.get('sectors', ['半导体', '人工智能', '新能源', '医药生物'])
            
            # 1. 新闻监控（优先级：网页抓取 > Tushare Pro（限流））
            news_result = {}
            
            # 网页抓取优先（避免 Tushare 限流）
            print("[新闻] 使用网页抓取新闻...")
            news_result = self.news_monitor.run()
            
            # Tushare Pro 作为备用（如果开启）
            tushare_config = self.config.get('tushare', {})
            if not news_result and self.tushare_pro and tushare_config.get('features', {}).get('news', False):
                print("[新闻] 网页抓取失败，使用 Tushare Pro...")
                today = datetime.now().strftime('%Y%m%d')
                news_list = self.tushare_pro.get_news(start_date=today, end_date=today, src='sina')
                if news_list:
                    sector_news = self.news_monitor.extract_sectors(news_list)
                    news_result = self.news_monitor.get_sector_sentiment(sector_news)
            
            # 2. 资金流分析（AKShare 优先，Tushare 备用）
            threshold = self.config.get('capital_flow', {}).get('threshold_inflow', 5000)
            flow_result = self.capital_analyzer.run(sectors, threshold)
            
            # 3. 增强数据（Tushare Pro + AKShare）
            extra_data = {}
            
            # Tushare Pro 数据（仅宏观等稳定接口）
            if self.tushare_pro:
                print("[Tushare Pro] 获取宏观数据...")
                try:
                    # 宏观经济（稳定，不限流）
                    extra_data['gdp'] = self.tushare_pro.get_cn_gdp()
                    extra_data['cpi'] = self.tushare_pro.get_cn_cpi()
                    print(f"   - 宏观：GDP {len(extra_data['gdp'])}年，CPI {len(extra_data['cpi'])}月")
                    
                except Exception as e:
                    print(f"   ⚠️ Tushare Pro 宏观数据获取失败：{e}")
            
            # AKShare 增强数据（北向资金等）
            if self.enhanced:
                print("[增强数据] 获取北向资金...")
                try:
                    extra_data['north_flow'] = self.enhanced.get_north_top_stocks(top_n=10)
                    if extra_data['north_flow']:
                        print(f"   - 北向：{len(extra_data['north_flow'])} 只持仓股")
                except Exception as e:
                    print(f"   ⚠️ 北向资金获取失败：{e}")
            
            # 4. 选股
            recommendations = self.stock_selector.run(news_result, flow_result)
            
            # 5. 生成报告（包含增强数据）
            report_result = self.report_generator.run(
                news_result, 
                flow_result, 
                recommendations,
                extra_data=extra_data
            )
            
            print(f"\n{'='*60}")
            print("✅ 分析完成")
            print(f"{'='*60}")
            print(f"📄 报告路径：{report_result['report_path']}")
            print(f"📊 数据路径：{report_result['data_path']}")
            
            return {
                'success': True,
                'news': news_result,
                'flow': flow_result,
                'recommendations': recommendations,
                'extra_data': extra_data,
                'report_path': report_result['report_path']
            }
            
        except Exception as e:
            print(f"\n❌ 分析失败：{e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def is_trading_time(self) -> bool:
        """判断是否在交易时间"""
        now = datetime.now()
        
        # 只在工作日运行
        if now.weekday() >= 5:  # 周六=5, 周日=6
            return False
        
        # 交易时间判断
        trading_hours = self.config.get('trading_hours', {})
        morning_start = trading_hours.get('morning_start', '09:30')
        morning_end = trading_hours.get('morning_end', '11:30')
        afternoon_start = trading_hours.get('afternoon_start', '13:00')
        afternoon_end = trading_hours.get('afternoon_end', '15:00')
        
        current_time = now.strftime('%H:%M')
        
        is_morning = morning_start <= current_time <= morning_end
        is_afternoon = afternoon_start <= current_time <= afternoon_end
        
        return is_morning or is_afternoon
    
    def run_scheduled(self, interval_minutes: int = 30):
        """定时运行（默认每 30 分钟）"""
        print(f"\n⏰ 启动定时任务 - 每{interval_minutes}分钟执行一次")
        print("按 Ctrl+C 停止\n")
        
        # 立即执行一次
        self.run_analysis()
        
        # 设置定时任务
        schedule.every(interval_minutes).minutes.do(self.run_analysis)
        
        # 保持运行
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    def run_once(self):
        """只运行一次"""
        return self.run_analysis()
    
    def monitor_stocks(self, stock_list: List[Dict], export_report: bool = True) -> Dict:
        """监控指定股票清单并提供买卖建议
        
        Args:
            stock_list: 股票列表，格式 [{'code': '000001', 'name': '平安银行'}, ...]
            export_report: 是否导出报告
        
        Returns:
            监控结果
        """
        print(f"\n{'='*60}")
        print(f"🎯 个股重点监控 - {len(stock_list)} 只股票")
        print(f"{'='*60}\n")
        
        try:
            # 执行监控
            results = self.stock_monitor.monitor_stocks(stock_list)
            
            # 导出报告
            report_path = None
            if export_report:
                report_path = self.stock_monitor.export_report(results)
            
            # 统计买卖信号
            buy_signals = [r for r in results if r.get('signal', {}).get('action_code') in ['BUY', 'STRONG_BUY']]
            sell_signals = [r for r in results if r.get('signal', {}).get('action_code') in ['SELL', 'STRONG_SELL']]
            hold_signals = [r for r in results if r.get('signal', {}).get('action_code') == 'HOLD']
            
            print(f"\n📊 信号统计:")
            print(f"  买入：{len(buy_signals)} 只")
            print(f"  持有：{len(hold_signals)} 只")
            print(f"  卖出：{len(sell_signals)} 只")
            
            # 显示买入信号详情
            if buy_signals:
                print(f"\n🔴 买入信号详情:")
                for r in buy_signals:
                    signal = r.get('signal', {})
                    stock = r.get('stock_info', {})
                    print(f"  {r.get('name')}({r.get('code')}): {signal.get('action')} "
                          f"(得分：{signal.get('score')}, 目标：{signal.get('target_price')})")
            
            return {
                'success': True,
                'results': results,
                'report_path': report_path,
                'summary': {
                    'total': len(results),
                    'buy': len(buy_signals),
                    'hold': len(hold_signals),
                    'sell': len(sell_signals)
                }
            }
            
        except Exception as e:
            print(f"\n❌ 监控失败：{e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}


def main():
    """主函数 - 统一入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='📊 股票分析 Agent - 推荐 + 监控',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
功能模块:
  recommend   股票推荐 - 基于市场分析推荐潜力股票
  monitor     股票监控 - 实时监控持仓股票

示例:
  python main.py recommend --once           运行一次推荐
  python main.py recommend -i 30            每 30 分钟推荐一次
  python main.py monitor --once             监控一次持仓
  python main.py monitor -i 300             每 5 分钟监控一次
  python main.py monitor -s 002181,300058   监控指定股票
  
快捷方式:
  python recommend.py --once                直接运行推荐
  python monitor.py --once                  直接运行监控
        '''
    )
    
    parser.add_argument('module', nargs='?', choices=['recommend', 'monitor'], 
                       help='功能模块 (recommend|monitor)')
    parser.add_argument('--config', '-c', default='config.yaml', help='配置文件路径')
    parser.add_argument('--once', action='store_true', help='只运行一次')
    parser.add_argument('--interval', '-i', type=int, default=0, help='运行间隔')
    parser.add_argument('--stocks', '-s', type=str, help='股票清单')
    parser.add_argument('--export', action='store_true', help='导出报告')
    parser.add_argument('--no-export', action='store_true', help='不导出报告')
    
    args, remaining = parser.parse_known_args()
    
    # 默认显示帮助
    if not args.module:
        parser.print_help()
        sys.exit(0)
    
    # 路由到对应模块
    if args.module == 'recommend':
        # 股票推荐
        from recommend import StockRecommender
        recommender = StockRecommender(config_path=args.config)
        
        if args.interval > 0:
            recommender.run_scheduled(interval_minutes=args.interval)
        else:
            result = recommender.run_once()
            sys.exit(0 if result.get('success') else 1)
    
    elif args.module == 'monitor':
        # 股票监控
        from monitor import StockWatcher, parse_stock_list
        watcher = StockWatcher(config_path=args.config)
        
        if args.interval > 0:
            watcher.run_scheduled(interval_seconds=args.interval, export_report=not args.no_export)
        elif args.stocks:
            stock_list = parse_stock_list(args.stocks)
            result = watcher.monitor_custom_stocks(stock_list, export_report=not args.no_export)
            sys.exit(0 if result.get('success') else 1)
        else:
            result = watcher.run_once(export_report=not args.no_export)
            sys.exit(0 if result.get('success') else 1)


if __name__ == '__main__':
    main()
