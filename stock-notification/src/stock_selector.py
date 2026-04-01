"""
选股逻辑模块 - 综合新闻和资金流推荐股票
"""
from datetime import datetime
from typing import List, Dict, Optional


class StockSelector:
    """智能选股器"""
    
    def __init__(self):
        # 选股权重配置
        self.weights = {
            'news_sentiment': 0.3,    # 新闻情感权重
            'capital_flow': 0.4,      # 资金流权重
            'price_performance': 0.3  # 价格表现权重
        }
    
    def calculate_stock_score(self, stock_info: Dict, news_sentiment: Dict, flow_data: Dict) -> float:
        """计算股票综合得分"""
        score = 0.0
        
        # 新闻情感分 (0-10)
        news_score = 5.0
        if news_sentiment:
            sentiment_score = news_sentiment.get('score', 0)
            news_score = 5 + min(max(sentiment_score, -5), 5)  # 限制在 0-10
        
        # 资金流分 (0-10)
        flow_score = 5.0
        if flow_data:
            main_force_in = flow_data.get('main_force_in', 0)
            # 净流入 1 亿以上得满分
            flow_score = 5 + min(main_force_in / 10000000, 5)
        
        # 价格表现分 (0-10)
        price_score = 5.0
        change_pct = stock_info.get('change_pct', 0)
        price_score = 5 + min(max(change_pct, -10), 10) / 2
        
        # 加权总分
        score = (
            news_score * self.weights['news_sentiment'] +
            flow_score * self.weights['capital_flow'] +
            price_score * self.weights['price_performance']
        )
        
        return round(score, 2)
    
    def select_stocks(self, news_result: Dict, flow_result: Dict, top_n: int = 10) -> List[Dict]:
        """综合选股"""
        candidates = []
        
        # 遍历各板块龙头股
        for sector, data in flow_result.get('sector_analysis', {}).items():
            leader = data.get('leader')
            if not leader:
                continue
            
            # 获取该板块新闻情感
            sector_news = news_result.get(sector, {})
            
            # 计算综合得分
            score = self.calculate_stock_score(leader, sector_news, leader)
            
            candidates.append({
                'code': leader['code'],
                'name': leader['name'],
                'sector': sector,
                'price': leader.get('price', 0),
                'change_pct': leader.get('change_pct', 0),
                'main_force_in': leader.get('main_force_in', 0),
                'news_sentiment': sector_news.get('trend', '中性'),
                'score': score,
                'reason': leader.get('reason', '')
            })
        
        # 按得分排序
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        return candidates[:top_n]
    
    def generate_recommendation(self, stock: Dict) -> Dict:
        """生成个股推荐意见"""
        score = stock['score']
        
        # 根据得分给出评级
        if score >= 8:
            rating = '强烈推荐'
            action = '重点关注，可考虑建仓'
        elif score >= 6.5:
            rating = '推荐'
            action = '逢低关注'
        elif score >= 5:
            rating = '中性'
            action = '观望为主'
        elif score >= 3.5:
            rating = '谨慎'
            action = '注意风险'
        else:
            rating = '回避'
            action = '建议规避'
        
        # 生成风险提示
        risks = []
        if stock['change_pct'] > 7:
            risks.append('短期涨幅较大，注意回调风险')
        if stock['main_force_in'] < 0:
            risks.append('主力资金流出，需谨慎')
        if stock['news_sentiment'] == '利空':
            risks.append('负面新闻较多')
        
        return {
            'stock': stock,
            'rating': rating,
            'action': action,
            'risks': risks,
            'confidence': min(score / 10, 1.0)
        }
    
    def run(self, news_result: Dict, flow_result: Dict, top_n: int = 10) -> List[Dict]:
        """执行选股流程"""
        print("[选股] 开始综合选股...")
        
        # 选股
        selected = self.select_stocks(news_result, flow_result, top_n)
        
        # 生成推荐意见
        recommendations = []
        for stock in selected:
            rec = self.generate_recommendation(stock)
            recommendations.append(rec)
        
        print(f"[选股] 完成，推荐 {len(recommendations)} 只股票")
        
        return recommendations


if __name__ == '__main__':
    # 测试数据
    news_result = {
        '半导体': {'trend': '利好', 'score': 3},
        '人工智能': {'trend': '利好', 'score': 5},
        '新能源': {'trend': '中性', 'score': 0}
    }
    
    flow_result = {
        'sector_analysis': {
            '半导体': {
                'leader': {
                    'code': '688981',
                    'name': '中芯国际',
                    'price': 52.5,
                    'change_pct': 3.2,
                    'main_force_in': 150000000,
                    'reason': '主力净流入 1.5 亿'
                }
            },
            '人工智能': {
                'leader': {
                    'code': '002230',
                    'name': '科大讯飞',
                    'price': 48.8,
                    'change_pct': 5.1,
                    'main_force_in': 80000000,
                    'reason': '涨幅 5.1% 领涨板块'
                }
            }
        }
    }
    
    selector = StockSelector()
    result = selector.run(news_result, flow_result)
    
    print("\n=== 选股推荐 ===")
    for rec in result:
        s = rec['stock']
        print(f"{s['name']}({s['code']}): {rec['rating']} - 得分{s['score']}")
        print(f"  建议：{rec['action']}")
        if rec['risks']:
            print(f"  风险：{', '.join(rec['risks'])}")
