#!/usr/bin/env python3
"""
自动交易执行模块

功能：
- 接收选股推荐
- 风控检查
- 仓位计算
- 执行买入/卖出
- 订单管理
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from stock_agent import Account, Config, TushareSource
from stock_agent.account import Order, Trade


class TradeExecutor:
    """交易执行器"""
    
    def __init__(self, account: Account, config: dict = None):
        self.account = account
        self.config = config or {}
        
        # 风控限制
        self.risk_limits = {
            'max_single_position': 0.30,  # 单只股票最大 30%
            'max_sector_exposure': 0.50,  # 单板块最大 50%
            'min_cash_ratio': 0.10,       # 最低现金 10%
            'max_daily_trades': 10,       # 每日最多 10 笔
        }
        
        # 更新风控配置
        if 'risk_limits' in self.config:
            self.risk_limits.update(self.config['risk_limits'])
        
        # 今日交易计数
        self.today_trades = 0
        self.today = datetime.now().strftime('%Y-%m-%d')
    
    def risk_check(self, stock: Dict) -> tuple:
        """
        风控检查
        
        Returns:
            (是否通过，原因)
        """
        # 1. 检查单只股票仓位
        code = stock.get('code', stock.get('ts_code', ''))
        position = self.account.get_position(code)
        
        if position:
            current_ratio = position.market_value / self.account.total_value
            if current_ratio >= self.risk_limits['max_single_position']:
                return False, f"单只股票仓位已达上限 ({current_ratio:.1%})"
        
        # 2. 检查现金比例
        if self.account.cash / self.account.total_value < self.risk_limits['min_cash_ratio']:
            return False, f"现金比例不足 ({self.account.cash/self.account.total_value:.1%})"
        
        # 3. 检查日交易次数
        if self.today_trades >= self.risk_limits['max_daily_trades']:
            return False, f"今日交易次数已达上限 ({self.today_trades}/{self.risk_limits['max_daily_trades']})"
        
        # 4. 检查停牌（简化）
        if 'ST' in stock.get('name', ''):
            return False, "ST 股票"
        
        return True, "通过"
    
    def calculate_position(self, stock: Dict, strategy: str = 'balanced') -> int:
        """
        计算买入仓位
        
        策略：
        - 单只股票不超过 10%
        - 100 股整数倍
        """
        # 目标仓位：10%
        target_ratio = 0.10
        
        # 可用资金（保留 10% 现金）
        available_cash = self.account.cash - (self.account.total_value * self.risk_limits['min_cash_ratio'])
        
        # 目标金额
        target_amount = self.account.total_value * target_ratio
        
        # 实际买入金额（取较小值）
        buy_amount = min(target_amount, available_cash)
        
        # 获取最新价格
        price = stock.get('price', 0)
        if price <= 0:
            price = stock.get('current_price', 0)
        
        if price <= 0:
            return 0
        
        # 计算股数（100 股整数倍）
        volume = int(buy_amount / price / 100) * 100
        
        # 最少 100 股
        if volume < 100:
            return 0
        
        return volume
    
    def execute_buy(self, stock: Dict, volume: int = None, strategy: str = 'balanced') -> Optional[Order]:
        """
        执行买入
        
        Args:
            stock: 股票信息
            volume: 买入数量（空则自动计算）
            strategy: 策略
        
        Returns:
            订单对象（失败返回 None）
        """
        code = stock.get('ts_code', stock.get('code', ''))
        name = stock.get('name', '')
        
        # 1. 风控检查
        passed, reason = self.risk_check(stock)
        if not passed:
            print(f"❌ 风控拒绝 {name}: {reason}")
            return None
        
        # 2. 计算仓位
        if volume is None:
            volume = self.calculate_position(stock, strategy)
        
        if volume <= 0:
            print(f"❌ 仓位计算失败 {name}")
            return None
        
        # 3. 获取最新价格
        price = stock.get('price', 0)
        if price <= 0:
            print(f"❌ 价格无效 {name}")
            return None
        
        # 4. 检查资金
        required = volume * price * (1 + self.account.commission_rate)
        if required > self.account.cash:
            print(f"❌ 资金不足 {name}: 需要¥{required:,.2f}, 可用¥{self.account.cash:,.2f}")
            return None
        
        # 5. 执行买入
        order = self.account.buy(code, name, volume, price)
        
        if order:
            self.today_trades += 1
            print(f"✅ 买入 {name} {volume}股 @¥{price:.2f} (¥{volume*price:,.2f})")
        
        return order
    
    def execute_sell(self, code: str, volume: int = None, reason: str = '') -> Optional[Order]:
        """
        执行卖出
        
        Args:
            code: 股票代码
            volume: 卖出数量（空则全部卖出）
            reason: 卖出原因
        """
        position = self.account.get_position(code)
        
        if not position:
            print(f"❌ 无持仓 {code}")
            return None
        
        if volume is None:
            volume = position.volume
        
        if volume <= 0 or volume > position.volume:
            print(f"❌ 卖出数量无效 {code}: {volume}")
            return None
        
        # 执行卖出
        order = self.account.sell(code, volume, position.current_price)
        
        if order:
            self.today_trades += 1
            print(f"✅ 卖出 {position.stock_name} {volume}股 @¥{position.current_price:.2f} ({reason})")
        
        return order
    
    def check_stop_loss(self) -> List[Order]:
        """
        检查止损
        
        Returns:
            执行的止损订单列表
        """
        orders = []
        stop_loss_pct = self.risk_limits.get('stop_loss_pct', 0.08)
        
        for position in self.account.get_positions():
            loss_pct = position.profit_rate
            
            # 止损检查
            if loss_pct < -stop_loss_pct:
                # 全部卖出
                order = self.execute_sell(
                    position.stock_code,
                    reason=f"止损 {loss_pct:.1%}"
                )
                if order:
                    orders.append(order)
        
        return orders
    
    def check_take_profit(self) -> List[Order]:
        """
        检查止盈
        
        Returns:
            执行的止盈订单列表
        """
        orders = []
        take_profit_pct = self.risk_limits.get('take_profit_pct', 0.20)
        
        for position in self.account.get_positions():
            profit_pct = position.profit_rate
            
            # 止盈检查（卖出一半）
            if profit_pct > take_profit_pct:
                volume = position.volume // 2
                if volume >= 100:
                    order = self.execute_sell(
                        position.stock_code,
                        volume=volume,
                        reason=f"止盈 {profit_pct:.1%}"
                    )
                    if order:
                        orders.append(order)
        
        return orders
    
    def execute_recommendations(self, recommendations: List[Dict], strategy: str = 'balanced') -> Dict:
        """
        执行选股推荐
        
        Args:
            recommendations: 推荐股票列表
            strategy: 策略
        
        Returns:
            执行结果统计
        """
        print("\n" + "=" * 60)
        print("🤖 执行选股推荐")
        print("=" * 60)
        
        results = {
            'success': 0,
            'failed': 0,
            'total_amount': 0,
            'orders': []
        }
        
        for stock in recommendations:
            # 执行买入
            order = self.execute_buy(stock, strategy=strategy)
            
            if order:
                results['success'] += 1
                results['total_amount'] += order.volume * order.price
                results['orders'].append({
                    'code': order.stock_code,
                    'name': order.stock_name,
                    'side': 'BUY',
                    'volume': order.volume,
                    'price': order.price
                })
            else:
                results['failed'] += 1
        
        print("\n" + "=" * 60)
        print(f"执行完成")
        print(f"成功：{results['success']}只")
        print(f"失败：{results['failed']}只")
        print(f"总金额：¥{results['total_amount']:,.2f}")
        print("=" * 60)
        
        return results
    
    def get_summary(self) -> Dict:
        """获取执行总结"""
        return {
            'date': self.today,
            'total_trades': self.today_trades,
            'account_summary': self.account.get_summary(),
        }


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='自动交易执行')
    parser.add_argument('--recommendations', '-r', type=str, help='推荐文件路径')
    parser.add_argument('--strategy', '-s', default='balanced', help='交易策略')
    parser.add_argument('--config', '-c', default='config.yaml', help='配置文件')
    parser.add_argument('--check-only', action='store_true', help='仅检查止损止盈')
    
    args = parser.parse_args()
    
    # 加载配置
    config = Config(args.config)
    
    # 创建账户
    account = Account(
        initial_capital=config.initial_capital,
        commission_rate=config.commission_rate,
        stamp_duty=config.stamp_duty
    )
    
    # 创建执行器
    executor = TradeExecutor(account, config.get('risk_limits', {}))
    
    if args.check_only:
        # 仅检查止损止盈
        print("检查止损...")
        stop_orders = executor.check_stop_loss()
        print(f"止损订单：{len(stop_orders)}个")
        
        print("\n检查止盈...")
        profit_orders = executor.check_take_profit()
        print(f"止盈订单：{len(profit_orders)}个")
        
    elif args.recommendations:
        # 执行推荐
        rec_file = Path(args.recommendations)
        if rec_file.exists():
            with open(rec_file, 'r', encoding='utf-8') as f:
                recommendations = json.load(f)
            
            executor.execute_recommendations(recommendations, args.strategy)
        else:
            print(f"❌ 推荐文件不存在：{rec_file}")
    
    # 输出总结
    summary = executor.get_summary()
    print(f"\n📊 今日总结")
    print(f"交易次数：{summary['total_trades']}")
    print(f"总资产：¥{summary['account_summary']['total_value']:,.2f}")
    print(f"收益率：{summary['account_summary']['return_rate']:+.2%}")


if __name__ == '__main__':
    main()
