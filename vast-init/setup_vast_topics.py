import os
from confluent_kafka import Producer, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic
import json

def main():
    """
    Connects to Kafka and creates the necessary topics for the demo.
    """

    KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL")
    if not KAFKA_BROKER_URL:
        raise ValueError("Error: Kafka Broker URL not set. Check your .env file.")

    try:
        # Establish a connection to Kafka
        print(f"Connecting to Kafka at {KAFKA_BROKER_URL}...")
        admin_client_conf = {
            'bootstrap.servers': KAFKA_BROKER_URL
        }
        admin_client = AdminClient(admin_client_conf)

        # Define the topics to create from .env
        topics_to_create = []
        topic_cdrs = os.getenv("KAFKA_TOPIC_CDRS")
        if not topic_cdrs:
            raise ValueError("Error: KAFKA_TOPIC_CDRS not set in .env file.")
        topics_to_create.append(topic_cdrs)

        topic_network_logs = os.getenv("KAFKA_TOPIC_NETWORK_LOGS")
        if not topic_network_logs:
            raise ValueError("Error: KAFKA_TOPIC_NETWORK_LOGS not set in .env file.")
        topics_to_create.append(topic_network_logs)

        topic_customer_service = os.getenv("KAFKA_TOPIC_CUSTOMER_SERVICE")
        if not topic_customer_service:
            raise ValueError("Error: KAFKA_TOPIC_CUSTOMER_SERVICE not set in .env file.")
        topics_to_create.append(topic_customer_service)

        # List existing topics
        existing_topics = admin_client.list_topics().topics
        print(f"Existing topics: {existing_topics.keys()}")

        new_topics = [NewTopic(topic, num_partitions=1, replication_factor=1)
                      for topic in topics_to_create if topic not in existing_topics]

        # Create topics that don't exist
        if new_topics:
            print(f"Creating topics: {[topic.topic for topic in new_topics]}")
            fs = admin_client.create_topics(new_topics)

            for topic, f in fs.items():
                try:
                    f.result()  # The result itself is None
                    print(f"Topic {topic} created")
                except Exception as e:
                    print(f"Failed to create topic {topic}: {e}")
                    raise e
        else:
            print("All topics exist.")

        print("\nTopic setup complete.")

    except Exception as e:
        print(f"An error occurred: {e}")
        raise e

if __name__ == "__main__":
    main()
