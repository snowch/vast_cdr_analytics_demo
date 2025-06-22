# telco-generator/src/main_generator.py
import os
import time
import json
import random
from datetime import datetime, timedelta
from confluent_kafka import Producer
from state_manager import StateManager
from scenario_engine import get_scenario_timeline
from config import SIMULATION_START_TIME, TIME_DILATION_FACTOR


def generate_baseline_traffic(subscriber):
    """Generates normal, everyday traffic based on persona. (Simplified)"""
    if random.random() < 0.01:
        return {
            "topic": os.getenv("KAFKA_TOPIC_CDRS"),
            "payload": {
                "recordOpeningTime": datetime.now(), 
                "servedMSISDN": subscriber['msisdn'], 
                "duration": 60, 
                "causeForRecClosing": "normalRelease", 
                "userLocationInformation": None,
                "servedIMSI": subscriber['imsi'], 
                "servedIMEI": None, 
                "calledNumber": None
            }
        }
    return None

def main():
    KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL")
    if not KAFKA_BROKER_URL:
        raise ValueError("KAFKA_BROKER_URL environment variable must be set")

    partition_id = int(os.getenv("GENERATOR_PARTITION_ID", 1))
    total_partitions = int(os.getenv("TOTAL_PARTITIONS", 1))
    
    # Batching configuration
    BATCH_SIZE = int(os.getenv("KAFKA_BATCH_SIZE", 100))  # Messages per batch
    BATCH_TIMEOUT = float(os.getenv("KAFKA_BATCH_TIMEOUT", 5.0))  # Seconds to wait before flushing
    
    print(f"KAFKA_BROKER_URL: {KAFKA_BROKER_URL}")
    print(f"Batch size: {BATCH_SIZE}, Batch timeout: {BATCH_TIMEOUT}s")
    print(f"Connecting to {KAFKA_BROKER_URL} for partition {partition_id} ...")

    conf = {
        'bootstrap.servers': KAFKA_BROKER_URL,
        'batch.size': 65536,  # Kafka producer batch size in bytes
        'linger.ms': 100,     # Wait up to 100ms to batch messages
        'compression.type': 'snappy',  # Compress batches
        'request.timeout.ms': 30000,  # 30 second timeout for requests
        'delivery.timeout.ms': 60000,  # 60 second total delivery timeout
        'retry.backoff.ms': 1000,  # 1 second backoff between retries
        'retries': 5,  # Retry up to 5 times
        'enable.idempotence': False,  # Ensure exactly-once semantics
        'max.in.flight.requests.per.connection': 1,  # For ordered delivery
        'socket.timeout.ms': 10000,  # 10 second socket timeout
        'metadata.max.age.ms': 300000,  # Refresh metadata every 5 minutes
        'reconnect.backoff.ms': 50,  # Start with 50ms reconnect backoff
        'reconnect.backoff.max.ms': 1000,  # Max 1 second reconnect backoff
    }
    producer = Producer(conf)
    state = StateManager(partition_id=partition_id, total_partitions=total_partitions)

    print(f"Kafka Producer connected to {KAFKA_BROKER_URL} for partition {partition_id}.")
    
    if partition_id == 1:
        state.populate_initial_state()
        time.sleep(5) # Give replica 1 a head start to populate

    my_subscribers = state.get_my_subscribers()
    timeline = get_scenario_timeline(my_subscribers, partition_id)
    current_sim_time = SIMULATION_START_TIME
    
    print(f"--- [Partition {partition_id}] Starting Simulation at {current_sim_time} for {len(my_subscribers)} subscribers ---")

    messages_delivered = 0
    batch_count = 0
    last_flush_time = time.time()

    def delivery_report(err, msg):
        nonlocal messages_delivered
        if err is not None:
            print(f'ERROR: Message failed delivery: {err}')
        else:
            messages_delivered += 1

    try:
        while True:
            current_batch_size = 0
            
            # Check for and execute scheduled scenario events
            for event in timeline:
                if event["trigger_time"] <= current_sim_time < event["trigger_time"] + timedelta(minutes=1):
                    print(f"\n>>> [Partition {partition_id}] EXECUTING SCENARIO at {current_sim_time} <<<")
                    generated_records = event["action"](**event["params"], current_time=current_sim_time)

                    for record in generated_records:
                        payload = json.dumps(record["payload"], default=str).encode('utf-8')
                        producer.produce(record["topic"], value=payload, callback=delivery_report)
                        current_batch_size += 1
                    timeline.remove(event)

            # Generate baseline "background noise" traffic
            for subscriber in my_subscribers:
                 if not subscriber.get('is_in_special_scenario', False):
                    record = generate_baseline_traffic(subscriber)
                    if record:
                        payload = json.dumps(record["payload"], default=str).encode('utf-8')
                        producer.produce(record["topic"], value=payload, callback=delivery_report)
                        current_batch_size += 1

            # Flush based on batch size or timeout
            current_time = time.time()
            should_flush = (
                current_batch_size >= BATCH_SIZE or 
                (current_batch_size > 0 and (current_time - last_flush_time) >= BATCH_TIMEOUT)
            )
            
            if should_flush:
                producer.flush()
                batch_count += 1
                last_flush_time = current_time
                print(f"\n[Partition {partition_id}] Batch #{batch_count} flushed: {current_batch_size} messages. Total delivered: {messages_delivered}")

            print(f"[Partition {partition_id}] Simulation time: {current_sim_time}", end='\r')
            time.sleep(1)
            current_sim_time += timedelta(minutes=1 * TIME_DILATION_FACTOR)
    except KeyboardInterrupt:
        print(f"\n[Partition {partition_id}] Shutting down...")

if __name__ == "__main__":
    main()
