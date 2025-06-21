# telco-generator/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ARG CACHEBUST=1

# Copy the entire src directory
COPY ./src ./src

CMD ["python", "src/main_generator.py"]
