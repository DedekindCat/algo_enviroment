import ccxt
import polars as pl
from datetime import datetime, timedelta
import time
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import logging
import json

# ロギングの設定
log_file_path = os.path.join(os.path.dirname(__file__), '../logs/data_collector/data_collection.log')
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DataCollection')

class DataCollector:
    def __init__(self):
        load_dotenv()
        
        # データベース接続設定
        self.engine = create_engine(
            f'postgresql://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}/{os.getenv("DB_NAME")}'
        )
        
        # 取引所の設定
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'rateLimit': 1000,
            'options': {
                'defaultType': 'future'
            }
        })
        
        # 進捗状況ファイルのパス
        self.progress_file = '/app/progress/collection_progress.json'
        
    def setup_database(self):
        """データベーステーブルの作成"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS market_data (
                    timestamp TIMESTAMP PRIMARY KEY,
                    open FLOAT,
                    high FLOAT,
                    low FLOAT,
                    close FLOAT,
                    volume FLOAT
                )
            """))
    
    def load_progress(self):
        """進捗状況の読み込み"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    progress = json.load(f)
                    return datetime.fromisoformat(progress['last_date'])
            return None
        except Exception as e:
            logger.error(f"Error loading progress: {e}")
            return None
            
    def save_progress(self, current_date):
        """進捗状況の保存"""
        try:
            with open(self.progress_file, 'w') as f:
                json.dump({'last_date': current_date.isoformat()}, f)
        except Exception as e:
            logger.error(f"Error saving progress: {e}")

    def fetch_and_store_data(self, symbol='BTC/USDT', start_date=None):
        """市場データの取得とデータベースへの保存"""
        self.setup_database()
        
        # 前回の進捗状況を読み込み
        last_progress = self.load_progress()
        current_date = last_progress if last_progress else start_date or datetime(2020, 1, 1)
        end_date = datetime.now()
        
        total_records = 0
        retry_count = 0
        max_retries = 5
        
        try:
            while current_date < end_date:
                try:
                    ohlcv = self.exchange.fetch_ohlcv(
                        symbol,
                        '1m',
                        self.exchange.parse8601(current_date.isoformat()),
                        limit=1000
                    )
                    
                    if not ohlcv:
                        logger.warning(f"No data available for {current_date}")
                        current_date += timedelta(minutes=1000)
                        continue
                        
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
                    
                    # 重複を避けるためにUPSERTを使用
                    pdf = df.to_pandas()
                    pdf.to_sql('market_data', self.engine, if_exists='append', index=False, 
                            method='multi', chunksize=1000)
                    
                    total_records += len(ohlcv)
                    current_batch_end = datetime.fromtimestamp(ohlcv[-1][0]/1000)
                    
                    # 進捗状況の保存
                    self.save_progress(current_batch_end)
                    
                    logger.info(f"Saved {len(ohlcv)} records up to {current_batch_end}. Total: {total_records}")
                    print(f"Progress: {current_batch_end} / {end_date}")
                    
                    current_date = current_batch_end + timedelta(minutes=1)
                    retry_count = 0  # 成功したらリトライカウントをリセット
                    time.sleep(self.exchange.rateLimit / 1000)
                    
                except Exception as e:
                    retry_count += 1
                    wait_time = min(60 * retry_count, 3600)  # 最大1時間まで
                    
                    logger.error(f"Error fetching data for {current_date}: {e}")
                    print(f"Error: {e}")
                    print(f"Retry {retry_count}/{max_retries} after {wait_time} seconds...")
                    
                    if retry_count >= max_retries:
                        logger.error("Max retries reached, skipping to next batch")
                        current_date += timedelta(minutes=1000)
                        retry_count = 0
                    
                    time.sleep(wait_time)
                    
        except KeyboardInterrupt:
            logger.info("Data collection interrupted by user")
            print("\nData collection interrupted. Progress saved.")
        
        return total_records

if __name__ == "__main__":
    collector = DataCollector()
    start_date = collector.load_progress() or datetime(2020, 1, 1)
    print(f"Starting data collection from {start_date}")
    total_records = collector.fetch_and_store_data(start_date=start_date)
    print(f"Data collection completed. Total records saved: {total_records}")
