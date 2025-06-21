FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ARG CACHEBUST=1

COPY . .

CMD ["bash", "-c", "python setup_vast_topics.py && python setup_vast_tables.py"]
