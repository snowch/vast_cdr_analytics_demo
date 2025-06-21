# telco-generator/src/state_manager.py
import os
import random
import vastdb
import pyarrow as pa
import numpy as np
from ibis import _
from config import TOTAL_SUBSCRIBERS, PERSONAS, TOTAL_CELL_TOWERS

class StateManager:
    """Manages state by directly interacting with VAST DB for its assigned partition."""
    def __init__(self, partition_id, total_partitions):
        self.partition_id = int(partition_id)
        self.total_partitions = int(total_partitions)
        
        self.session = vastdb.connect(
            endpoint=os.getenv("VASTDB_ENDPOINT"),
            access=os.getenv("VASTDB_ACCESS_KEY"),
            secret=os.getenv("VASTDB_SECRET_KEY")
        )
        print(f"[Partition {self.partition_id}] StateManager connected to VAST DB.")

    def get_my_subscribers(self):
        """Fetches subscriber profiles for this partition and returns them as a list of dicts."""
        print(f"[Partition {self.partition_id}] Fetching assigned subscribers...")
        with self.session.transaction() as tx:
            bucket_name = os.getenv("VASTDB_BUCKET")
            schema_name = os.getenv("VASTDB_SCHEMA")
            table = tx.bucket(bucket_name).schema(schema_name).table("subscribers")
            try:
                reader = table.select(predicate=(_.partition_id == self.partition_id))
                arrow_table = reader.read_all()
                return arrow_table.to_pylist()
            except Exception as e:
                print(f"Error fetching subscribers: {e}")
                return []


    def update_subscriber_location(self, imsi, new_tower_id):
        """
        Updates a subscriber's location (HOT STATE UPDATE).
        NOTE: This performs a DELETE and INSERT as a workaround for a direct UPDATE.
        """
        print(f"[Partition {self.partition_id}] Updating location for {imsi} to {new_tower_id}")
        try:
            with self.session.transaction() as tx:
                bucket_name = os.getenv("VASTDB_BUCKET")
                schema_name = os.getenv("VASTDB_SCHEMA")
                table = tx.bucket(bucket_name).schema(schema_name).table("subscribers")
                
                reader = table.select(predicate=(_.imsi == imsi))
                old_record_table = reader.read_all()
                if old_record_table.num_rows == 0:
                    print(f"WARN: IMSI {imsi} not found for update.")
                    return

                # NOTE: Assuming a 'delete' method exists with a predicate.
                # This is a critical assumption for this hot-state update pattern.
                table.delete(predicate=(_.imsi == imsi))

                record_dict = old_record_table.to_pylist()[0]
                record_dict['current_tower_id'] = new_tower_id
                
                new_record_arrow_table = pa.Table.from_pylist([record_dict], schema=old_record_table.schema)
                table.insert(new_record_arrow_table)
        except Exception as e:
            print(f"ERROR updating subscriber {imsi}: {e}")

    def populate_initial_state(self):
        """Populates VAST DB with the initial set of subscribers for this partition."""
        with self.session.transaction() as tx:
            bucket_name = os.getenv("VASTDB_BUCKET")
            schema_name = os.getenv("VASTDB_SCHEMA")
            table = tx.bucket(bucket_name).schema(schema_name).table("subscribers")
            
            reader = table.select(columns=['imsi'], predicate=(_.partition_id == self.partition_id), limit_rows=1)
            if reader.read_all().num_rows > 0:
                print(f"[Partition {self.partition_id}] Subscribers already exist. Skipping population.")
                return

            print(f"[Partition {self.partition_id}] Generating initial state...")
            subscribers_to_insert = []
            for i in range(TOTAL_SUBSCRIBERS):
                if (i % self.total_partitions) + 1 == self.partition_id:
                    subscribers_to_insert.append({
                        "imsi": f"IMSI_{i:06d}",
                        "msisdn": f"447911{random.randint(100000, 999999)}",
                        "persona": random.choice(list(PERSONAS.keys())),
                        "churn_risk": "LOW",
                        "current_tower_id": f"TOWER_{random.randint(0, TOTAL_CELL_TOWERS-1):04d}",
                        "is_in_special_scenario": False,
                        "partition_id": self.partition_id
                    })
            
            if not subscribers_to_insert:
                return
            # Convert partition_id to int32
            for subscriber in subscribers_to_insert:
                subscriber['partition_id'] = np.int32(subscriber['partition_id'])
            arrow_table = pa.Table.from_pylist(subscribers_to_insert)

            print(f"arrow_table schema: {arrow_table.schema}")
            table_schema = table.arrow_schema
            print("table schema:", table_schema)

            table.insert(arrow_table)
            print(f"[Partition {self.partition_id}] Inserted {len(subscribers_to_insert)} subscribers into VAST DB.")

    def close_session(self):
        # no close session operation for vastdb
        pass
