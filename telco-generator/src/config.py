# telco-generator/src/config.py
from datetime import datetime

# --- Simulation Configuration ---
SIMULATION_START_TIME = datetime(2025, 6, 19, 12, 0, 0)
TIME_DILATION_FACTOR = 60  # 1 real-world second = 1 minute simulation time
TOTAL_SUBSCRIBERS = 10000
TOTAL_CELL_TOWERS = 100

# --- Subscriber Personas ---
# Defines baseline behavior for generating "normal" traffic
PERSONAS = {
    "student": {"data_usage_gb_monthly": 50, "sms_monthly": 100, "voice_mins_monthly": 200},
    "business_traveler": {"data_usage_gb_monthly": 25, "sms_monthly": 50, "voice_mins_monthly": 1500},
    "gamer": {"data_usage_gb_monthly": 200, "sms_monthly": 30, "voice_mins_monthly": 100},
    "iot_device": {"data_usage_gb_monthly": 1, "sms_monthly": 0, "voice_mins_monthly": 0}
}

# --- Use Case Specific Constants ---
COMPETITOR_PHONE_NUMBER = "447700900999" # A number to call when simulating churn
