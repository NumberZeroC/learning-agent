#!/usr/bin/env python3
"""
晚间综合分析报告 - 每日盘后总结

功能：
1. 分析当天大盘走势（上证、深证、创业板）
2. 收集全天财经新闻
3. 分析板块资金流入情况
4. 输出晚间总结报告

用法：
    python evening_analysis.py
"""
import os
import sys
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
import argparse

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from news_monitor import NewsMonitor
from capital_flow import CapitalFlowAnalyzer
from tushare_pro_source import TushareProSource
from enhanced_data_source import EnhancedDataSource
from reliable_data_source import ReliableDataSource

# 🤖 新增：AI 新闻监控模块
try:
    from ai_news_monitor import AINewsMonitor
    AI_NEWS_AVAILABLE = True
    print("[AI 新闻监控] ✅ 模块已加载")
except Exception as e:
    print(f"[AI 新闻监控] ⚠️ 模块加载失败：{e}")
    AI_NEWS_AVAILABLE = False


class EveningSummaryAnalyzer:
    """晚间综合分析器"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 初始化新闻监控
        self.news_monitor = NewsMonitor(self.config.get('news_keywords', {}))
        
        # 初始化资金流分析
        akshare_config = self.config.get('akshare', {})
        self.capital_analyzer = CapitalFlowAnalyzer(
            cache_dir=akshare_config.get('cache_dir'),
            cache_ttl=akshare_config.get('cache_ttl', 300),
            max_retries=akshare_config.get('max_retries', 3)
        )
        
        # 尝试初始化 Tushare Pro
        self.tushare_pro = None
        try:
            tushare_config = self.config.get('tushare', {})
            token = tushare_config.get('token') or os.getenv('TUSHARE_TOKEN')
            if token:
                self.tushare_pro = TushareProSource(
                    token=token,
                    cache_dir=akshare_config.get('cache_dir'),
                    cache_ttl=600
                )
                print("[Tushare Pro] ✅ 已连接")
        except Exception as e:
            print(f"[Tushare Pro] ⚠️ 未连接：{e}")
        
        # 增强数据源
        self.enhanced_data = None
        try:
            self.enhanced_data = EnhancedDataSource(
                cache_dir=akshare_config.get('cache_dir'),
                cache_ttl=600
            )
            print("[数据源] ✅ AKShare 可用 - 备用数据源")
        except Exception as e:
            print(f"[数据源] ⚠️ AKShare 不可用：{e}")
        
        # 🔥 新增：可靠数据源（用于大盘指数等关键数据）
        self.reliable_data = None
        try:
            tushare_token = self.config.get('tushare', {}).get('token')
            self.reliable_data = ReliableDataSource(
                cache_dir=akshare_config.get('cache_dir'),
                cache_ttl=300,
                tushare_token=tushare_token
            )
            print("[可靠数据源] ✅ 已初始化 - 用于大盘指数/股价/资金流")
        except Exception as e:
            print(f"[可靠数据源] ⚠️ 初始化失败：{e}")
        
        # 🤖 新增：AI 新闻监控（集成到晚间总结）
        self.ai_news_monitor = None
        if AI_NEWS_AVAILABLE:
            try:
                self.ai_news_monitor = AINewsMonitor(
                    cache_dir=akshare_config.get('cache_dir'),
                    cache_ttl=600  # 10 分钟缓存
                )
                print("[AI 新闻监控] ✅ 已初始化 - 用于 AI 行业动态分析")
            except Exception as e:
                print(f"[AI 新闻监控] ⚠️ 初始化失败：{e}")
        
        print("=" * 70)
        print("🌙 晚间新闻综合分析器")
        print("=" * 70)
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                config_file = Path(__file__).parent / config_path
            
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
        except:
            pass
        return {}
    
    def get_market_performance(self) -> dict:
        """获取当天大盘走势（使用可靠数据源）"""
        print("\n📊 获取大盘走势...")
        
        market_data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'indices': {}
        }
        
        # 🔥 优先使用可靠数据源获取大盘指数
        if self.reliable_data:
            try:
                indices_data = self.reliable_data.get_index_data()
                if indices_data:
                    market_data['indices'] = indices_data
                    print(f"   ✅ 成功获取 {len(indices_data)} 个指数数据")
            except Exception as e:
                print(f"   ⚠️ 可靠数据源获取失败：{e}")
        
        # 如果可靠数据源失败，回退到原有逻辑
        if not market_data['indices']:
            print("   ⚠️ 回退到备用数据源...")
            
            # 主要指数代码
            indices = {
                'shanghai': {'code': '000001.SH', 'name': '上证指数'},
                'shenzhen': {'code': '399001.SZ', 'name': '深证成指'},
                'chinext': {'code': '399006.SZ', 'name': '创业板指'},
                'zheng50': {'code': '000016.SH', 'name': '上证 50'},
                'hs300': {'code': '000300.SH', 'name': '沪深 300'}
            }
            
            today = datetime.now().strftime('%Y%m%d')
            
            # 尝试从 Tushare Pro 获取
            if self.tushare_pro:
                for key, info in indices.items():
                    try:
                        data = self.tushare_pro.get_index_daily(info['code'], today)
                        if data:
                            market_data['indices'][key] = {
                                'name': info['name'],
                                'close': float(data.get('close', 0)),
                                'change_pct': float(data.get('pct_chg', 0)),
                                'volume': float(data.get('vol', 0)) if data.get('vol') else 0,
                                'amount': float(data.get('amount', 0)) if data.get('amount') else 0,
                                'high': float(data.get('high', 0)),
                                'low': float(data.get('low', 0)),
                                'open': float(data.get('open', 0))
                            }
                            print(f"   ✅ {info['name']}: {data.get('close', 0):.2f} ({data.get('pct_chg', 0):+.2f}%)")
                    except Exception as e:
                        print(f"   ⚠️ {info['name']} 获取失败：{e}")
            
            # 如果 Tushare 失败，尝试 AKShare
            if not market_data['indices'] and self.enhanced_data:
                for key, info in indices.items():
                    try:
                        # 简化处理，使用代码获取
                        code = info['code'].split('.')[0]
                        data = self.enhanced_data.get_stock_data(code)
                        if data:
                            market_data['indices'][key] = {
                                'name': info['name'],
                                'close': float(data.get('current_price', 0)),
                                'change_pct': float(data.get('change_pct', 0)),
                                'volume': float(data.get('volume', 0)),
                            }
                            print(f"   ✅ {info['name']}: {data.get('current_price', 0):.2f} ({data.get('change_pct', 0):+.2f}%)")
                    except:
                        pass
        
        return market_data
    
    def get_full_day_news(self) -> tuple:
        """获取全天新闻"""
        print("\n📰 获取全天新闻...")
        
        # 运行新闻监控
        news_result = self.news_monitor.run()
        
        # 收集所有新闻
        all_news = []
        total_count = 0
        for sector, info in news_result.items():
            if 'latest_news' in info:
                all_news.extend(info['latest_news'])
                total_count += info.get('news_count', 0)
        
        print(f"   获取新闻：{len(all_news)} 条")
        print(f"   覆盖板块：{len(news_result)} 个")
        
        return all_news, news_result
    
    def analyze_sector_capital_flow(self) -> list:
        """分析板块资金流入情况（2000 积分增强版）- 按板块涨幅排序"""
        print("\n💰 分析板块资金流 (Tushare 2000 积分)...")
        
        # 配置的板块列表
        sectors = self.config.get('sectors', [
            '半导体', '人工智能', '新能源', '医药生物', 
            '消费电子', '汽车', '金融', '消费', 
            '化工', '机械', '军工', '通信'
        ])
        
        # 获取全市场资金流数据（一次调用获取所有股票）
        today = datetime.now().strftime('%Y%m%d')
        market_flow = self.capital_analyzer.get_market_moneyflow(trade_date=today)
        
        sector_flows = []
        
        for sector in sectors:
            try:
                # 获取板块成分股 + 资金流
                stocks = self.capital_analyzer._get_sector_with_market_flow(sector, market_flow)
                
                if stocks:
                    # 计算板块总体资金流
                    total_inflow = sum(s.get('main_force_in', 0) for s in stocks if s.get('main_force_in', 0) > 0)
                    total_outflow = abs(sum(s.get('main_force_in', 0) for s in stocks if s.get('main_force_in', 0) < 0))
                    net_flow = total_inflow - total_outflow
                    
                    # 机构净买入
                    inst_net = sum(s.get('inst_net', 0) for s in stocks)
                    # 融资净买入
                    financing_net = sum(s.get('financing_net', 0) for s in stocks)
                    
                    # 计算板块平均涨幅
                    changes = [s.get('change_pct', 0) for s in stocks if s.get('change_pct') is not None]
                    avg_change = sum(changes) / len(changes) if changes else 0
                    
                    sector_flows.append({
                        'sector': sector,
                        'main_force_in': total_inflow,
                        'main_force_out': total_outflow,
                        'net_flow': net_flow,
                        'inst_net': inst_net,  # 机构净买入
                        'financing_net': financing_net,  # 融资净买入
                        'stock_count': len(stocks),
                        'avg_change': avg_change,  # 板块平均涨幅
                        'top_stocks': [s for s in stocks if s.get('top_reason', '')]  # 上榜股票
                    })
                    
                    print(f"   {sector}: 涨幅 {avg_change:+.2f}%, 净流入 {net_flow/10000:.1f}万，机构 {inst_net/10000:.1f}万")
                        
            except Exception as e:
                print(f"   ⚠️ {sector} 获取失败：{e}")
        
        # 🔥 修改：按板块涨幅排序（而不是按资金净流入）
        sector_flows.sort(key=lambda x: x['avg_change'], reverse=True)
        
        # 显示涨幅前五
        print("\n   板块涨幅 TOP5:")
        for i, s in enumerate(sector_flows[:5], 1):
            net_text = f" (净流入 {s['net_flow']/10000:.1f}万)" if s['net_flow'] != 0 else ""
            print(f"   {i}. {s['sector']}: {s['avg_change']:+.2f}%{net_text}")
        
        return sector_flows
    
    def analyze_news_sentiment(self, news_result: dict) -> dict:
        """分析新闻情绪"""
        print("\n📈 分析新闻情绪...")
        
        sector_sentiment = {}
        
        for sector, info in news_result.items():
            score = info.get('score', 0)
            news_count = info.get('news_count', 0)
            positive_news = info.get('positive_news', 0)
            
            # 计算情绪得分
            if news_count > 0:
                positive_ratio = positive_news / news_count
            else:
                positive_ratio = 0
            
            sentiment_score = score * 0.5 + positive_ratio * 50
            
            if sentiment_score > 60:
                level = '🔴 乐观'
            elif sentiment_score > 40:
                level = '🟡 中性'
            else:
                level = '🟢 谨慎'
            
            sector_sentiment[sector] = {
                'score': round(sentiment_score, 1),
                'level': level,
                'news_count': news_count,
                'positive_ratio': round(positive_ratio * 100, 1)
            }
        
        # 排序
        sorted_sentiment = sorted(
            sector_sentiment.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )
        
        print("\n   新闻情绪 TOP5:")
        for i, (sector, info) in enumerate(sorted_sentiment[:5], 1):
            print(f"   {i}. {sector}: {info['level']} (得分：{info['score']})")
        
        return dict(sorted_sentiment)
    
    def get_ai_news_and_sentiment(self) -> tuple:
        """获取 AI 新闻并分析情感"""
        print("\n🤖 获取 AI 行业新闻...")
        
        if not self.ai_news_monitor:
            print("   ⚠️ AI 新闻监控未初始化")
            return [], {}
        
        try:
            # 获取 AI 新闻
            ai_news = self.ai_news_monitor.fetch_all_news(limit_sources=8)
            print(f"   ✅ 获取 {len(ai_news)} 条 AI 新闻")
            
            # 分析情感
            sentiment = self.ai_news_monitor.analyze_news_sentiment(ai_news)
            print(f"   📊 情感得分：{sentiment['overall_score']} ({sentiment['overall_emoji']} {sentiment['overall_level']})")
            
            return ai_news, sentiment
            
        except Exception as e:
            print(f"   ⚠️ AI 新闻获取失败：{e}")
            return [], {}
    
    def generate_summary_report(self, market_data: dict, news_result: dict, 
                                sector_flows: list, sector_sentiment: dict,
                                ai_news: list = None, ai_sentiment: dict = None) -> str:
        """生成晚间总结报告"""
        print("\n📝 生成晚间总结报告...")
        
        today = datetime.now().strftime('%Y-%m-%d')
        output_dir = Path('./data/reports')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = output_dir / f'evening_summary_{today}.md'
        
        # 计算市场整体表现
        indices = market_data.get('indices', {})
        shanghai = indices.get('shanghai', {})
        shenzhen = indices.get('shenzhen', {})
        chinext = indices.get('chinext', {})
        
        # 生成 Markdown 报告
        report = f"""# 🌙 晚间市场总结报告

**日期：** {today}  
**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 大盘走势

### 主要指数表现

| 指数 | 收盘价 | 涨跌幅 | 状态 |
|------|--------|--------|------|
"""
        
        for key in ['shanghai', 'shenzhen', 'chinext']:
            if key in indices:
                idx = indices[key]
                status = '🔴' if idx.get('change_pct', 0) > 0 else '🟢' if idx.get('change_pct', 0) < 0 else '⚪'
                report += f"| {idx['name']} | {idx['close']:.2f} | {idx['change_pct']:+.2f}% | {status} |\n"
        
        # 市场总结
        market_summary = self._get_market_summary(indices)
        report += f"""
### 市场总结

{market_summary}

---

## 📰 新闻概览

**分析新闻来源：** 同花顺财经、金融界、证券时报、上海证券报、和讯财经

**新闻总数：** {sum(info.get('news_count', 0) for info in news_result.values())} 条

**覆盖板块：** {len(news_result)} 个

---

## 🏆 板块涨幅 TOP10（推荐）

> 💡 **说明：** 按板块平均涨幅排序，重点考虑热门板块 + 龙头股 + 资金流入指标

| 排名 | 板块 | 平均涨幅 | 主力流入 | 主力流出 | 净流入 | 机构净买 | 成分股数 |
|------|------|----------|----------|----------|--------|----------|----------|
"""
        
        for i, s in enumerate(sector_flows[:10], 1):
            inflow = s['main_force_in'] / 10000
            outflow = s['main_force_out'] / 10000
            netflow = s['net_flow'] / 10000
            inst_net = s.get('inst_net', 0) / 10000
            stock_count = s.get('stock_count', 0)
            change_color = '🔴' if s['avg_change'] > 0 else '🟢' if s['avg_change'] < 0 else '⚪'
            flow_icon = '🔥' if netflow > 500 else '💰' if netflow > 0 else '📉'
            report += f"| {i} | {s['sector']} | {change_color} {s['avg_change']:+.1f}% | {inflow:.1f}万 | {outflow:.1f}万 | {flow_icon} {netflow:+.1f}万 | {inst_net:+.1f}万 | {stock_count} |\n"
        
        report += f"""
---

## 📈 新闻情绪分析

| 排名 | 板块 | 情绪得分 | 情绪 | 新闻数 | 正面比例 |
|------|------|----------|------|--------|----------|
"""
        
        for i, (sector, info) in enumerate(list(sector_sentiment.items())[:10], 1):
            report += f"| {i} | {sector} | {info['score']:.1f} | {info['level']} | {info['news_count']} | {info['positive_ratio']:.1f}% |\n"
        
        # 🤖 新增：AI 新闻板块
        if ai_news and ai_sentiment:
            report += f"""
---

## 🤖 AI 行业动态

### 情感分析

| 指标 | 数值 |
|------|------|
| 整体情感 | {ai_sentiment.get('overall_emoji', '🟡')} {ai_sentiment.get('overall_level', 'neutral')} |
| 情感得分 | {ai_sentiment.get('overall_score', 50)}/100 |
| 新闻总数 | {ai_sentiment.get('total_news', 0)} 条 |
| 正面比例 | {ai_sentiment.get('positive_ratio', 0)}% |
| 负面比例 | {ai_sentiment.get('negative_ratio', 0)}% |

### 热点话题

"""
            for topic in ai_sentiment.get('hot_topics', [])[:5]:
                report += f"- 🔥 {topic}\n"
            
            report += "\n### 风险信号\n"
            risk_signals = ai_sentiment.get('risk_signals', [])
            if risk_signals:
                for risk in risk_signals[:3]:
                    severity_emoji = "🔴" if risk.get('severity') == 'high' else "🟡"
                    report += f"- {severity_emoji} {risk.get('title', '')[:60]}...\n"
            else:
                report += "- ✅ 无明显风险信号\n"
            
            report += "\n### AI 新闻精选\n\n"
            for i, item in enumerate(ai_news[:5], 1):
                title = item.get('title', '无标题')
                source = item.get('source', '未知')
                report += f"{i}. **{title[:50]}...** ({source})\n"
            
            report += "\n### 💡 对持仓的启示\n\n"
            report += "1. **技术趋势**: 关注 AI 新技术对产品的影响\n"
            report += "2. **资本动向**: 融资热点可能是下一个风口\n"
            report += "3. **风险提示**: 注意监管政策变化\n"
            report += "4. **创业机会**: 结合华为云背景，寻找差异化机会\n"
        
        # 重点关注板块
        hot_sectors = self._get_hot_sectors(sector_flows, sector_sentiment)
        
        report += f"""
---

## 🎯 重点关注板块

"""
        
        for i, sector in enumerate(hot_sectors[:5], 1):
            flow_info = next((s for s in sector_flows if s['sector'] == sector), {})
            sentiment_info = sector_sentiment.get(sector, {})
            
            report += f"### {i}. {sector}\n"
            report += f"- **资金流**: 净流入 {flow_info.get('net_flow', 0)/10000:+.1f}万\n"
            report += f"- **新闻情绪**: {sentiment_info.get('level', '中性')} (得分：{sentiment_info.get('score', 0)})\n"
            report += f"- **新闻数**: {sentiment_info.get('news_count', 0)} 条\n"
            report += f"- **关注理由**: 资金持续流入 + 新闻面利好\n\n"
        
        report += f"""
---

## 💡 明日策略建议

### 市场判断

{self._get_market_outlook(indices, sector_flows, sector_sentiment)}

### 操作建议

1. **仓位控制**: 建议仓位 {self._suggest_position(indices)}%
2. **关注方向**: 重点关注资金流入明显的板块
3. **风险控制**: 设置止损位，避免追高
4. **观察重点**: 关注早盘竞价情况和北向资金流向

---

## 📋 数据说明

- **数据来源**: AKShare、Tushare Pro、各大财经媒体
- **更新时间**: 每个交易日 20:00
- **覆盖范围**: A 股主要指数、板块资金流、财经新闻

---

*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*  
*⚠️ 免责声明：以上分析仅供参考，不构成投资建议*
"""
        
        # 保存报告
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # 获取龙虎榜数据
        try:
            today_ymd = datetime.now().strftime('%Y-%m-%d')  # 用于文件名
            today = datetime.now().strftime('%Y%m%d')  # 用于 API
            print(f"\n💰 获取龙虎榜数据...")
            market_flow = self.capital_analyzer.get_market_moneyflow(trade_date=today)
            print(f"   获取到 {len(market_flow)} 只股票")
            
            top_list = [
                {
                    'code': stock.get('code', ''),
                    'name': stock.get('name', ''),
                    'reason': stock.get('top_reason', ''),
                    'net_in': float(stock.get('top_net_in', 0)),  # 龙虎榜净买入
                    'amount': float(stock.get('top_amount', 0)),  # 总成交额
                    'l_buy': float(stock.get('top_l_buy', 0)),  # 龙虎榜买入
                    'l_sell': float(stock.get('top_l_sell', 0)),  # 龙虎榜卖出
                    'change_pct': float(stock.get('change_pct', 0))  # 涨跌幅
                }
                for stock in market_flow if stock.get('top_reason')
            ]
            print(f"   龙虎榜股票：{len(top_list)} 只")
        except Exception as e:
            print(f"   ⚠️ 龙虎榜获取失败：{e}")
            top_list = []
        
        # 同时保存 JSON 数据（增强版 - 包含更多资金流信息）
        json_file = output_dir / f'evening_summary_{today_ymd}.json'
        json_data = {
            'date': today,
            'timestamp': datetime.now().isoformat(),
            'market': market_data,
            'sector_flows': [
                {
                    'sector': s['sector'],
                    'main_force_in': s['main_force_in'],
                    'main_force_out': s['main_force_out'],
                    'net_flow': s['net_flow'],
                    'inst_net': s.get('inst_net', 0),
                    'financing_net': s.get('financing_net', 0),
                    'stock_count': s['stock_count'],
                    'avg_change': s['avg_change'],
                    'top_stocks': top_list[:5] if i == 0 else []  # 第一个板块包含龙虎榜
                }
                for i, s in enumerate(sector_flows[:10])
            ],
            'top_list': top_list,  # 完整龙虎榜数据
            'sector_sentiment': dict(list(sector_sentiment.items())[:10]),
            'hot_sectors': hot_sectors[:5],
            'news_count': sum(info.get('news_count', 0) for info in news_result.values()),
            'market_summary': {
                'total_net_flow': sum(s['net_flow'] for s in sector_flows),
                'positive_sectors': sum(1 for s in sector_flows if s['net_flow'] > 0),
                'negative_sectors': sum(1 for s in sector_flows if s['net_flow'] < 0),
                'total_inst_net': sum(s.get('inst_net', 0) for s in sector_flows),
                'total_financing_net': sum(s.get('financing_net', 0) for s in sector_flows)
            }
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"   报告已保存：{report_file}")
        print(f"   数据已保存：{json_file}")
        
        # 🔥 保存原始数据快照（确保数据可追溯、不变）
        if self.reliable_data:
            snapshot_data = {
                'market_indices': market_data.get('indices', {}),
                'sector_flows': sector_flows[:10],
                'sector_sentiment': dict(list(sector_sentiment.items())[:10]),
                'reliable_data_log': self.reliable_data.get_data_log()
            }
            self.reliable_data.save_data_snapshot('evening', snapshot_data, str(output_dir))
        
        return str(report_file)
    
    def _get_market_summary(self, indices: dict) -> str:
        """生成市场总结文字"""
        if not indices:
            return "市场数据暂缺"
        
        shanghai = indices.get('shanghai', {})
        shenzhen = indices.get('shenzhen', {})
        chinext = indices.get('chinext', {})
        
        up_count = sum(1 for idx in [shanghai, shenzhen, chinext] 
                      if idx.get('change_pct', 0) > 0)
        
        if up_count == 3:
            return "🔴 今日市场普涨，三大指数全线收红，市场情绪较好"
        elif up_count == 2:
            return "🟡 今日市场分化，多数指数收红，震荡格局"
        elif up_count == 1:
            return "🟠 今日市场偏弱，仅个别指数收红，注意风险"
        else:
            return "🟢 今日市场调整，三大指数集体收绿，谨慎观望"
    
    def _get_hot_sectors(self, sector_flows: list, sector_sentiment: dict) -> list:
        """综合板块涨幅和情绪选出热点板块"""
        # 🔥 修改：按涨幅前 5（而不是资金流）
        change_top5 = [s['sector'] for s in sector_flows[:5] if s['avg_change'] > 0]
        
        # 情绪前 5
        sentiment_top5 = [s for s, info in list(sector_sentiment.items())[:5] 
                         if info['score'] > 40]
        
        # 合并去重
        hot = list(dict.fromkeys(change_top5 + sentiment_top5))
        
        return hot[:10]
    
    def _suggest_position(self, indices: dict) -> int:
        """根据市场情况建议仓位"""
        if not indices:
            return 50
        
        up_count = sum(1 for idx in indices.values() 
                      if idx.get('change_pct', 0) > 0.5)
        
        if up_count >= 2:
            return 70
        elif up_count == 1:
            return 50
        else:
            return 30
    
    def _get_market_outlook(self, indices: dict, sector_flows: list, 
                           sector_sentiment: dict) -> str:
        """生成市场展望"""
        if not indices:
            return "数据不足，谨慎判断"
        
        # 计算整体趋势
        avg_change = sum(idx.get('change_pct', 0) for idx in indices.values()) / len(indices)
        
        # 资金流情况
        positive_flow = sum(1 for s in sector_flows if s['net_flow'] > 0)
        
        if avg_change > 1 and positive_flow > 5:
            return "市场走势强劲，资金面积极，有望延续上涨趋势。建议适度加仓，关注主线板块。"
        elif avg_change > 0:
            return "市场震荡偏强，结构性机会为主。建议保持中等仓位，精选个股。"
        elif avg_change > -1:
            return "市场震荡整理，方向不明。建议控制仓位，等待明确信号。"
        else:
            return "市场走势偏弱，注意风险。建议降低仓位，防御为主。"
    
    def run_analysis(self) -> dict:
        """执行完整分析"""
        print(f"\n{'='*70}")
        print(f"🌙 晚间市场综合分析 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*70}\n")
        
        try:
            # 1. 获取大盘走势
            market_data = self.get_market_performance()
            
            # 2. 获取全天新闻
            all_news, news_result = self.get_full_day_news()
            
            # 3. 分析板块资金流
            sector_flows = self.analyze_sector_capital_flow()
            
            # 4. 分析新闻情绪
            sector_sentiment = self.analyze_news_sentiment(news_result)
            
            # 🤖 5. 获取 AI 新闻并分析情感
            ai_news, ai_sentiment = self.get_ai_news_and_sentiment()
            
            # 6. 生成报告（包含 AI 新闻）
            report_file = self.generate_summary_report(
                market_data, 
                news_result, 
                sector_flows, 
                sector_sentiment,
                ai_news,
                ai_sentiment
            )
            
            print(f"\n{'='*70}")
            print("✅ 晚间分析完成")
            print(f"{'='*70}")
            print(f"📄 报告：{report_file}")
            if ai_news:
                print(f"🤖 AI 新闻：{len(ai_news)} 条，情感得分：{ai_sentiment.get('overall_score', 0)}")
            
            return {
                'success': True,
                'report_file': report_file,
                'sector_count': len(sector_flows),
                'news_count': len(all_news),
                'ai_news_count': len(ai_news) if ai_news else 0
            }
            
        except Exception as e:
            print(f"\n❌ 分析失败：{e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}


def main():
    parser = argparse.ArgumentParser(description='🌙 晚间市场综合分析')
    parser.add_argument('--config', '-c', default='config.yaml', help='配置文件路径')
    
    args = parser.parse_args()
    
    analyzer = EveningSummaryAnalyzer(config_path=args.config)
    result = analyzer.run_analysis()
    
    sys.exit(0 if result.get('success') else 1)


if __name__ == '__main__':
    main()
