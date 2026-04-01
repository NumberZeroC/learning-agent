#!/usr/bin/env python3
"""
自动选股模块 - 多因子量化选股

功能：
- 基本面筛选（PE/PB/ROE/增长）
- 技术面确认（MACD/均线/量比）
- 资金流验证（主力/机构/融资）
- 综合评分排序
- TOP10 推荐
"""
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from stock_agent import TushareSource, AKShareSource, Config


class StockScreener:
    """股票筛选器"""
    
    def __init__(self, ts: TushareSource, ak: AKShareSource, config: dict = None):
        self.ts = ts
        self.ak = ak
        self.config = config or {}
        
        # 选股阈值
        self.thresholds = {
            'pe_max': 30,
            'pb_max': 5,
            'roe_min': 10,
            'revenue_growth_min': 10,
            'main_force_net_min': 5000000,  # 500 万
            'volume_ratio_min': 1.5,
        }
        
        # 更新阈值
        if 'fundamental' in self.config:
            self.thresholds.update(self.config['fundamental'])
    
    def fundamental_filter(self, stocks: List[Dict]) -> List[Dict]:
        """
        基本面筛选
        
        条件：
        - PE < 30
        - PB < 5
        - ROE > 10%
        - 营收增长 > 10%
        - 非 ST
        """
        filtered = []
        
        for stock in stocks:
            # 排除 ST
            if 'ST' in stock.get('name', ''):
                continue
            
            # 获取基本面数据
            ts_code = stock.get('ts_code', '')
            basic_data = self.ts.get_daily_basic(ts_code)
            
            if not basic_data:
                continue
            
            basic = basic_data[0] if isinstance(basic_data, list) else basic_data
            
            # PE 筛选
            pe = basic.get('pe', 999)
            if pe <= 0 or pe > self.thresholds['pe_max']:
                continue
            
            # PB 筛选
            pb = basic.get('pb', 999)
            if pb <= 0 or pb > self.thresholds['pb_max']:
                continue
            
            # 获取财务数据
            fina = self.ts.get_fina_indicator(ts_code)
            if fina:
                latest_fina = fina[0]
                
                # ROE 筛选
                roe = latest_fina.get('roe', 0)
                if roe < self.thresholds['roe_min']:
                    continue
                
                # 营收增长筛选
                revenue_growth = latest_fina.get('revenue_yoy', 0)
                if revenue_growth < self.thresholds['revenue_growth_min']:
                    continue
            
            # 通过筛选
            stock['fundamental_score'] = self._score_fundamental(basic, fina[0] if fina else None)
            filtered.append(stock)
        
        print(f"基本面筛选后：{len(filtered)}只")
        return filtered
    
    def technical_filter(self, stocks: List[Dict]) -> List[Dict]:
        """
        技术面筛选
        
        条件：
        - MACD 金叉
        - 均线多头
        - 量比 > 1.5
        """
        filtered = []
        
        for stock in stocks:
            ts_code = stock.get('ts_code', '')
            
            # 获取日线数据（用于计算技术指标）
            daily = self.ts.get_daily(ts_code)
            if not daily:
                continue
            
            # 简单技术面评分（实际应该计算 MACD、均线等）
            tech_score = self._score_technical(daily)
            
            if tech_score >= 20:  # 最低 20 分
                stock['technical_score'] = tech_score
                filtered.append(stock)
        
        print(f"技术面筛选后：{len(filtered)}只")
        return filtered
    
    def capital_filter(self, stocks: List[Dict]) -> List[Dict]:
        """
        资金流筛选
        
        条件：
        - 主力净流入 > 500 万
        """
        filtered = []
        
        for stock in stocks:
            ts_code = stock.get('ts_code', '')
            
            # 获取资金流数据
            moneyflow = self.ts.get_moneyflow(ts_code)
            
            if not moneyflow:
                continue
            
            net_inflow = moneyflow.get('net_mf_amount', 0)
            
            if net_inflow >= self.thresholds['main_force_net_min']:
                stock['capital_score'] = self._score_capital(moneyflow)
                stock['main_force_net'] = net_inflow
                filtered.append(stock)
        
        print(f"资金流验证后：{len(filtered)}只")
        return filtered
    
    def calculate_scores(self, stocks: List[Dict], strategy: str = 'balanced') -> List[Dict]:
        """
        计算综合评分
        
        策略：
        - balanced: 均衡策略 (30/35/25/10)
        - value: 价值策略 (40/30/20/10)
        - momentum: 动量策略 (20/45/25/10)
        - capital: 资金流策略 (25/25/40/10)
        """
        # 权重配置
        weights = {
            'balanced': {'fundamental': 0.30, 'technical': 0.35, 'capital': 0.25, 'sentiment': 0.10},
            'value': {'fundamental': 0.40, 'technical': 0.30, 'capital': 0.20, 'sentiment': 0.10},
            'momentum': {'fundamental': 0.20, 'technical': 0.45, 'capital': 0.25, 'sentiment': 0.10},
            'capital': {'fundamental': 0.25, 'technical': 0.25, 'capital': 0.40, 'sentiment': 0.10},
        }
        
        w = weights.get(strategy, weights['balanced'])
        
        for stock in stocks:
            fundamental = stock.get('fundamental_score', 0)
            technical = stock.get('technical_score', 0)
            capital = stock.get('capital_score', 0)
            sentiment = stock.get('sentiment_score', 5)  # 默认 5 分
            
            # 综合得分
            total_score = (
                fundamental * w['fundamental'] +
                technical * w['technical'] +
                capital * w['capital'] +
                sentiment * w['sentiment']
            )
            
            stock['total_score'] = total_score
        
        # 按得分排序
        stocks.sort(key=lambda x: x.get('total_score', 0), reverse=True)
        
        return stocks
    
    def _score_fundamental(self, basic: Dict, fina: Optional[Dict]) -> float:
        """基本面评分（满分 30）"""
        score = 0
        
        # PE 评分（8 分）
        pe = basic.get('pe', 999)
        if 0 < pe <= 15:
            score += 8
        elif 15 < pe <= 30:
            score += 5
        
        # PB 评分（5 分）
        pb = basic.get('pb', 999)
        if 0 < pb <= 3:
            score += 5
        elif 3 < pb <= 5:
            score += 3
        
        # ROE 评分（8 分）
        if fina:
            roe = fina.get('roe', 0)
            if roe > 20:
                score += 8
            elif roe > 10:
                score += 5
        
        # 营收增长评分（5 分）
        if fina:
            growth = fina.get('revenue_yoy', 0)
            if growth > 30:
                score += 5
            elif growth > 10:
                score += 3
        
        # 非 ST（4 分）
        score += 4
        
        return min(score, 30)
    
    def _score_technical(self, daily: Dict) -> float:
        """技术面评分（满分 35）"""
        # 简化版本：基于涨跌幅和量比
        score = 15  # 基础分
        
        pct_chg = daily.get('pct_chg', 0)
        if pct_chg > 3:
            score += 10
        elif pct_chg > 0:
            score += 5
        
        # 量比评分（简化）
        score += 10
        
        return min(score, 35)
    
    def _score_capital(self, moneyflow: Dict) -> float:
        """资金流评分（满分 25）"""
        score = 0
        
        net_inflow = moneyflow.get('net_mf_amount', 0)
        
        if net_inflow > 10000000:  # 1000 万
            score += 12
        elif net_inflow > 5000000:  # 500 万
            score += 8
        elif net_inflow > 0:
            score += 3
        
        # 大单评分
        buy_lg = moneyflow.get('buy_lg_amount', 0)
        if buy_lg > 0:
            score += 8
        
        # 特大单评分
        buy_elg = moneyflow.get('buy_elg_amount', 0)
        if buy_elg > 0:
            score += 5
        
        return min(score, 25)
    
    def screen(self, strategy: str = 'balanced', top_n: int = 10) -> List[Dict]:
        """
        执行完整选股流程
        
        Returns:
            推荐股票列表（TOP N）
        """
        print("=" * 60)
        print(f"📈 Stock-Agent 自动选股")
        print(f"策略：{strategy}")
        print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 1. 获取股票池
        print("\n1️⃣  获取股票池...")
        stocks = self.ts.get_stock_basic()
        print(f"   全市场股票：{len(stocks)}只")
        
        # 2. 基本面筛选
        print("\n2️⃣  基本面筛选...")
        filtered = self.fundamental_filter(stocks)
        
        # 3. 技术面筛选
        print("\n3️⃣  技术面筛选...")
        filtered = self.technical_filter(filtered)
        
        # 4. 资金流验证
        print("\n4️⃣  资金流验证...")
        filtered = self.capital_filter(filtered)
        
        # 5. 综合评分
        print("\n5️⃣  综合评分...")
        scored = self.calculate_scores(filtered, strategy)
        
        # 6. TOP N 推荐
        recommendations = scored[:top_n]
        
        print("\n" + "=" * 60)
        print(f"✅ 推荐 TOP{len(recommendations)}")
        print("=" * 60)
        
        for i, stock in enumerate(recommendations, 1):
            print(f"\n{i}. {stock.get('name', '')} ({stock.get('ts_code', '')})")
            print(f"   综合得分：{stock.get('total_score', 0):.1f}")
            print(f"   基本面：{stock.get('fundamental_score', 0):.0f}/30")
            print(f"   技术面：{stock.get('technical_score', 0):.0f}/35")
            print(f"   资金流：{stock.get('capital_score', 0):.0f}/25")
            if 'main_force_net' in stock:
                print(f"   主力净流入：{stock['main_force_net']/10000:.1f}万")
        
        print("\n" + "=" * 60)
        
        return recommendations


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='自动选股')
    parser.add_argument('--strategy', '-s', default='balanced',
                       choices=['balanced', 'value', 'momentum', 'capital'],
                       help='选股策略')
    parser.add_argument('--top', '-t', type=int, default=10, help='推荐数量')
    parser.add_argument('--config', '-c', default='config.yaml', help='配置文件')
    
    args = parser.parse_args()
    
    # 加载配置
    config = Config(args.config)
    
    # 初始化数据源
    ts_token = config.get('tushare.token', '')
    ts = TushareSource(token=ts_token, cache_ttl=600)
    
    try:
        ak = AKShareSource(cache_ttl=300)
    except ImportError:
        print("⚠️ AKShare 未安装，仅使用 Tushare")
        ak = None
    
    # 获取选股配置
    selection_config = config.get('stock_selection', {})
    
    # 创建筛选器
    screener = StockScreener(ts, ak, selection_config)
    
    # 执行选股
    recommendations = screener.screen(strategy=args.strategy, top_n=args.top)
    
    # 保存结果
    if recommendations:
        import json
        result_file = Path(__file__).parent.parent / 'data' / f'selection_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        result_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(recommendations, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📄 结果已保存：{result_file}")


if __name__ == '__main__':
    main()
