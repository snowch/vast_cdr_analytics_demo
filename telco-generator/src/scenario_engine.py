# telco-generator/src/scenario_engine.py
from datetime import timedelta
import patterns
from config import SIMULATION_START_TIME

def get_scenario_timeline(all_my_subscribers, my_partition_id):
    """Defines the master timeline of all scheduled story events for this partition."""
    if not all_my_subscribers:
        return []

    # Make scenarios deterministic based on partition ID to avoid collisions
    churn_candidate = all_my_subscribers[0]
    busy_tower_id = f"TOWER_{(10 + my_partition_id):04d}"
    fraud_ring_imsis = [sub['imsi'] for sub in all_my_subscribers[1:6]]
    
    for sub in all_my_subscribers:
        if sub['imsi'] == churn_candidate['imsi'] or sub['imsi'] in fraud_ring_imsis:
            sub['is_in_special_scenario'] = True

    timeline = [
        {
            "trigger_time": SIMULATION_START_TIME + timedelta(hours=2),
            "action": patterns.generate_churn_warning_pattern,
            "params": {"subscriber": churn_candidate}
        },
        {
            "trigger_time": SIMULATION_START_TIME + timedelta(hours=4, minutes=30),
            "action": patterns.generate_network_congestion_pattern,
            "params": {
                "tower_id": busy_tower_id,
                "subscribers_on_tower": [s for s in all_my_subscribers if s['current_tower_id'] == busy_tower_id]
            }
        },
        {
            "trigger_time": SIMULATION_START_TIME + timedelta(hours=6),
            "action": patterns.generate_sim_box_fraud_pattern,
            "params": {
                "fraud_imsi_list": fraud_ring_imsis,
                "tower_id": f"TOWER_{(20 + my_partition_id):04d}"
            }
        }
    ]
    return timeline
