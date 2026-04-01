"""
市场情绪分析模块 - 多维度量化个股情绪

情绪因子：
1. 新闻情感 (30%)
2. 资金流向 (25%)
3. 交易情绪 (20%)
4. 分析师预期 (15%)
5. 社交媒体 (10%)
"""
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class SentimentAnalyzer:
    """市场情绪分析器"""
    
    def __init__(self):
        # 情绪权重
        self.weights = {
            'news': 0.30,        # 新闻情感
            'capital': 0.25,     # 资金流
            'trading': 0.20,     # 交易情绪
            'analyst': 0.15,     # 分析师预期
            'social': 0.10       # 社交媒体
        }
        
        # 情绪等级
        self.levels = {
            'extreme_bullish': {'min': 0.8, 'label': '极度乐观', 'emoji': '🔥'},
            'bullish': {'min': 0.6, 'label': '乐观', 'emoji': '🔴'},
            'neutral': {'min': 0.4, 'label': '中性', 'emoji': '⚪'},
            'bearish': {'min': 0.2, 'label': '悲观', 'emoji': '🟡'},
            'extreme_bearish': {'min': 0.0, 'label': '极度悲观', 'emoji': '🟢'}
        }
    
    def analyze_news_sentiment(self, stock_code: str, stock_name: str) -> Dict:
        """
        分析新闻情感
        返回：情感分数 (0-1), 新闻数量，正面/负面比例
        """
        # 简化版：使用关键词匹配
        positive_keywords = [
            '利好', '突破', '增长', '订单', '签约', '预增', '超预期',
            '创新高', '获批', '中标', '合作', '重组', '增持', '回购'
        ]
        negative_keywords = [
            '利空', '下跌', '亏损', '处罚', '风险', '减持', '下滑',
            '违约', '诉讼', '调查', '警告', '退市', '爆雷'
        ]
        
        # 实际应用中应该爬取新闻
        # 这里返回模拟数据结构
        return {
            'score': 0.65,  # 0-1 之间
            'news_count': 15,
            'positive_count': 10,
            'negative_count': 3,
            'neutral_count': 2,
            'latest_headlines': [
                {'title': f'{stock_name}获大额订单', 'sentiment': 'positive'},
                {'title': f'{stock_name}业绩超预期', 'sentiment': 'positive'}
            ]
        }
    
    def analyze_capital_flow(self, stock_code: str) -> Dict:
        """
        分析资金流向
        返回：主力净流入，净流入占比，资金情绪分数
        """
        # 东方财富资金流 API
        try:
            url = 'http://push2.eastmoney.com/api/qt/stock/fflow/daykline/get'
            params = {
                'lmt': 0,
                'klt': 1,
                'fields1': 'f1,f2,f3,f7',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65',
                'ut': 'b2884a393a59ad64002292a3e90d46a5',
                'secid': f'1.{stock_code}' if stock_code.startswith('6') else f'0.{stock_code}'
            }
            
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if data.get('data') and data['data'].get('klines'):
                latest = data['data']['klines'][-1].split(',')
                main_force_net = float(latest[2])  # 主力净流入
                net_ratio = float(latest[6])  # 净流入占比
                
                # 转换为情绪分数 (0-1)
                if net_ratio > 10:
                    score = 0.9
                elif net_ratio > 5:
                    score = 0.7
                elif net_ratio > 0:
                    score = 0.5 + net_ratio / 20
                elif net_ratio > -5:
                    score = 0.5 + net_ratio / 20
                elif net_ratio > -10:
                    score = 0.3
                else:
                    score = 0.1
                
                return {
                    'score': score,
                    'main_force_net': main_force_net,
                    'net_ratio': net_ratio,
                    'trend': '流入' if net_ratio > 0 else '流出'
                }
        except Exception as e:
            pass
        
        # 返回默认值
        return {'score': 0.5, 'main_force_net': 0, 'net_ratio': 0, 'trend': '震荡'}
    
    def analyze_trading_sentiment(self, stock_code: str, price_data: Dict) -> Dict:
        """
        分析交易情绪
        需要：现价，涨跌幅，换手率，量比，振幅
        """
        score = 0.5
        
        # 涨跌幅贡献 (40%)
        change_pct = price_data.get('change_pct', 0)
        if change_pct >= 9.5:  # 涨停
            score += 0.4
        elif change_pct >= 5:
            score += 0.25
        elif change_pct >= 2:
            score += 0.1
        elif change_pct <= -9.5:  # 跌停
            score -= 0.4
        elif change_pct <= -5:
            score -= 0.25
        elif change_pct <= -2:
            score -= 0.1
        
        # 换手率贡献 (30%)
        turnover = price_data.get('turnover', 0)
        if 5 <= turnover <= 15:  # 健康换手
            score += 0.15
        elif turnover > 20:  # 过热
            score -= 0.1
        elif turnover < 1:  # 冷清
            score -= 0.1
        
        # 量比贡献 (30%)
        volume_ratio = price_data.get('volume_ratio', 1)
        if 1.5 <= volume_ratio <= 3:  # 温和放量
            score += 0.15
        elif volume_ratio > 5:  # 异常放量
            score -= 0.1
        elif volume_ratio < 0.5:  # 严重缩量
            score -= 0.1
        
        # 限制在 0-1 范围
        score = max(0, min(1, score))
        
        return {
            'score': score,
            'change_pct': change_pct,
            'turnover': turnover,
            'volume_ratio': volume_ratio,
            'status': '活跃' if turnover > 5 else '正常' if turnover > 1 else '冷清'
        }
    
    def analyze_analyst_sentiment(self, stock_code: str) -> Dict:
        """
        分析分析师预期
        返回：评级分布，目标价变化，预期分数
        """
        # 实际应用中调用券商 API 或爬取研报
        # 这里返回模拟数据
        return {
            'score': 0.65,
            'buy_count': 8,
            'hold_count': 3,
            'sell_count': 1,
            'avg_target_price': 55.0,
            'upside': 15.0  # 较现价上涨空间%
        }
    
    def analyze_social_sentiment(self, stock_code: str, stock_name: str) -> Dict:
        """
        分析社交媒体情绪
        爬取雪球、股吧、微博讨论
        """
        # 实际应用中需要爬虫
        # 这里返回模拟数据
        return {
            'score': 0.55,
            'discussion_count': 1250,
            'positive_ratio': 0.6,
            'hot_rank': 15,  # 热度排名
            'trending': True
        }
    
    def calculate_composite_sentiment(self, stock_code: str, stock_name: str, 
                                     price_data: Optional[Dict] = None) -> Dict:
        """
        计算综合情绪分数
        """
        if price_data is None:
            price_data = {}
        
        # 获取各维度情绪
        news = self.analyze_news_sentiment(stock_code, stock_name)
        capital = self.analyze_capital_flow(stock_code)
        trading = self.analyze_trading_sentiment(stock_code, price_data)
        analyst = self.analyze_analyst_sentiment(stock_code)
        social = self.analyze_social_sentiment(stock_code, stock_name)
        
        # 加权计算
        composite_score = (
            news['score'] * self.weights['news'] +
            capital['score'] * self.weights['capital'] +
            trading['score'] * self.weights['trading'] +
            analyst['score'] * self.weights['analyst'] +
            social['score'] * self.weights['social']
        )
        
        # 确定情绪等级
        level = self._get_sentiment_level(composite_score)
        
        # 生成情绪解读
        interpretation = self._generate_interpretation(
            composite_score, news, capital, trading, analyst, social
        )
        
        return {
            'composite_score': round(composite_score, 3),
            'level': level['label'],
            'emoji': level['emoji'],
            'breakdown': {
                'news': {'score': news['score'], 'weight': self.weights['news']},
                'capital': {'score': capital['score'], 'weight': self.weights['capital']},
                'trading': {'score': trading['score'], 'weight': self.weights['trading']},
                'analyst': {'score': analyst['score'], 'weight': self.weights['analyst']},
                'social': {'score': social['score'], 'weight': self.weights['social']}
            },
            'details': {
                'news': news,
                'capital': capital,
                'trading': trading,
                'analyst': analyst,
                'social': social
            },
            'interpretation': interpretation,
            'update_time': datetime.now().isoformat()
        }
    
    def _get_sentiment_level(self, score: float) -> Dict:
        """根据分数返回情绪等级"""
        for level_key, level_info in sorted(
            self.levels.items(), 
            key=lambda x: x[1]['min'], 
            reverse=True
        ):
            if score >= level_info['min']:
                return level_info
        return self.levels['neutral']
    
    def _generate_interpretation(self, composite: float, news: Dict, 
                                 capital: Dict, trading: Dict,
                                 analyst: Dict, social: Dict) -> str:
        """生成情绪解读"""
        interpretations = []
        
        # 综合判断
        if composite >= 0.7:
            interpretations.append("市场情绪极度乐观，注意短期过热风险")
        elif composite >= 0.55:
            interpretations.append("市场情绪偏乐观，资金关注度较高")
        elif composite >= 0.45:
            interpretations.append("市场情绪中性，多空分歧")
        elif composite >= 0.3:
            interpretations.append("市场情绪偏悲观，谨慎观望")
        else:
            interpretations.append("市场情绪极度悲观，可能存在超跌机会")
        
        # 资金流提示
        if capital['score'] > 0.7:
            interpretations.append("主力资金大幅流入")
        elif capital['score'] < 0.3:
            interpretations.append("主力资金持续流出")
        
        # 交易热度提示
        if trading['score'] > 0.7:
            interpretations.append("交易活跃度高，注意追高风险")
        elif trading['score'] < 0.3:
            interpretations.append("交易冷清，流动性不足")
        
        return "；".join(interpretations)
    
    def run(self, stocks: List[Dict]) -> List[Dict]:
        """
        批量分析多只股票的情绪
        stocks: [{'code': '002230', 'name': '科大讯飞', 'price_data': {...}}, ...]
        """
        print(f"[情绪分析] 开始分析 {len(stocks)} 只股票...")
        
        results = []
        for stock in stocks:
            print(f"[情绪分析] {stock['name']}({stock['code']})...")
            result = self.calculate_composite_sentiment(
                stock['code'], 
                stock['name'],
                stock.get('price_data', {})
            )
            result['code'] = stock['code']
            result['name'] = stock['name']
            results.append(result)
        
        # 按情绪分数排序
        results.sort(key=lambda x: x['composite_score'], reverse=True)
        
        print(f"[情绪分析] 完成")
        return results


if __name__ == '__main__':
    # 测试
    analyzer = SentimentAnalyzer()
    
    test_stocks = [
        {'code': '002230', 'name': '科大讯飞', 'price_data': {
            'change_pct': 6.82, 'turnover': 8.5, 'volume_ratio': 2.1
        }},
        {'code': '688981', 'name': '中芯国际', 'price_data': {
            'change_pct': 4.25, 'turnover': 5.2, 'volume_ratio': 1.8
        }},
        {'code': '002475', 'name': '立讯精密', 'price_data': {
            'change_pct': -1.2, 'turnover': 2.1, 'volume_ratio': 0.7
        }}
    ]
    
    results = analyzer.run(test_stocks)
    
    print("\n=== 情绪分析结果 ===")
    for r in results:
        print(f"{r['emoji']} {r['name']}: {r['level']} ({r['composite_score']})")
        print(f"   {r['interpretation']}")
