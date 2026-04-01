"""
报告生成模块 - 生成投资分析报告
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional


class ReportGenerator:
    """投资报告生成器"""
    
    def __init__(self, output_dir: str = None):
        # 使用绝对路径
        if output_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_dir = os.path.dirname(script_dir)
            output_dir = os.path.join(project_dir, 'data', 'reports')
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_market_summary(self, news_result: Dict, flow_result: Dict, 
                                extra_data: Dict = None) -> str:
        """生成市场概览（支持增强数据）"""
        lines = []
        lines.append("## 📊 市场概览")
        lines.append("")
        
        # 资金流入前三板块
        top_sectors = flow_result.get('top_inflow_sectors', [])[:3]
        if top_sectors:
            lines.append("### 资金流入前三板块")
            for i, sector in enumerate(top_sectors, 1):
                lines.append(f"**{i}. {sector['sector']}** - 净流入 {sector['net_flow']:,.0f}万")
            lines.append("")
        
        # 新闻热点板块
        lines.append("### 新闻热点板块")
        for sector, info in list(news_result.items())[:3]:
            trend_emoji = '🔴' if info['trend'] == '利好' else '🟢' if info['trend'] == '利空' else '⚪'
            lines.append(f"{trend_emoji} **{sector}**: {info['trend']} ({info['news_count']}条新闻)")
        lines.append("")
        
        # 增强数据：北向资金
        if extra_data and extra_data.get('north_flow'):
            lines.append("### 🌊 北向资金持仓 TOP5")
            for i, stock in enumerate(extra_data['north_flow'][:5], 1):
                lines.append(f"**{i}. {stock['name']}** - 持股 {stock['hold_ratio']:.2f}% ({stock['market']})")
            lines.append("")
        
        # 增强数据：ETF 资金流
        if extra_data and extra_data.get('etfs'):
            etfs = extra_data['etfs']
            if len(etfs) > 0:
                lines.append("### 📈 ETF 市场")
                lines.append(f"- 监控 ETF 数量：**{len(etfs)} 只**")
                # 找出涨跌幅前三
                top_gainers = sorted(etfs, key=lambda x: x.get('change_pct', 0), reverse=True)[:3]
                lines.append("- 今日领涨 ETF:")
                for i, etf in enumerate(top_gainers, 1):
                    lines.append(f"  {i}. {etf['name']} ({etf['code']}): {etf['change_pct']:+.2f}%")
                lines.append("")
        
        # 增强数据：宏观经济
        if extra_data and extra_data.get('gdp'):
            gdp = extra_data['gdp']
            if len(gdp) > 0:
                latest_gdp = gdp[0]
                lines.append("### 🌍 宏观经济")
                lines.append(f"- 最新 GDP 增长率：**{latest_gdp.get('growth_rate', 'N/A')}%**")
                lines.append(f"- 数据年份：{len(gdp)} 年")
                lines.append("")
        
        return '\n'.join(lines)
    
    def generate_stock_recommendations(self, recommendations: List[Dict]) -> str:
        """生成个股推荐"""
        lines = []
        lines.append("## 🎯 个股推荐")
        lines.append("")
        
        for i, rec in enumerate(recommendations[:5], 1):
            stock = rec['stock']
            rating_emoji = {
                '强烈推荐': '🔥',
                '推荐': '✅',
                '中性': '⚪',
                '谨慎': '⚠️',
                '回避': '❌'
            }.get(rec['rating'], '⚪')
            
            lines.append(f"### {i}. {rating_emoji} {stock['name']} ({stock['code']})")
            lines.append(f"- **板块**: {stock['sector']}")
            lines.append(f"- **现价**: ¥{stock['price']:.2f} ({stock['change_pct']:+.2f}%)")
            lines.append(f"- **主力净流入**: {stock['main_force_in']/10000:.1f}万")
            lines.append(f"- **新闻情绪**: {stock['news_sentiment']}")
            lines.append(f"- **综合得分**: {stock['score']}/10")
            lines.append(f"- **评级**: {rec['rating']}")
            lines.append(f"- **建议**: {rec['action']}")
            
            if rec['risks']:
                lines.append(f"- **风险提示**: {'; '.join(rec['risks'])}")
            
            lines.append("")
        
        return '\n'.join(lines)
    
    def generate_investment_advice(self, recommendations: List[Dict]) -> str:
        """生成投资建议"""
        lines = []
        lines.append("## 💡 投资策略建议")
        lines.append("")
        
        # 统计评级分布
        rating_dist = {}
        for rec in recommendations:
            rating = rec['rating']
            rating_dist[rating] = rating_dist.get(rating, 0) + 1
        
        lines.append("### 推荐分布")
        for rating, count in sorted(rating_dist.items(), key=lambda x: ['强烈推荐', '推荐', '中性', '谨慎', '回避'].index(x[0]) if x[0] in ['强烈推荐', '推荐', '中性', '谨慎', '回避'] else 99):
            lines.append(f"- {rating}: {count}只")
        lines.append("")
        
        # 总体建议
        strong_count = rating_dist.get('强烈推荐', 0) + rating_dist.get('推荐', 0)
        avoid_count = rating_dist.get('回避', 0) + rating_dist.get('谨慎', 0)
        
        lines.append("### 总体策略")
        if strong_count >= 3:
            lines.append("🔴 **积极进攻**: 市场情绪较好，可适当提高仓位，重点关注推荐个股")
        elif strong_count >= 1:
            lines.append("🟡 **结构性机会**: 精选个股，控制仓位，关注资金流入板块")
        elif avoid_count >= 3:
            lines.append("🟢 **防御为主**: 市场风险较大，建议降低仓位，以观望为主")
        else:
            lines.append("⚪ **中性策略**: 市场分化，精选个股，控制风险")
        
        lines.append("")
        lines.append("### 操作建议")
        lines.append("1. **仓位控制**: 建议总仓位 50%-70%，留足现金应对波动")
        lines.append("2. **止盈止损**: 设置 8%-10%止损位，盈利 15%-20%可部分止盈")
        lines.append("3. **分散投资**: 不要重仓单一个股，建议分散 3-5 个板块")
        lines.append("4. **关注时机**: 早盘 9:30-10:00 和尾盘 14:30-15:00 是关键决策窗口")
        lines.append("")
        
        return '\n'.join(lines)
    
    def generate_full_report(self, news_result: Dict, flow_result: Dict, 
                            recommendations: List[Dict], extra_data: Dict = None) -> str:
        """生成完整报告（支持增强数据）"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        report = f"""# 📈 股票投资分析报告

**生成时间**: {timestamp}

---

{self.generate_market_summary(news_result, flow_result, extra_data)}

{self.generate_stock_recommendations(recommendations)}

{self.generate_investment_advice(recommendations)}

---

## ⚠️ 免责声明

本报告由 AI 自动生成，仅供参考和学习使用，**不构成任何投资建议**。

- 数据来源于公开信息，可能存在延迟或误差
- 股市有风险，投资需谨慎
- 请结合个人风险承受能力独立决策
- 过往表现不代表未来收益

**投资有风险，入市需谨慎** 🙏
"""
        
        return report
    
    def save_report(self, report: str, filename: Optional[str] = None) -> str:
        """保存报告到文件"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'report_{timestamp}.md'
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"[报告] 已保存至：{filepath}")
        return filepath
    
    def save_json(self, data: Dict, filename: Optional[str] = None) -> str:
        """保存原始数据为 JSON"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data_{timestamp}.json'
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"[数据] 已保存至：{filepath}")
        return filepath
    
    def run(self, news_result: Dict, flow_result: Dict, 
            recommendations: List[Dict], extra_data: Dict = None) -> Dict:
        """执行报告生成流程（支持增强数据）"""
        print("[报告] 开始生成投资报告...")
        
        # 生成报告
        report = self.generate_full_report(news_result, flow_result, recommendations, extra_data)
        
        # 保存
        report_path = self.save_report(report)
        
        # 保存原始数据
        data = {
            'news': news_result,
            'flow': flow_result,
            'recommendations': recommendations,
            'timestamp': datetime.now().isoformat()
        }
        data_path = self.save_json(data)
        
        print("[报告] 生成完成")
        
        return {
            'report_path': report_path,
            'data_path': data_path,
            'report_preview': report[:500] + '...'
        }


if __name__ == '__main__':
    # 测试
    news_result = {
        '半导体': {'trend': '利好', 'score': 3, 'news_count': 5},
        '人工智能': {'trend': '利好', 'score': 5, 'news_count': 8}
    }
    
    flow_result = {
        'top_inflow_sectors': [
            {'sector': '半导体', 'net_flow': 50000},
            {'sector': '人工智能', 'net_flow': 30000}
        ]
    }
    
    recommendations = [
        {
            'stock': {
                'code': '688981',
                'name': '中芯国际',
                'sector': '半导体',
                'price': 52.5,
                'change_pct': 3.2,
                'main_force_in': 150000000,
                'news_sentiment': '利好',
                'score': 8.5
            },
            'rating': '强烈推荐',
            'action': '重点关注，可考虑建仓',
            'risks': []
        }
    ]
    
    generator = ReportGenerator()
    result = generator.run(news_result, flow_result, recommendations)
    print(f"\n报告预览:\n{result['report_preview']}")
