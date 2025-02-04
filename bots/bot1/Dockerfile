# ベースイメージにPythonを使用
FROM python:3.9

# 作業ディレクトリを設定
WORKDIR /app

# 必要なファイルをコンテナにコピー
COPY requirements.txt .
COPY data_collector.py .
COPY .env .

# Pythonライブラリをインストール
RUN pip install --no-cache-dir -r requirements.txt

# コンテナ起動時に実行するコマンド
CMD ["python", "data_collector.py"]
