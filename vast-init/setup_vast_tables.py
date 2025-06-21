# vast-init/setup_vast_tables.py
import os
import vastdb
import pyarrow as pa

def main():
    """Connects to VAST DB and creates the necessary schemas and tables for the demo."""
    
    VASTDB_ENDPOINT = os.getenv("VASTDB_ENDPOINT")
    VASTDB_ACCESS_KEY = os.getenv("VASTDB_ACCESS_KEY")
    VASTDB_SECRET_KEY = os.getenv("VASTDB_SECRET_KEY")
    VASTDB_BUCKET = os.getenv("VASTDB_BUCKET")
    VASTDB_SCHEMA = os.getenv("VASTDB_SCHEMA")

    if not all([VASTDB_ENDPOINT, VASTDB_ACCESS_KEY, VASTDB_SECRET_KEY, VASTDB_BUCKET, VASTDB_SCHEMA]):
        raise ValueError("Error: VAST DB environment variables not set. Check your .env file.")

    # Establish a session with VAST DB
    print(f"Connecting to VAST at {VASTDB_ENDPOINT}...")
    try:
        session = vastdb.connect(
            endpoint=VASTDB_ENDPOINT,
            access=VASTDB_ACCESS_KEY,
            secret=VASTDB_SECRET_KEY,
            timeout=30  # Add a timeout to prevent hanging
        )

        try:
            with session.transaction() as tx:
                # Using a bucket named 'telco' and schema 'demo'
                bucket_name = os.getenv("VASTDB_BUCKET")
                schema_name = os.getenv("VASTDB_SCHEMA")

                bucket = tx.bucket(bucket_name)
                schema = bucket.schema(schema_name, fail_if_missing=False)
                if not schema:
                    print(f"Schema '{schema_name}' not found, creating...")
                    bucket.create_schema(schema_name)
                
                print(f"Using bucket '{bucket.name}', schema '{schema.name}'")

                # --- Define expected schemas ---
                subscribers_schema = pa.schema([
                    ('imsi', pa.string()), ('msisdn', pa.string()),
                    ('persona', pa.string()), ('churn_risk', pa.string()),
                    ('current_tower_id', pa.string()), ('is_in_special_scenario', pa.bool_()),
                    ('partition_id', pa.int32())
                ])
                cdrs_schema = pa.schema([
                    ('recordOpeningTime', pa.timestamp('ns')), ('servedMSISDN', pa.string()),
                    ('duration', pa.int32()), ('causeForRecClosing', pa.string()),
                    ('userLocationInformation', pa.string()), ('servedIMSI', pa.string()),
                    ('servedIMEI', pa.string()), ('calledNumber', pa.string())
                ])
                network_logs_schema = pa.schema([
                    ('timestamp', pa.timestamp('ns')), ('tower_id', pa.string()),
                    ('log_level', pa.string()), ('message', pa.string())
                ])
                customer_service_schema = pa.schema([
                    ('msisdn', pa.string()), ('call_time', pa.timestamp('ns')),
                    ('duration', pa.int32()), ('call_reason', pa.string()),
                    ('resolution', pa.string()), ('agent_id', pa.string())
                ])

                # --- Verify tables and schemas ---
                subscribers_table = schema.table("subscribers", fail_if_missing=False)
                if not subscribers_table:
                    print(f"Table 'subscribers' not found, creating...")
                    subscribers_table = schema.create_table("subscribers", subscribers_schema)
                    print(f"Table '{subscribers_table.name}' created.")
                elif subscribers_table.arrow_schema != subscribers_schema:
                    raise ValueError("Subscribers table has incorrect schema.")
                else:
                    print(f"Table '{subscribers_table.name}' is ready.")

                cdrs_table = schema.table("cdrs", fail_if_missing=False)
                if not cdrs_table:
                    print(f"Table 'cdrs' not found, creating...")
                    cdrs_table = schema.create_table("cdrs", cdrs_schema)
                    print(f"Table '{cdrs_table.name}' created.")
                elif cdrs_table.arrow_schema != cdrs_schema:
                    raise ValueError("CDRs table has incorrect schema.")
                else:
                    print(f"Table '{cdrs_table.name}' is ready.")

                network_logs_table = schema.table("network_logs", fail_if_missing=False)
                if not network_logs_table:
                    print(f"Table 'network_logs' not found, creating...")
                    network_logs_table = schema.create_table("network_logs", network_logs_schema)
                    print(f"Table '{network_logs_table.name}' created.")
                elif network_logs_table.arrow_schema != network_logs_schema:
                    raise ValueError("Network logs table has incorrect schema.")
                else:
                    print(f"Table '{network_logs_table.name}' is ready.")

                customer_service_table = schema.table("customer_service", fail_if_missing=False)
                if not customer_service_table:
                    print(f"Table 'customer_service' not found, creating...")
                    customer_service_table = schema.create_table("customer_service", customer_service_schema)
                    print(f"Table '{customer_service_table.name}' created.")
                elif customer_service_table.arrow_schema != customer_service_schema:
                    raise ValueError("Customer service table has incorrect schema.")
                else:
                    print(f"Table '{customer_service_table.name}' is ready.")

                print("\nSchema setup complete. Verification successful.")

        except Exception as e:
            print(f"An error occurred during transaction: {e}")
            raise e
    except Exception as e:
        print(f"An error occurred during VAST connection: {e}")
        raise e

if __name__ == "__main__":
    print("Starting VAST DB setup...")
    main()
