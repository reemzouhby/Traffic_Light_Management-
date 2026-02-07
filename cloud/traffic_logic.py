# traffic_logic.py - UPDATED WITH IR INTEGRATION

import json
import time
import paho.mqtt.client as mqtt
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import BROKER, PORT, TOPIC_SUMMARY, PUBLISH_INTERVAL, GREEN_MIN, GREEN_MAX

# Store latest summary
latest_summary = {
    "lane1_vehicles": 0,
    "lane1_ir": 0,  # IR data
    "lane2_vehicles": 0,
    "lane2_ir": 0,  #  IR data
    "emergency": 0,
    "emergency_lane": None,
    "green_light": "Lane 1",
    "green_duration": GREEN_MIN
}


def on_connect(client, userdata, flags, rc):
    print("✅ Connected to MQTT broker (Cloud logic)")
    client.subscribe(TOPIC_SUMMARY)


def on_message(client, userdata, msg):
    global latest_summary
    payload = json.loads(msg.payload.decode())
    latest_summary.update(payload)

    if payload.get("emergency") == 1:
        print(f"🚨 EMERGENCY ALERT: {payload.get('emergency_lane')} has emergency vehicle!")


# NEW: Calculate confidence score
def calculate_confidence_score(lane_name):
    """
    Calculate confidence in data based on IR and ultrasonic agreement
    Returns: 0.5 to 1.0 (50% to 100%)
    """
    if lane_name == "Lane 1":
        ir = latest_summary.get("lane1_ir", 0)
        count = latest_summary["lane1_vehicles"]
    else:
        ir = latest_summary.get("lane2_ir", 0)
        count = latest_summary["lane2_vehicles"]

    # Perfect agreement cases
    if ir == 0 and count == 0:
        return 1.0  # 100% confident: both say no vehicles
    elif ir == 1 and count > 0:
        return 1.0  # 100% confident: both say yes vehicles
    # Disagreement cases
    elif ir == 1 and count == 0:
        return 0.5  # 50% confident: IR says yes, count says no
    else:  # ir == 0 and count > 0
        return 0.75  # 75% confident: vehicles past IR point


def decide_green_light():
    """
    Decide which lane gets green light
    WITH IR validation
    """
    emergency = latest_summary["emergency"]
    emergency_lane = latest_summary["emergency_lane"]
    lane1_count = latest_summary["lane1_vehicles"]
    lane2_count = latest_summary["lane2_vehicles"]

    # If emergency, give green to that lane
    if emergency == 1 and emergency_lane:
        return emergency_lane

    # Otherwise, green to lane with more vehicles
    if lane1_count >= lane2_count:
        return "Lane 1"
    else:
        return "Lane 2"


def calculate_green_duration():

    lane = latest_summary["green_light"]
    lane1_count = latest_summary["lane1_vehicles"]
    lane2_count = latest_summary["lane2_vehicles"]

    emergency = latest_summary["emergency"]
    emergency_lane = latest_summary.get("emergency_lane")

    # Emergency gets MAXIMUM duration
    if emergency == 1 and emergency_lane == lane:
        return GREEN_MAX

    # Get IR data for validation
    if lane == "Lane 1":
        lane_ir = latest_summary.get("lane1_ir", 1)
        current_count = lane1_count
    else:
        lane_ir = latest_summary.get("lane2_ir", 1)
        current_count = lane2_count

    # Check if IR and ultrasonic agree
    if lane_ir == 1 and current_count == 0:
        # IR detected vehicle but count is 0
        # Adjust: assume at least 1 vehicle
        print(f"⚠️  {lane}: IR detected, adjusting count from 0 to 1")
        current_count = 1
    elif lane_ir == 0 and current_count > 0:
        # Count says vehicles but IR detects nothing
        # These are vehicles past IR detection point - trust ultrasonic
        print(f"⚠️  {lane}: Vehicles past IR detection, trusting count")
        # Keep current_count as is

    # Calculate base duration
    total_vehicles = lane1_count + lane2_count

    if total_vehicles == 0:
        return GREEN_MIN

    congestion_ratio = current_count / max(total_vehicles, 1)

    #  confidence score for this lane
    confidence = calculate_confidence_score(lane)

    # Base duration
    base_duration = GREEN_MIN + int(congestion_ratio * (GREEN_MAX - GREEN_MIN))

    # Apply confidence adjustment
    # Low confidence → slightly reduce duration (be conservative)
    # High confidence → use full calculated duration
    adjusted_duration = int(base_duration * confidence)


    adjusted_duration = max(GREEN_MIN, min(GREEN_MAX, adjusted_duration))

    return adjusted_duration


# MQTT setup
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.loop_start()

print("\n" + "=" * 70)
print("🚦 CLOUD TRAFFIC LOGIC STARTED")
print("=" * 70)
print("Features:")
print("  ✅ Emergency vehicle priority")
print("  ✅ Congestion-based duration")
print("  ✅ IR SENSOR VALIDATION")
print("  ✅ Confidence scoring")
print("=" * 70 + "\n")

iteration = 0

while True:
    iteration += 1

    # Calculate with IR validation
    green_light = decide_green_light()
    green_duration = calculate_green_duration()

    # Calculate confidence for display
    lane1_confidence = calculate_confidence_score("Lane 1")
    lane2_confidence = calculate_confidence_score("Lane 2")

    latest_summary["green_light"] = green_light
    latest_summary["green_duration"] = green_duration

    # Print detailed status
    print(f"\n{'=' * 70}")
    print(f"[ITERATION {iteration}] Traffic Light Control")
    print(f"{'=' * 70}")

    print(f"\n📊 LANE STATUS:")
    print(
        f"  Lane 1: IR={latest_summary.get('lane1_ir', 0)}, Count={latest_summary['lane1_vehicles']}, Confidence={lane1_confidence * 100:.0f}%")
    print(
        f"  Lane 2: IR={latest_summary.get('lane2_ir', 0)}, Count={latest_summary['lane2_vehicles']}, Confidence={lane2_confidence * 100:.0f}%")

    if latest_summary["emergency"] == 1:
        print(f"\n🚨 EMERGENCY: {latest_summary['emergency_lane']}")

    print(f"\n✅ DECISION:")
    print(f"  Green Light: {green_light}")
    print(f"  Duration: {green_duration}s (min: {GREEN_MIN}s, max: {GREEN_MAX}s)")
    print(f"  Confidence: {((lane1_confidence + lane2_confidence) / 2) * 100:.0f}%")

    # Publish
    client.publish(TOPIC_SUMMARY, json.dumps(latest_summary))
    print(f"\n📤 Published to MQTT")

    time.sleep(PUBLISH_INTERVAL)