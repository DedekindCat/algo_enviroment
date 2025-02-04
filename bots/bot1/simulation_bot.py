from bot import CryptoBot
from bots.bot1.simulated_exchange import SimulatedExchange
import logging

class SimulationBot(CryptoBot):
    def __init__(self, initial_balance=10000):
        super().__init__()
        self.exchange = SimulatedExchange(initial_balance)
        
    def setup_logging(self):
        logging.basicConfig(
            filename='simulation_bot.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('SimulationBot')

if __name__ == "__main__":
    print("Starting bot in simulation mode...")
    sim_bot = SimulationBot(initial_balance=10000)
    sim_bot.run()
