import logging
from datetime import datetime

class SimulatedExchange:
    def __init__(self, initial_balance=10000):
        self.balance = initial_balance
        self.positions = {}
        self.trade_history = []
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            filename='simulation.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('SimulatedExchange')
        
    def create_market_buy_order(self, symbol, amount):
        current_price = self.fetch_ticker(symbol)['last']
        cost = amount * current_price
        
        if cost > self.balance:
            raise Exception("Insufficient funds")
            
        self.balance -= cost
        self.positions[symbol] = self.positions.get(symbol, 0) + amount
        
        order = {
            'symbol': symbol,
            'type': 'market',
            'side': 'buy',
            'amount': amount,
            'price': current_price,
            'timestamp': datetime.now()
        }
        
        self.trade_history.append(order)
        self.logger.info(f"Buy order executed: {order}")
        return order
        
    def create_market_sell_order(self, symbol, amount):
        pass
        
    def fetch_balance(self):
        return {
            'total': {'USDT': self.balance}
        }
