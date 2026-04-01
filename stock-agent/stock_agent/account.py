"""
账户管理模块 - 模拟交易账户
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class Position:
    """持仓"""
    stock_code: str
    stock_name: str
    volume: int  # 持股数量
    avg_cost: float  # 平均成本
    current_price: float = 0.0  # 当前价
    buy_date: str = ""  # 买入日期
    
    @property
    def market_value(self) -> float:
        """市值"""
        return self.volume * self.current_price
    
    @property
    def cost_value(self) -> float:
        """成本"""
        return self.volume * self.avg_cost
    
    @property
    def profit(self) -> float:
        """盈利"""
        return self.market_value - self.cost_value
    
    @property
    def profit_rate(self) -> float:
        """收益率"""
        if self.cost_value == 0:
            return 0
        return self.profit / self.cost_value


@dataclass
class Order:
    """订单"""
    stock_code: str
    stock_name: str
    side: str  # BUY | SELL
    volume: int
    price: float
    timestamp: str = ""
    status: str = "pending"  # pending | filled | cancelled
    order_id: str = ""
    
    def fill(self, filled_price: float) -> None:
        """成交"""
        self.price = filled_price
        self.status = "filled"
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


@dataclass
class Trade:
    """成交记录"""
    stock_code: str
    stock_name: str
    side: str
    volume: int
    price: float
    amount: float
    commission: float
    stamp_duty: float
    timestamp: str
    order_id: str = ""


class Account:
    """模拟交易账户"""
    
    def __init__(self, initial_capital: float = 1000000, 
                 commission_rate: float = 0.0003,
                 stamp_duty: float = 0.001):
        self.initial_capital = initial_capital
        self.cash = initial_capital  # 可用资金
        self.commission_rate = commission_rate  # 佣金率
        self.stamp_duty = stamp_duty  # 印花税
        
        self.positions: Dict[str, Position] = {}  # 持仓
        self.orders: List[Order] = []  # 订单
        self.trades: List[Trade] = []  # 成交记录
        
        self.created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.last_updated = self.created_at
    
    @property
    def market_value(self) -> float:
        """持仓市值"""
        return sum(pos.market_value for pos in self.positions.values())
    
    @property
    def total_value(self) -> float:
        """总资产"""
        return self.cash + self.market_value
    
    @property
    def total_return(self) -> float:
        """总收益"""
        return self.total_value - self.initial_capital
    
    @property
    def return_rate(self) -> float:
        """收益率"""
        return self.total_return / self.initial_capital
    
    @property
    def position_count(self) -> int:
        """持仓数量"""
        return len(self.positions)
    
    @property
    def position_ratio(self) -> float:
        """仓位"""
        if self.total_value == 0:
            return 0
        return self.market_value / self.total_value
    
    def update_prices(self, prices: Dict[str, float]) -> None:
        """更新持仓价格"""
        for code, price in prices.items():
            if code in self.positions:
                self.positions[code].current_price = price
        self.last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def buy(self, stock_code: str, stock_name: str, volume: int, 
            price: float) -> Optional[Order]:
        """买入"""
        # 检查资金
        required = volume * price * (1 + self.commission_rate)
        if required > self.cash:
            print(f"❌ 资金不足：需要{required:.2f}, 可用{self.cash:.2f}")
            return None
        
        # 创建订单
        order = Order(
            stock_code=stock_code,
            stock_name=stock_name,
            side='BUY',
            volume=volume,
            price=price,
            order_id=f"BUY_{stock_code}_{len(self.orders)}"
        )
        
        # 执行交易
        commission = volume * price * self.commission_rate
        total_cost = volume * price + commission
        
        self.cash -= total_cost
        
        # 更新持仓
        if stock_code in self.positions:
            pos = self.positions[stock_code]
            total_cost = pos.volume * pos.avg_cost + volume * price
            pos.volume += volume
            pos.avg_cost = total_cost / pos.volume
        else:
            self.positions[stock_code] = Position(
                stock_code=stock_code,
                stock_name=stock_name,
                volume=volume,
                avg_cost=price,
                current_price=price,
                buy_date=datetime.now().strftime('%Y-%m-%d')
            )
        
        # 记录订单和成交
        order.fill(price)
        self.orders.append(order)
        self.trades.append(Trade(
            stock_code=stock_code,
            stock_name=stock_name,
            side='BUY',
            volume=volume,
            price=price,
            amount=volume * price,
            commission=commission,
            stamp_duty=0,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            order_id=order.order_id
        ))
        
        print(f"✅ 买入 {stock_name}({stock_code}) {volume}股 @¥{price:.2f}")
        return order
    
    def sell(self, stock_code: str, volume: int, price: float) -> Optional[Order]:
        """卖出"""
        # 检查持仓
        if stock_code not in self.positions:
            print(f"❌ 无持仓：{stock_code}")
            return None
        
        pos = self.positions[stock_code]
        if pos.volume < volume:
            print(f"❌ 持仓不足：持有{pos.volume}, 卖出{volume}")
            return None
        
        # 创建订单
        order = Order(
            stock_code=stock_code,
            stock_name=pos.stock_name,
            side='SELL',
            volume=volume,
            price=price,
            order_id=f"SELL_{stock_code}_{len(self.orders)}"
        )
        
        # 执行交易
        commission = volume * price * self.commission_rate
        stamp_duty = volume * price * self.stamp_duty
        total_received = volume * price - commission - stamp_duty
        
        self.cash += total_received
        
        # 更新持仓
        pos.volume -= volume
        if pos.volume == 0:
            del self.positions[stock_code]
        
        # 记录订单和成交
        order.fill(price)
        self.orders.append(order)
        self.trades.append(Trade(
            stock_code=stock_code,
            stock_name=pos.stock_name,
            side='SELL',
            volume=volume,
            price=price,
            amount=volume * price,
            commission=commission,
            stamp_duty=stamp_duty,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            order_id=order.order_id
        ))
        
        print(f"✅ 卖出 {pos.stock_name}({stock_code}) {volume}股 @¥{price:.2f}")
        return order
    
    def get_position(self, stock_code: str) -> Optional[Position]:
        """获取持仓"""
        return self.positions.get(stock_code)
    
    def get_positions(self) -> List[Position]:
        """获取所有持仓"""
        return list(self.positions.values())
    
    def get_summary(self) -> Dict:
        """账户概览"""
        return {
            'initial_capital': self.initial_capital,
            'cash': self.cash,
            'market_value': self.market_value,
            'total_value': self.total_value,
            'total_return': self.total_return,
            'return_rate': self.return_rate,
            'position_count': self.position_count,
            'position_ratio': self.position_ratio,
            'last_updated': self.last_updated,
        }
    
    def __repr__(self) -> str:
        return f"Account(总资产={self.total_value:.2f}, 收益={self.return_rate:.2%})"
