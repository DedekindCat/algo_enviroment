FROM python:3.9

WORKDIR /app

# 進捗状況保存用のディレクトリを作成
RUN mkdir -p /app/progress

COPY requirements.txt .
COPY data_collector.py .
COPY .env .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "data_collector.py"]
