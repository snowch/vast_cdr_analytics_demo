# vast-db-init/setup_vast_tables.py
import os
import vastdb
import pyarrow as pa
from dotenv import load_dotenv

def main():
    """Connects to VAST DB and creates the necessary schemas and tables for the demo."""
    # Load .env from the parent directory when running this script locally
    load_dotenv(dotenv_path='../.env')
    
    VASTDB_ENDPOINT = os.getenv("VASTDB_ENDPOINT")
    VASTDB_ACCESS_KEY = os.getenv("VASTDB_ACCESS_KEY")
    VASTDB_SECRET_KEY = os.getenv("VASTDB_SECRET_KEY")

    if not all([VASTDB_ENDPOINT, VASTDB_ACCESS_KEY, VASTDB_SECRET_KEY]):
        print("Error: VAST DB environment variables not set. Check your .env file.")
        return

    # Establish a session with VAST DB
    print(f"Connecting to VAST at {VASTDB_ENDPOINT}...")
    session = vastdb.connect(
        endpoint=VASTDB_ENDPOINT,
        access=VASTDB_ACCESS_KEY,
        secret=VASTDB_SECRET_KEY
    )

    try:
        with session.transaction() as tx:
            # Using a bucket named 'telco' and schema 'demo'
            bucket_name = os.getenv("VASTDB_BUCKET")
            schema_name = os.getenv("VASTDB_SCHEMA")
            bucket = tx.bucket(bucket_name)
            schema = bucket.create_schema(schema_name, fail_if_exists=False)
            print(f"Using bucket '{bucket.name}', schema '{schema.name}'")

            # --- Define and Create Subscribers Table (Hot/Warm State) ---
            subscribers_cols = pa.schema([
                ('imsi', pa.string()), ('msisdn', pa.string()),
                ('persona', pa.string()), ('churn_risk', pa.string()),
                ('current_tower_id', pa.string()), ('is_in_special_scenario', pa.bool_()),
                ('partition_id', pa.int32())
            ])
            subscribers_table = schema.create_table("subscribers", subscribers_cols, fail_if_exists=False)
            print(f"Table '{subscribers_table.name}' is ready.")

            # --- Define and Create CDRs Table (Cold Analytics Data) ---
            cdrs_cols = pa.schema([
                ('recordOpeningTime', pa.timestamp('ns')), ('servedMSISDN', pa.string()),
                ('duration', pa.int32()), ('causeForRecClosing', pa.string()),
                ('userLocationInformation', pa.string()), ('servedIMSI', pa.string()),
                ('servedIMEI', pa.string()), ('calledNumber', pa.string())
            ])
            cdrs_table = schema.create_table("cdrs", cdrs_cols, fail_if_exists=False)
            print(f"Table '{cdrs_table.name}' is ready.")
            
            # --- Define and Create Network Logs Table ---
            network_logs_cols = pa.schema([
                ('timestamp', pa.timestamp('ns')), ('tower_id', pa.string()),
                ('log_level', pa.string()), ('message', pa.string())
            ])
            network_logs_table = schema.create_table("network_logs", network_logs_cols, fail_if_exists=False)
            print(f"Table '{network_logs_table.name}' is ready.")
            
            # --- Define and Create Customer Service Logs Table ---
            customer_service_cols = pa.schema([
                ('msisdn', pa.string()), ('call_time', pa.timestamp('ns')),
                ('duration', pa.int32()), ('call_reason', pa.string()),
                ('resolution', pa.string()), ('agent_id', pa.string())
            ])
            customer_service_table = schema.create_table("customer_service", customer_service_cols, fail_if_exists=False)
            print(f"Table '{customer_service_table.name}' is ready.")
            
            print("\nSchema setup complete. The transaction will now be committed.")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
