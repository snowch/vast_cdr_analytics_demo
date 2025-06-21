# vast-db-connector/src/connector.py
import os
import json
import time
import vastdb
import pyarrow as pa
from kafka import KafkaConsumer
from datetime import datetime

# Define the Arrow schemas for our Kafka topics. This must match the VAST DB table schema.
ARROW_SCHEMAS = {
    "cdrs": pa.schema([
        ('recordOpeningTime', pa.timestamp('ns')), ('servedMSISDN', pa.string()),
        ('duration', pa.int32()), ('causeForRecClosing', pa.string()),
        ('userLocationInformation', pa.string()), ('servedIMSI', pa.string()),
        ('servedIMEI', pa.string()), ('calledNumber', pa.string())
    ]),
    "network_logs": pa.schema([
        ('timestamp', pa.timestamp('ns')), ('tower_id', pa.string()),
        ('log_level', pa.string()), ('message', pa.string())
    ]),
    "customer_service": pa.schema([
        ('msisdn', pa.string()), ('call_time', pa.timestamp('ns')),
        ('duration', pa.int32()), ('call_reason', pa.string()),
        ('resolution', pa.string()), ('agent_id', pa.string())
    ])
}

def write_batch_to_vast(session, topic, batch):
    """Converts a batch of JSON messages to an Arrow Table and inserts into VAST DB."""
    if not batch:
        return
        
    print(f"Preparing batch of {len(batch)} records for topic '{topic}'...")
    try:
        schema = ARROW_SCHEMAS.get(topic)
        if not schema:
            print(f"WARN: No Arrow schema defined for topic '{topic}'. Skipping.")
            return

        # Convert string timestamps to datetime objects for PyArrow
        for record in batch:
            for field in schema:
                if pa.types.is_timestamp(field.type) and isinstance(record.get(field.name), str):
                    try:
                        record[field.name] = datetime.fromisoformat(record[field.name].replace('Z', '+00:00'))
                    except:
                        record[field.name] = None # Handle potential parsing errors

        arrow_table = pa.Table.from_pylist(batch, schema=schema)

        with session.transaction() as tx:
            bucket_name = os.getenv("VASTDB_BUCKET")
            schema_name = os.getenv("VASTDB_SCHEMA")
            table = tx.bucket(bucket_name).schema(schema_name).table(topic)
            table.insert(arrow_table)
        print(f"Successfully inserted batch of {len(batch)} records into table '{topic}'.")

    except Exception as e:
        print(f"ERROR writing batch to VAST DB for topic '{topic}': {e}")


def main():
    KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL")
    KAFKA_TOPICS = os.getenv("KAFKA_TOPICS", "cdrs,network_logs,customer_service").split(',')
    BATCH_SIZE = 1000
    BATCH_TIMEOUT_S = 5

    session = vastdb.connect(
        endpoint=os.getenv("VASTDB_ENDPOINT"),
        access=os.getenv("VASTDB_ACCESS_KEY"),
        secret=os.getenv("VASTDB_SECRET_KEY")
    )
    consumer = KafkaConsumer(
        *KAFKA_TOPICS,
        bootstrap_servers=KAFKA_BROKER_URL,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id="vast-db-connector-group-1",
        auto_offset_reset='earliest'
    )
    print(f"Connector initialized. Consuming from topics: {KAFKA_TOPICS}")
    
    message_batch = {topic: [] for topic in KAFKA_TOPICS}
    last_write_time = {topic: time.time() for topic in KAFKA_TOPICS}

    try:
        for message in consumer:
            topic = message.topic
            if topic in message_batch:
                message_batch[topic].append(message.value)
                time_since_last_write = time.time() - last_write_time[topic]

                if len(message_batch[topic]) >= BATCH_SIZE or time_since_last_write > BATCH_TIMEOUT_S:
                    write_batch_to_vast(session, topic, message_batch[topic])
                    message_batch[topic] = []
                    last_write_time[topic] = time.time()

    except KeyboardInterrupt:
        print("Shutdown signal received. Writing any remaining batches...")
        for topic, batch in message_batch.items():
            write_batch_to_vast(session, topic, batch)
    finally:
        session.close()
        consumer.close()
        print("Connector shut down gracefully.")

if __name__ == "__main__":
    main()
