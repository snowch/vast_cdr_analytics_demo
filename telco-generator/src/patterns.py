# telco-generator/src/patterns.py
import random
import os
from datetime import timedelta
from config import COMPETITOR_PHONE_NUMBER

def generate_churn_warning_pattern(subscriber, current_time):
    """Generates data for a subscriber who is likely to churn."""
    print(f"PATTERN: Generating CHURN pattern for {subscriber['msisdn']}")
    events = []

    events.append({
        "topic": os.getenv("KAFKA_TOPIC_CUSTOMER_SERVICE"),
        "payload": {
            "msisdn": subscriber["msisdn"], "call_time": current_time,
            "duration": random.randint(120, 600), "call_reason": "BILLING_DISPUTE",
            "resolution": "UNRESOLVED_ESCALATED", "agent_id": f"agent_{random.randint(100,199)}"
        }
    })

    call_to_competitor_time = current_time + timedelta(hours=3)
    events.append({
        "topic": os.getenv("KAFKA_TOPIC_CDRS"),
        "payload": {
            "recordOpeningTime": call_to_competitor_time, "servedMSISDN": subscriber["msisdn"],
            "callingNumber": subscriber["msisdn"], "calledNumber": COMPETITOR_PHONE_NUMBER,
            "duration": random.randint(180, 900), "causeForRecClosing": "normalRelease",
            "servedIMSI": subscriber["imsi"], "servedIMEI": None, "userLocationInformation": None
        }
    })
    return events

def generate_network_congestion_pattern(tower_id, subscribers_on_tower, current_time):
    """Generates data for a network cell tower under heavy load."""
    print(f"PATTERN: Generating NETWORK CONGESTION for {tower_id}")
    events = []

    events.append({
        "topic": os.getenv("KAFKA_TOPIC_NETWORK_LOGS"),
        "payload": {
            "timestamp": current_time, "tower_id": tower_id,
            "log_level": "WARNING", "message": f"CPU load at 95%. User capacity nearing maximum."
        }
    })

    for sub in subscribers_on_tower:
        if random.random() < 0.1:
            events.append({
                "topic": os.getenv("KAFKA_TOPIC_CDRS"),
                "payload": {
                    "recordOpeningTime": (current_time + timedelta(minutes=random.randint(1,5))),
                    "servedMSISDN": sub["msisdn"], "duration": random.randint(10, 60),
                    "causeForRecClosing": "networkCongestion", "userLocationInformation": f"TAC:{tower_id}",
                    "servedIMSI": sub["imsi"], "servedIMEI": None, "calledNumber": None
                }
            })
    return events

def generate_sim_box_fraud_pattern(fraud_imsi_list, tower_id, current_time):
    """Generates data for SIM Box fraud."""
    print(f"PATTERN: Generating SIM BOX FRAUD from {tower_id}")
    events = []
    shared_imei = f"IMEI_FRAUD_{random.randint(10000, 99999)}"
    
    for imsi in fraud_imsi_list:
        for i in range(5):
            events.append({
                "topic": os.getenv("KAFKA_TOPIC_CDRS"),
                "payload": {
                    "recordOpeningTime": (current_time + timedelta(seconds=i*15)),
                    "servedIMSI": imsi, "servedIMEI": shared_imei,
                    "duration": random.randint(5, 20),
                    "calledNumber": f"+{random.randint(1,200)}{random.randint(10**9, 9*10**9)}",
                    "userLocationInformation": f"TAC:{tower_id}", "causeForRecClosing": "normalRelease",
                    "servedMSISDN": None
                }
            })
    return events
