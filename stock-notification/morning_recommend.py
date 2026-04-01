#!/usr/bin/env python3
"""
早盘推荐报告 - 基于晚间分析和早间数据

功能：
1. 读取前一天晚间分析报告
2. 获取早间新闻和隔夜消息
3. 获取集合竞价数据
4. 推荐热点板块（最多 5 个）
5. 每个热点板块推荐 3 只龙头股票

用法：
    python morning_recommend.py
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


class MorningRecommender:
    """早盘推荐引擎"""
    
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
                cache_ttl=300
            )
            print("[数据源] ✅ AKShare 可用")
        except Exception as e:
            print(f"[数据源] ⚠️ AKShare 不可用：{e}")
        
        print("=" * 70)
        print("📈 早盘推荐引擎")
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
    
    def load_evening_summary(self) -> dict:
        """加载前一天晚间总结报告"""
        print("\n📋 加载晚间总结报告...")
        
        # 查找最近的晚间报告
        report_dir = Path('./data/reports')
        today = datetime.now()
        
        # 尝试昨天和前天（周末情况）
        for days_ago in range(1, 5):
            date = today - timedelta(days=days_ago)
            date_str = date.strftime('%Y-%m-%d')
            
            json_file = report_dir / f'evening_summary_{date_str}.json'
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"   ✅ 已加载：{date_str} 的晚间报告")
                return data
            
            # 也检查旧格式
            old_json = report_dir / f'evening_analysis_{date_str}.json'
            if old_json.exists():
                with open(old_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"   ✅ 已加载：{date_str} 的晚间报告 (旧格式)")
                return data
        
        print("   ⚠️ 未找到晚间报告，将基于当前数据分析")
        return {}
    
    def get_morning_news(self) -> tuple:
        """获取早间新闻（隔夜消息和早盘新闻）"""
        print("\n📰 获取早间新闻...")
        
        # 运行新闻监控获取最新新闻
        news_result = self.news_monitor.run()
        
        # 收集新闻
        all_news = []
        for sector, info in news_result.items():
            if 'latest_news' in info:
                all_news.extend(info['latest_news'][:5])  # 每个板块最多 5 条
        
        print(f"   获取新闻：{len(all_news)} 条")
        
        return all_news, news_result
    
    def get_auction_data(self, stocks: list) -> list:
        """获取集合竞价数据"""
        print("\n🔔 获取竞价数据...")
        
        auction_data = []
        
        # 如果是交易时间 9:15-9:30，尝试获取竞价数据
        now = datetime.now()
        is_auction_time = (now.hour == 9 and 15 <= now.minute < 30) or \
                         (now.hour == 9 and now.minute >= 30 and now.hour < 15)
        
        if not is_auction_time:
            print("   ⚠️ 非竞价时间，使用最新行情数据")
            # 获取最新行情作为参考
            for stock_info in stocks[:20]:  # 最多处理 20 只
                try:
                    code = stock_info.get('code', '')
                    if not code:
                        continue
                    
                    # 获取股票数据
                    data = self._get_stock_data(code)
                    if data:
                        auction_data.append({
                            'code': code,
                            'name': data.get('name', stock_info.get('name', '')),
                            'open': data.get('open', data.get('current_price', 0)),
                            'change_pct': data.get('change_pct', 0),
                            'volume': data.get('volume', 0),
                            'amount': data.get('amount', 0)
                        })
                except Exception as e:
                    pass
            
            print(f"   ✅ 获取 {len(auction_data)} 只股票行情")
            return auction_data
        
        # 竞价时间逻辑（实际实现需要接入实时数据）
        print("   📊 分析竞价数据...")
        
        for stock_info in stocks[:20]:
            try:
                code = stock_info.get('code', '')
                if not code:
                    continue
                
                data = self._get_stock_data(code)
                if data:
                    # 判断竞价强弱
                    auction_strength = '强' if data.get('change_pct', 0) > 2 else \
                                      '中' if data.get('change_pct', 0) > 0 else '弱'
                    
                    auction_data.append({
                        'code': code,
                        'name': data.get('name', stock_info.get('name', '')),
                        'open': data.get('open', 0),
                        'change_pct': data.get('change_pct', 0),
                        'volume': data.get('volume', 0),
                        'auction_strength': auction_strength
                    })
            except:
                pass
        
        print(f"   ✅ 获取 {len(auction_data)} 只股票竞价数据")
        return auction_data
    
    def _get_stock_data(self, code: str) -> dict:
        """获取股票数据"""
        if self.enhanced_data:
            try:
                return self.enhanced_data.get_stock_data(code)
            except:
                pass
        
        if self.tushare_pro:
            try:
                return self.tushare_pro.get_realtime_quote(code)
            except:
                pass
        
        return {}
    
    def select_hot_sectors(self, evening_data: dict, morning_news: dict) -> list:
        """选择热点板块（最多 5 个）- 综合涨幅 + 资金流 + 情绪"""
        print("\n🔥 选择热点板块...")
        
        hot_sectors = []
        sector_scores = {}
        sector_details = {}
        
        # 1. 从晚间报告获取热点板块
        if evening_data:
            # 新格式：有 hot_sectors、sector_flows、sector_sentiment
            evening_hot = evening_data.get('hot_sectors', [])
            sector_flows = evening_data.get('sector_flows', [])
            sector_sentiment = evening_data.get('sector_sentiment', {})
            
            # 旧格式：有 sector_benefits
            sector_benefits = evening_data.get('sector_benefits', {})
            
            if sector_benefits:
                # 旧格式处理：从 sector_benefits 提取
                for sector, info in sector_benefits.items():
                    score = info.get('benefit_score', 0)
                    if score > 0:
                        sector_scores[sector] = score
            elif sector_flows:
                # 🔥 新格式处理：综合评分（涨幅 40% + 资金流 40% + 情绪 20%）
                for sector_info in sector_flows[:15]:  # 取前 15 个板块
                    sector = sector_info.get('sector', '')
                    avg_change = sector_info.get('avg_change', 0)
                    net_flow = sector_info.get('net_flow', 0)
                    main_force_in = sector_info.get('main_force_in', 0)
                    
                    # 📈 涨幅得分（40 分）
                    change_score = min(avg_change * 5, 40)  # 涨幅 8% 以上满分
                    
                    # 💰 资金流得分（40 分）
                    flow_score = 0
                    if net_flow > 0:
                        flow_score = min(net_flow / 250000, 40)  # 净流入 1000 万以上满分
                    
                    # 📰 情绪得分（20 分）
                    sentiment_info = sector_sentiment.get(sector, {})
                    sentiment_score = sentiment_info.get('score', 0) * 0.2
                    
                    # 总分
                    total_score = change_score + flow_score + sentiment_score
                    
                    sector_scores[sector] = total_score
                    sector_details[sector] = {
                        'change': avg_change,
                        'net_flow': net_flow,
                        'flow_in': main_force_in
                    }
        
        # 2. 结合早间新闻调整
        if morning_news:
            for sector, info in morning_news.items():
                if info.get('score', 0) > 5 and sector not in sector_scores:
                    sector_scores[sector] = info.get('score', 0) * 10
        
        # 排序取前 5
        sorted_sectors = sorted(sector_scores.items(), key=lambda x: x[1], reverse=True)
        hot_sectors = [s[0] for s in sorted_sectors[:5]]
        
        print(f"   选定热点板块：{len(hot_sectors)} 个")
        for i, sector in enumerate(hot_sectors, 1):
            score = sector_scores.get(sector, 0)
            detail = sector_details.get(sector, {})
            change_text = f"涨幅 {detail.get('change', 0):+.1f}%" if detail else ""
            flow_text = f"净流入 {detail.get('net_flow', 0)/10000:.0f}万" if detail else ""
            print(f"   {i}. {sector} (得分：{score:.1f}) - {change_text} | {flow_text}")
        
        return hot_sectors
    
    def select_sector_leaders(self, sector: str, auction_data: list) -> list:
        """为板块选择龙头股票（3 只）- 重点考虑资金流入指标"""
        print(f"\n   📊 分析 {sector} 板块龙头...")
        
        leaders = []
        
        # 获取板块成分股
        try:
            stocks = self.capital_analyzer.get_sector_stocks(sector)
            
            if not stocks:
                print(f"      ⚠️ 无法获取 {sector} 成分股")
                return []
            
            # 🔥 综合评分：资金流 (60%) + 涨幅 (25%) + 竞价 (15%)
            # 重点突出资金流入指标
            scored_stocks = []
            for stock in stocks[:50]:  # 最多分析 50 只
                code = stock.get('code', '')
                name = stock.get('name', '')
                
                # 🌟 资金流得分（权重 60% - 最高 60 分）
                # 主力净流入 = 主力流入 - 主力流出
                main_force_in = stock.get('main_force_in', 0)
                main_force_out = stock.get('main_force_out', 0)
                main_force_net = main_force_in - main_force_out
                
                # 机构净买入加分
                inst_net = stock.get('inst_net', 0)
                
                # 融资净买入加分
                financing_net = stock.get('financing_net', 0)
                
                # 资金流综合得分
                flow_score = min(main_force_net / 500, 40)  # 主力净流入最多 40 分
                flow_score += min(inst_net / 1000, 10)  # 机构净买入最多 10 分
                flow_score += min(financing_net / 500, 10)  # 融资净买入最多 10 分
                
                # 📈 涨幅得分（权重 25% - 最高 25 分）
                change_pct = stock.get('change_pct', 0)
                change_score = min(max(change_pct, 0) * 2.5, 25)  # 涨幅 10% 以上满分
                
                # 🔔 竞价得分（权重 15% - 最高 15 分）
                auction_info = next((a for a in auction_data if a['code'] == code), {})
                auction_strength = auction_info.get('auction_strength', '')
                if auction_strength == '强':
                    auction_score = 15
                elif auction_strength == '中':
                    auction_score = 8
                else:
                    auction_score = 0
                
                # 总分
                total_score = flow_score + change_score + auction_score
                
                scored_stocks.append({
                    'code': code,
                    'name': name,
                    'score': total_score,
                    'main_force_in': main_force_in,  # 主力流入
                    'main_force_out': main_force_out,  # 主力流出
                    'main_force_net': main_force_net,  # 主力净流入
                    'inst_net': inst_net,  # 机构净买入
                    'financing_net': financing_net,  # 融资净买入
                    'change_pct': change_pct,
                    'auction': auction_strength if auction_strength else '-'
                })
            
            # 排序取前 3
            scored_stocks.sort(key=lambda x: x['score'], reverse=True)
            leaders = scored_stocks[:3]
            
            for i, leader in enumerate(leaders, 1):
                print(f"      {i}. {leader['name']}({leader['code']}) - 得分：{leader['score']:.1f} (主力净流入：{leader['main_force_net']/10000:.1f}万)")
            
        except Exception as e:
            print(f"      ⚠️ 分析失败：{e}")
        
        return leaders
    
    def generate_recommendation_report(self, evening_data: dict, hot_sectors: list,
                                       sector_leaders: dict, morning_news_count: int) -> str:
        """生成早盘推荐报告"""
        print("\n📝 生成早盘推荐报告...")
        
        today = datetime.now().strftime('%Y-%m-%d')
        output_dir = Path('./data/reports')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = output_dir / f'morning_recommend_{today}.md'
        
        # 获取晚间报告日期
        evening_date = evening_data.get('date', '昨日')
        
        # 生成报告
        report = f"""# 📈 早盘推荐报告

**日期：** {today}  
**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**参考依据：** {evening_date} 晚间总结 + 早间新闻 + 竞价数据

---

## 📋 隔夜回顾

### 晚间总结要点

"""
        
        if evening_data:
            # 市场表现
            market = evening_data.get('market', {})
            indices = market.get('indices', {})
            
            report += "**大盘表现：**\n"
            for key in ['shanghai', 'shenzhen', 'chinext']:
                if key in indices:
                    idx = indices[key]
                    report += f"- {idx['name']}: {idx['close']:.2f} ({idx['change_pct']:+.2f}%)\n"
            
            # 热点板块
            hot = evening_data.get('hot_sectors', [])
            if hot:
                report += f"\n**昨日热点：** {'、'.join(hot[:5])}\n"
        else:
            report += "*暂无晚间报告数据*\n"
        
        report += f"""
### 早间新闻

- 获取早间新闻：{morning_news_count} 条
- 重点关注：政策面消息、隔夜外盘、行业利好

---

## 🔥 今日热点板块推荐

**推荐逻辑：** 综合晚间资金流向 + 新闻情绪 + 早间竞价表现

"""
        
        for i, sector in enumerate(hot_sectors, 1):
            report += f"### {i}. {sector}\n\n"
            
            # 获取该板块的龙头股
            leaders = sector_leaders.get(sector, [])
            
            # 🔥 更新表格：突出显示资金流入指标
            report += "| 排名 | 股票 | 代码 | 得分 | 主力流入 | 主力流出 | 净流入 | 机构净买 | 涨幅 | 竞价 |\n"
            report += "|------|------|------|------|----------|----------|--------|----------|------|------|\n"
            
            for j, leader in enumerate(leaders, 1):
                force_in = leader.get('main_force_in', 0) / 10000
                force_out = leader.get('main_force_out', 0) / 10000
                force_net = leader.get('main_force_net', 0) / 10000
                inst_net = leader.get('inst_net', 0) / 10000
                change_pct = leader.get('change_pct', 0)
                
                # 净流入颜色标记
                net_color = '🔴' if force_net > 500 else '🟡' if force_net > 0 else '🟢'
                
                report += f"| {j} | **{leader['name']}** | {leader['code']} | {leader['score']:.1f} | {force_in:+.1f}万 | {force_out:.1f}万 | {net_color} {force_net:+.1f}万 | {inst_net:+.1f}万 | {change_pct:+.1f}% | {leader['auction']} |\n"
            
            report += "\n"
        
        report += f"""
---

## 💡 今日操作策略

### 重点关注

1. **主线板块**: {'、'.join(hot_sectors[:3]) if hot_sectors else '待定'}
2. **仓位建议**: {self._suggest_position(evening_data)}%
3. **操作节奏**: 早盘观察竞价，确认强势后介入

### 风险提示

- ⚠️ 注意大盘整体走势，弱势环境下降低预期
- ⚠️ 避免追高，关注低吸机会
- ⚠️ 设置止损位，控制单笔风险
- ⚠️ 关注北向资金流向

---

## 📊 竞价观察

| 指标 | 数值 | 解读 |
|------|------|------|
| 涨停竞价 | 待更新 | 市场情绪指标 |
| 跌停竞价 | 待更新 | 风险指标 |
| 高开封板 | 待更新 | 强势股数量 |

*竞价数据在 9:25 后更新*

---

## 📋 数据来源

- **晚间报告**: 资金流分析、新闻情绪分析
- **早间新闻**: 各大财经媒体
- **竞价数据**: 交易所集合竞价
- **行情数据**: AKShare、Tushare Pro

---

*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*  
*⚠️ 免责声明：以上分析仅供参考，不构成投资建议*
"""
        
        # 保存报告
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # 保存 JSON 数据（增强版 - 包含推荐股票列表）
        json_file = output_dir / f'morning_recommend_{today}.json'
        
        # 构建推荐列表（5 大板块 × 各 5 只股票 = 25 只）
        recommendations = []
        for sector in hot_sectors[:5]:
            leaders = sector_leaders.get(sector, [])[:5]
            recommendations.append({
                'sector': sector,
                'stocks': [
                    {
                        'code': stock.get('code', ''),
                        'name': stock.get('name', ''),
                        'reason': stock.get('recommendation_reason', stock.get('reason', '')),
                        'price': stock.get('price', 0),
                        'change_pct': stock.get('change_pct', 0)
                    }
                    for stock in leaders
                ]
            })
        
        json_data = {
            'date': today,
            'evening_date': evening_date,
            'hot_sectors': hot_sectors,
            'sector_leaders': sector_leaders,
            'news_count': morning_news_count,
            'recommendations': recommendations,  # 新增推荐列表
            'position_suggestion': self._suggest_position(evening_data)
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"   报告已保存：{report_file}")
        print(f"   数据已保存：{json_file}")
        
        return str(report_file)
    
    def _suggest_position(self, evening_data: dict) -> int:
        """根据晚间数据建议仓位"""
        if not evening_data:
            return 50
        
        # 从晚间报告判断市场情绪
        market = evening_data.get('market', {})
        indices = market.get('indices', {})
        
        if not indices:
            return 50
        
        avg_change = sum(idx.get('change_pct', 0) for idx in indices.values()) / len(indices)
        
        if avg_change > 1:
            return 70
        elif avg_change > 0:
            return 60
        elif avg_change > -1:
            return 40
        else:
            return 30
    
    def run_recommendation(self) -> dict:
        """执行完整推荐流程"""
        print(f"\n{'='*70}")
        print(f"📈 早盘推荐分析 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*70}\n")
        
        try:
            # 1. 加载晚间总结
            evening_data = self.load_evening_summary()
            
            # 2. 获取早间新闻
            morning_news, news_result = self.get_morning_news()
            
            # 3. 选择热点板块
            hot_sectors = self.select_hot_sectors(evening_data, news_result)
            
            # 4. 获取竞价数据（用于龙头选择）
            # 先收集所有可能需要的股票代码
            candidate_stocks = []
            if evening_data:
                for sector in hot_sectors:
                    try:
                        stocks = self.capital_analyzer.get_sector_stocks(sector)
                        if stocks:
                            candidate_stocks.extend(stocks[:10])
                    except:
                        pass
            
            auction_data = self.get_auction_data(candidate_stocks)
            
            # 5. 为每个热点板块选择龙头
            sector_leaders = {}
            for sector in hot_sectors:
                leaders = self.select_sector_leaders(sector, auction_data)
                sector_leaders[sector] = leaders
            
            # 6. 生成推荐报告
            report_file = self.generate_recommendation_report(
                evening_data,
                hot_sectors,
                sector_leaders,
                len(morning_news)
            )
            
            print(f"\n{'='*70}")
            print("✅ 早盘推荐完成")
            print(f"{'='*70}")
            print(f"📄 报告：{report_file}")
            print(f"\n📋 推荐摘要:")
            print(f"   热点板块：{len(hot_sectors)} 个")
            for i, sector in enumerate(hot_sectors, 1):
                leaders = sector_leaders.get(sector, [])
                print(f"   {i}. {sector}: {leaders[0]['name'] if leaders else '暂无'} 等 {len(leaders)} 只龙头")
            
            return {
                'success': True,
                'report_file': report_file,
                'hot_sectors': hot_sectors,
                'sector_leaders': sector_leaders
            }
            
        except Exception as e:
            print(f"\n❌ 推荐失败：{e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}


def main():
    parser = argparse.ArgumentParser(description='📈 早盘推荐引擎')
    parser.add_argument('--config', '-c', default='config.yaml', help='配置文件路径')
    
    args = parser.parse_args()
    
    recommender = MorningRecommender(config_path=args.config)
    result = recommender.run_recommendation()
    
    sys.exit(0 if result.get('success') else 1)


if __name__ == '__main__':
    main()
