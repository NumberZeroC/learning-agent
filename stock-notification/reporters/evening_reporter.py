#!/usr/bin/env python3
"""
晚间报告生成器
功能：从聚合数据生成晚间总结报告
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.data_aggregator import DataAggregator


class EveningReporter:
    """晚间报告生成器"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        self.config_path = config_path
        self.reports_dir = Path(__file__).parent.parent / 'data' / 'reports'
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据聚合器
        self.aggregator = DataAggregator(config_path)
    
    def generate(self, trade_date: str = None) -> str:
        """生成晚间报告"""
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        print(f"\n{'='*70}")
        print(f"🌙 生成晚间总结报告 - {trade_date}")
        print(f"{'='*70}")
        
        # 加载数据
        print("\n📂 加载数据...")
        data = self.aggregator.load_all(trade_date)
        
        if not data:
            print("   ⚠️ 未找到数据，请先运行数据获取服务")
            return ""
        
        # 提取数据
        market = data.get('market', {})
        capital = data.get('capital', {})
        ai_news = data.get('ai_news', {})
        
        # 生成报告
        report = self._build_report(market, capital, ai_news, trade_date)
        
        # 保存报告
        report_file = self._save_report(trade_date, report)
        
        # 同时保存 JSON
        self._save_json(trade_date, data)
        
        print(f"\n✅ 晚间报告生成完成")
        print(f"📄 报告：{report_file}")
        
        return str(report_file)
    
    def _build_report(self, market: dict, capital: dict, ai_news: dict, trade_date: str) -> str:
        """构建报告内容"""
        today = trade_date if len(trade_date) == 10 else f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}"
        
        # 大盘走势
        indices = market.get('indices', {})
        
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
                report += f"| {idx.get('name', key)} | {idx.get('close', 0):.2f} | {idx.get('change_pct', 0):+.2f}% | {status} |\n"
        
        # 板块资金流
        sector_flows = capital.get('sector_flows', [])
        
        report += f"""
---

## 💰 板块资金流 TOP10

| 排名 | 板块 | 主力流入 | 主力流出 | 净流入 |
|------|------|----------|----------|--------|
"""
        
        for i, s in enumerate(sector_flows[:10], 1):
            inflow = s.get('main_force_in', 0) / 10000
            outflow = s.get('main_force_out', 0) / 10000
            netflow = s.get('net_flow', 0) / 10000
            color = '🔴' if netflow > 0 else '🟢' if netflow < 0 else '⚪'
            report += f"| {i} | {s.get('sector', '')} | {inflow:.1f}万 | {outflow:.1f}万 | {color} {netflow:+.1f}万 |\n"
        
        # AI 行业动态
        sentiment = ai_news.get('sentiment', {})
        news_list = ai_news.get('news', [])
        
        report += f"""
---

## 🤖 AI 行业动态

### 情感分析

| 指标 | 数值 |
|------|------|
| 整体情感 | {sentiment.get('overall_emoji', '🟡')} {sentiment.get('overall_level', 'neutral')} |
| 情感得分 | {sentiment.get('overall_score', 50)}/100 |
| 新闻总数 | {sentiment.get('total_news', 0)} 条 |

### 热点话题

"""
        
        for topic in sentiment.get('hot_topics', [])[:5]:
            report += f"- 🔥 {topic}\n"
        
        report += "\n### AI 新闻精选\n\n"
        
        for i, item in enumerate(news_list[:5], 1):
            title = item.get('title', '无标题')[:60]
            source = item.get('source', '未知')
            report += f"{i}. **{title}...** ({source})\n"
        
        report += f"""
---

## 💡 明日策略建议

### 市场判断

{self._get_market_outlook(indices, sector_flows)}

### 操作建议

1. **仓位控制**: 建议仓位 {self._suggest_position(indices)}%
2. **关注方向**: 重点关注资金流入明显的板块
3. **风险控制**: 设置止损位，避免追高

---

**报告生成：** Stock-Agent 数据服务（解耦架构）
"""
        
        return report
    
    def _get_market_outlook(self, indices: dict, sector_flows: list) -> str:
        """生成市场展望"""
        if not indices:
            return "数据不足，谨慎判断"
        
        avg_change = sum(idx.get('change_pct', 0) for idx in indices.values()) / len(indices)
        positive_flow = sum(1 for s in sector_flows if s.get('net_flow', 0) > 0)
        
        if avg_change > 1 and positive_flow > 5:
            return "市场走势强劲，资金面积极，有望延续上涨趋势。"
        elif avg_change > 0:
            return "市场震荡偏强，结构性机会为主。"
        elif avg_change > -1:
            return "市场震荡整理，方向不明。"
        else:
            return "市场走势偏弱，注意风险。"
    
    def _suggest_position(self, indices: dict) -> int:
        """建议仓位"""
        if not indices:
            return 50
        
        up_count = sum(1 for idx in indices.values() if idx.get('change_pct', 0) > 0.5)
        
        if up_count >= 2:
            return 70
        elif up_count == 1:
            return 50
        else:
            return 30
    
    def _save_report(self, trade_date: str, report: str) -> Path:
        """保存 Markdown 报告"""
        today = trade_date if len(trade_date) == 10 else f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}"
        report_file = self.reports_dir / f'evening_summary_{today}.md'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"   📄 Markdown: {report_file}")
        
        return report_file
    
    def _save_json(self, trade_date: str, data: dict):
        """保存 JSON 数据"""
        today = trade_date if len(trade_date) == 10 else f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}"
        json_file = self.reports_dir / f'evening_summary_{today}.json'
        
        # 转换数据格式
        report_data = {
            'date': today,
            'timestamp': datetime.now().isoformat(),
            'market': data.get('market', {}),
            'sector_flows': data.get('capital', {}).get('sector_flows', []),
            'ai_news': data.get('ai_news', {}),
            'top_list': data.get('market', {}).get('top_list', [])
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"   📄 JSON: {json_file}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='晚间报告生成器')
    parser.add_argument('--date', '-d', help='交易日期 (YYYYMMDD)')
    parser.add_argument('--config', '-c', default='config.yaml', help='配置文件')
    
    args = parser.parse_args()
    
    reporter = EveningReporter(config_path=args.config)
    report_file = reporter.generate(args.date)
    
    if report_file:
        print(f"\n✅ 报告已生成：{report_file}")


if __name__ == '__main__':
    main()
