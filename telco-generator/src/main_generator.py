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
                "recordOpeningTime": datetime.now(), "servedMSISDN": subscriber['msisdn'], 
                "duration": 60, "causeForRecClosing": "normalRelease", "userLocationInformation": None,
                "servedIMSI": subscriber['imsi'], "servedIMEI": None, "calledNumber": None
            }
        }
    return None

def main():
    KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL")
    if not KAFKA_BROKER_URL:
        raise ValueError("KAFKA_BROKER_URL environment variable must be set")

    partition_id = int(os.getenv("GENERATOR_PARTITION_ID", 1))
    total_partitions = int(os.getenv("TOTAL_PARTITIONS", 1))
    
    print(f"KAFKA_BROKER_URL: {KAFKA_BROKER_URL}")
    print(f"Connecting to {KAFKA_BROKER_URL} for partition {partition_id} ...")

    conf = {
        'bootstrap.servers': KAFKA_BROKER_URL,
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

    try:
        while True:
            # Check for and execute scheduled scenario events
            def delivery_report(err, msg):
                if err is not None:
                    print(f'ERROR: Message failed delivery: {err}')
                else:
                    print(f"Message delivered to topic {msg.topic()} [{msg.partition()}]")

            for event in timeline:
                if event["trigger_time"] <= current_sim_time < event["trigger_time"] + timedelta(minutes=1):
                    print(f"\n>>> [Partition {partition_id}] EXECUTING SCENARIO at {current_sim_time} <<<")
                    generated_records = event["action"](**event["params"], current_time=current_sim_time)

                    for record in generated_records:
                        producer.produce(record["topic"], value=json.dumps(record["payload"], default=str).encode('utf-8'), callback=delivery_report)
                    timeline.remove(event)

            # Generate baseline "background noise" traffic
            for subscriber in my_subscribers:
                 if not subscriber.get('is_in_special_scenario', False):
                    record = generate_baseline_traffic(subscriber)
                    if record:
                        producer.produce(record["topic"], value=json.dumps(record["payload"], default=str).encode('utf-8'), callback=delivery_report)

            producer.flush()
            print(f"[Partition {partition_id}] Simulation time: {current_sim_time}", end='\r')
            time.sleep(1)
            current_sim_time += timedelta(minutes=1 * TIME_DILATION_FACTOR)
    except KeyboardInterrupt:
        print(f"\n[Partition {partition_id}] Shutting down...")

if __name__ == "__main__":
    main()
