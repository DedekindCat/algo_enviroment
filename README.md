# algo_enviroment
## Purpose
This is a template for cryptocurrency CEX-based machine learning trading.   I hope it will be helpful for beginners in crypto trading who are unsure how to set up their environment.

これは仮想通貨のCEX型機械学習トレードのテンプレートです。
仮想通貨トレードの初心者で、環境構築方法が分からないという方の参考になれば幸いです。

## Note
現在のバージョンは未完成の機能を多く含みます
今後、バージョンアップを行い、機能を追加してい
く予定です。

## Strategy 

MLでn分後の価格を予測し、その予測価格に対してポジションを取る

データをbinanceAPIから取得しモデルを学習させる

ここではawsのEC2を使用し常時稼働させる

DBはRDSを使用

モデルの学習にはGoogle ColabのGPUを使用


## File Structure
<pre>
/
bots
├─ bot1
│  ├─ bot1.py #bot1の取引戦略
│  ├─ Dockerfile
│  ├─ requirements.text
│  ├─ simulated_exchange.py #取引所のシミュレーション
│  └─ simulation_bot.py #取引のシミュレーション
└─ bot2
data_collecor
├─ data_collector.py #データの取得
├─ Dockerfile
└─ requirements.txt
logs　#ログを管理するフォルダ
├─ bot1
├─ datacollector
└─ test
ml #モデルを管理するフォルダ
├─ notebooks #モデルの学習
│  ├─ bot1
│  │  └─ model_training_bot1.ipynb
│  └─ bot2
└─ scripts #ipynbではない部分
   ├─ bot1
   │  ├─ __init__.py
   │  ├─ features.py
   │  └─ train.py
   ├─ bot2
   └─ common
      ├─ __init__.py
      ├─ data_loader.py
      └─ feature_engineering.py
models #学習済みモデルを管理するフォルダ
├─ bot1
│  └─ model.joblib
└─ bot2
tests #テストコードを管理するフォルダ
.env #環境変数を管理するファイル
docker-compose.yml 
README.md 
</pre>
