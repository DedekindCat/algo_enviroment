import ccxt
import polars as pl
from datetime import datetime
import os
from dotenv import load_dotenv
import time
import signal
import sys
import joblib  
import numpy as np
import logging

class CryptoBot:
    def __init__(self):
        load_dotenv()
        
        self.running = True
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # データ管理用の属性を追加
        self.historical_data = None
        self.latest_predictions = None
        
        # 取引所の設定
        self.exchange = ccxt.binance({
            'apiKey': os.getenv('EXCHANGE_API_KEY'),
            'secret': os.getenv('EXCHANGE_SECRET'),
            'enableRateLimit': True,
            'rateLimit': 1000,  # ミリ秒単位でのレート制限
            'options': {
                'defaultType': 'future'  # 先物取引用（必要な場合）
            }
        })
        
        self.model = None
        self.load_model()
        
        self.setup_logging()
    
    def setup_logging(self):
        logging.basicConfig(
            filename='crypto_bot.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('CryptoBot')
    
    def signal_handler(self, signum, frame):
        print("\nBot stopping...")
        self.running = False

    def fetch_market_data(self, symbol, timeframe='1m', limit=100):
        """市場データの取得（リアルタイムおよび履歴データ用）"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pl.DataFrame({
                'timestamp': [x[0] for x in ohlcv],
                'open': [x[1] for x in ohlcv],
                'high': [x[2] for x in ohlcv],
                'low': [x[3] for x in ohlcv],
                'close': [x[4] for x in ohlcv],
                'volume': [x[5] for x in ohlcv]
            })
            df = df.with_columns(
                pl.col('timestamp').cast(pl.Datetime).alias('timestamp')
            )
            return df
        except Exception as e:
            print(f"Error fetching market data: {e}")
            return None

    def load_model(self, model_path='models/bot1/model.joblib'):
        """学習済みモデルの読み込み"""
        try:
            self.model = joblib.load(model_path)
            print("Model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")
            
    def predict(self, features):
        """モデルによる予測"""
        if self.model is None:
            return None
        try:
            prediction = self.model.predict(features)
            return prediction
        except Exception as e:
            print(f"Error in prediction: {e}")
            return None

    def run(self):
        consecutive_errors = 0
        while self.running:
            try:
                # 既存のコード（startLine: 77, endLine: 114）
                consecutive_errors = 0  # エラーカウントをリセット
                
            except Exception as e:
                consecutive_errors += 1
                print(f"Error in main loop: {e}")
                
                # エラーが続く場合は待機時間を延長
                wait_time = min(60 * consecutive_errors, 3600)  # 最大1時間まで
                print(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)

    def calculate_features(self, df):
        """予測用の特徴量を計算"""
        df = df.with_columns([
            pl.col('close').rolling_mean(window_size=20).alias('MA20'),
            pl.col('close').rolling_mean(window_size=50).alias('MA50'),
            pl.col('close').pct_change().alias('returns'),
            pl.col('close').rolling_std(window_size=20).alias('volatility')
        ])
        return df

    def get_position(self, current_price, predicted_price, threshold=0.0001):
        """ポジションの決定
        Returns:
            1: ロング
            -1: ショート
            0: ニュートラル
        """
        price_change = (predicted_price - current_price) / current_price
        
        if price_change > threshold:
            return 1  # ロング
        elif price_change < -threshold:
            return -1  # ショート
        return 0  # ニュートラル

    def execute_trade(self, symbol, side, amount):
        """取引の実行"""
        try:
            if side == 1:  # LONG
                order = self.exchange.create_market_buy_order(symbol, amount)
            elif side == -1:  # SHORT
                order = self.exchange.create_market_sell_order(symbol, amount)
            print(f"Order executed: {side} {amount} {symbol}")
            return order
        except Exception as e:
            print(f"Error executing trade: {e}")
            return None

    def manage_position(self, symbol, position, current_price):
        """ポジション管理"""
        try:
            # 現在のポジションを取得
            balance = self.exchange.fetch_balance()
            current_position = balance['total']['BTC'] if 'BTC' in balance['total'] else 0
            
            # 取引量の設定（例：100USD相当）
            trade_amount = 100 / current_price
            
            if position == 1 and current_position <= 0:  # LONGポジションを取る
                order = self.execute_trade(symbol, 1, trade_amount)
                if order:
                    # 1分後に決済するためのフラグを設定
                    self.position_time = time.time()
                    self.current_position_size = trade_amount
                return order
            elif position == -1 and current_position >= 0:  # SHORTポジションを取る
                order = self.execute_trade(symbol, -1, trade_amount)
                if order:
                    # 1分後に決済するためのフラグを設定
                    self.position_time = time.time()
                    self.current_position_size = trade_amount
                return order
            
            return None
        except Exception as e:
            print(f"Error managing position: {e}")
            return None

    def check_and_close_position(self, symbol):
        """ポジションの決済確認"""
        try:
            if hasattr(self, 'position_time') and hasattr(self, 'current_position_size'):
                # 1分経過したかチェック
                if time.time() - self.position_time >= 60:
                    # 現在のポジションを取得
                    balance = self.exchange.fetch_balance()
                    current_position = balance['total']['BTC'] if 'BTC' in balance['total'] else 0
                    
                    if current_position != 0:
                        # 反対売買で決済
                        side = -1 if current_position > 0 else 1
                        order = self.execute_trade(symbol, side, abs(self.current_position_size))
                        
                        # フラグをリセット
                        delattr(self, 'position_time')
                        delattr(self, 'current_position_size')
                        
                        return order
            return None
        except Exception as e:
            print(f"Error closing position: {e}")
            return None

    def health_check(self):
        try:
            print("Health check started...")
            # 取引所への接続確認をスキップ
            print("Exchange connection check skipped (test mode)")
            # モデルの存在確認
            if self.model is None:
                print("Model not found (test mode)")
            return True
        except Exception as e:
            print(f"Health check error: {e}")
            return False

if __name__ == "__main__":
    print("Crypto bot is starting...")
    bot = CryptoBot()
    bot.run()


