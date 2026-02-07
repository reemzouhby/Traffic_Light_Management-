
"""

This gateway:
1. Receives data from BOTH IR and Ultrasonic sensors
2. Validates data between the two sensors
3. Calculates confidence scores
4. Publishes enhanced summary with both sensor types
"""

import json
import time
import paho.mqtt.client as mqtt
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from config import (BROKER, PORT, TOPIC_LANE_1, TOPIC_LANE_2, TOPIC_RFID,
                        TOPIC_SUMMARY, PUBLISH_INTERVAL)
except ImportError:
    BROKER = "broker.hivemq.com"
    PORT = 1883
    TOPIC_LANE_1 = "traffic/lane1"
    TOPIC_LANE_2 = "traffic/lane2"
    TOPIC_RFID = "traffic/emergency"
    TOPIC_SUMMARY = "traffic/summary"
    PUBLISH_INTERVAL = 1

# Store latest sensor data
lane_data = {
    "Lane 1": {
        "IR": 0,   #0 or 1 (vehicle presence)
        "Ultrasonic": 0  # 0-20 (vehicle count)
    },
    "Lane 2": {
        "IR": 0,  #  0 or 1 (vehicle presence)
        "Ultrasonic": 0  # 0-20 (vehicle count)
    },
    "Emergency": 0,
    "Emergency_Lane": None
}

# Statistics
stats = {
    "messages_received": 0,
    "sensor_mismatches": 0,
    "data_validations": 0
}

client = mqtt.Client(client_id="smart_traffic_gateway")


def on_connect(client, userdata, flags, rc):
    """Connect to broker and subscribe to all topics"""
    if rc == 0:
        print("✅ Gateway connected to MQTT broker")
        # Subscribe to all sensor topics
        client.subscribe([(TOPIC_LANE_1, 0),
                          (TOPIC_LANE_2, 0),
                          (TOPIC_RFID, 1)])
        print(f"   Subscribed to: {TOPIC_LANE_1}")
        print(f"   Subscribed to: {TOPIC_LANE_2}")
        print(f"   Subscribed to: {TOPIC_RFID}")
    else:
        print(f"❌ Connection failed: {rc}")


def calculate_confidence_score(lane_name):
    """
    Calculate confidence in data based on IR and Ultrasonic agreement

    Returns confidence score 0-100%
    """
    ir = lane_data[lane_name]["IR"]
    us = lane_data[lane_name]["Ultrasonic"]

    # Perfect agreement: both say no vehicles
    if ir == 0 and us == 0:
        return 100  # 100% confident

    # Perfect agreement: both say yes vehicles
    elif ir == 1 and us > 0:
        return 100  # 100% confident

    # Mismatch: IR says yes, count says no
    elif ir == 1 and us == 0:
        # Could be a single vehicle at detection point
        # Confidence: medium
        return 50  # 50% confident

    # Mismatch: IR says no, count says yes
    elif ir == 0 and us > 0:
        # Could be vehicles past IR detection point
        # Confidence: high (trust ultrasonic)
        return 75  # 75% confident

    else:
        return 50  # Default


def validate_sensor_data(lane_name):
    """
    Validate IR and Ultrasonic data match
    Returns validation status and any warnings
    """
    ir = lane_data[lane_name]["IR"]
    us = lane_data[lane_name]["Ultrasonic"]
    warnings = []

    # Check for mismatches
    if ir == 1 and us == 0:
        warnings.append(f"⚠️  {lane_name}: IR detects vehicle but count=0")
        # Likely 1 vehicle at detection point

    if ir == 0 and us > 0:
        warnings.append(f"⚠️  {lane_name}: Count={us} but IR detects nothing")
        # Vehicles past detection point

    if us > 20:
        warnings.append(f"⚠️  {lane_name}: Ultrasonic count exceeds max (20)")

    return warnings


def on_message(client, userdata, msg):
    """Process incoming MQTT messages from sensors"""
    global lane_data, stats

    stats["messages_received"] += 1

    try:
        payload = json.loads(msg.payload.decode())

        # ===== UPDATE LANE 1 DATA =====
        if msg.topic == TOPIC_LANE_1:
            if payload["sensor"] == "IR":
                lane_data["Lane 1"]["IR"] = payload["vehicle_detected"]
                print(f"   📡 Lane 1 IR: {payload['vehicle_detected']}")

            elif payload["sensor"] == "Ultrasonic":
                lane_data["Lane 1"]["Ultrasonic"] = payload["vehicle_count"]
                print(f"   📊 Lane 1 Count: {payload['vehicle_count']}")


        elif msg.topic == TOPIC_LANE_2:
            if payload["sensor"] == "IR":
                lane_data["Lane 2"]["IR"] = payload["vehicle_detected"]
                print(f"   📡 Lane 2 IR: {payload['vehicle_detected']}")

            elif payload["sensor"] == "Ultrasonic":
                lane_data["Lane 2"]["Ultrasonic"] = payload["vehicle_count"]
                print(f"   📊 Lane 2 Count: {payload['vehicle_count']}")


        elif msg.topic == TOPIC_RFID:
            lane_data["Emergency"] = payload["emergency"]
            lane_data["Emergency_Lane"] = payload.get("emergency_lane")

            if payload["emergency"] == 1:
                print(f"   🚨 EMERGENCY in {payload.get('emergency_lane')}!")

    except Exception as e:
        print(f"❌ Error parsing message: {e}")


def calculate_green_light():
    """Decide which lane gets green light (preliminary decision at gateway)"""
    if lane_data["Emergency"] == 1 and lane_data["Emergency_Lane"]:
        return lane_data["Emergency_Lane"]

    if lane_data["Lane 1"]["Ultrasonic"] >= lane_data["Lane 2"]["Ultrasonic"]:
        return "Lane 1"
    else:
        return "Lane 2"


# Set callbacks
client.on_connect = on_connect
client.on_message = on_message

# Connect
try:
    client.connect(BROKER, PORT, 60)
    client.loop_start()
except Exception as e:
    print(f"❌ Failed to connect: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("🌐 SMART TRAFFIC GATEWAY STARTED")
print("=" * 70)
print("Features:")
print("  ✅ IR Sensor Integration")
print("  ✅ Ultrasonic Sensor Integration")
print("  ✅ Data Validation")
print("  ✅ Confidence Scoring")
print("  ✅ Sensor Mismatch Detection")
print("=" * 70 + "\n")

# Wait for initial connection
time.sleep(2)

# Main gateway loop
iteration = 0

while True:
    iteration += 1

    try:
        # ===== VALIDATE SENSOR DATA =====

        print(f"\n{'=' * 70}")
        print(f"📊 GATEWAY ITERATION {iteration}")
        print(f"{'=' * 70}")

        # Check Lane 1
        lane1_warnings = validate_sensor_data("Lane 1")
        if lane1_warnings:
            for warning in lane1_warnings:
                print(warning)
                stats["sensor_mismatches"] += 1
        else:
            print("✅ Lane 1: Data validated successfully")

        # Check Lane 2
        lane2_warnings = validate_sensor_data("Lane 2")
        if lane2_warnings:
            for warning in lane2_warnings:
                print(warning)
                stats["sensor_mismatches"] += 1
        else:
            print("✅ Lane 2: Data validated successfully")

        # ===== CALCULATE CONFIDENCE SCORES =====

        print(f"\n{'─' * 70}")
        print("📈 CONFIDENCE SCORES")
        print(f"{'─' * 70}")

        lane1_confidence = calculate_confidence_score("Lane 1")
        lane2_confidence = calculate_confidence_score("Lane 2")

        print(f"  Lane 1: {lane1_confidence}% confident")
        print(f"    → IR={lane_data['Lane 1']['IR']}, Count={lane_data['Lane 1']['Ultrasonic']}")

        print(f"  Lane 2: {lane2_confidence}% confident")
        print(f"    → IR={lane_data['Lane 2']['IR']}, Count={lane_data['Lane 2']['Ultrasonic']}")

        # ===== PREPARE ENHANCED SUMMARY =====

        green_light = calculate_green_light()

        summary = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),

            # IR Sensor Data (NEW)
            "lane1_ir": lane_data["Lane 1"]["IR"],
            "lane2_ir": lane_data["Lane 2"]["IR"],

            # Ultrasonic Sensor Data
            "lane1_vehicles": lane_data["Lane 1"]["Ultrasonic"],
            "lane2_vehicles": lane_data["Lane 2"]["Ultrasonic"],

            # Confidence Scores (NEW)
            "lane1_confidence": lane1_confidence,
            "lane2_confidence": lane2_confidence,
            "average_confidence": (lane1_confidence + lane2_confidence) / 2,

            # Emergency Data
            "emergency": lane_data["Emergency"],
            "emergency_lane": lane_data["Emergency_Lane"],

            # Preliminary Decision
            "green_light": green_light,


            "messages_processed": stats["messages_received"],
            "sensor_mismatches_detected": stats["sensor_mismatches"]
        }



        print(f"\n{'─' * 70}")
        print("📤 PUBLISHING SUMMARY")
        print(f"{'─' * 70}")

        result = client.publish(TOPIC_SUMMARY, json.dumps(summary), qos=1)

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"✅ Summary published successfully")
            print(f"   Green Light (preliminary): {green_light}")
            print(f"   Confidence: {summary['average_confidence']:.0f}%")
        else:
            print(f"❌ Failed to publish: {result.rc}")

        # ===== STATISTICS =====

        print(f"\n{'─' * 70}")
        print("📊 GATEWAY STATISTICS")
        print(f"{'─' * 70}")
        print(f"  Iterations: {iteration}")
        print(f"  Messages Processed: {stats['messages_received']}")
        print(f"  Sensor Mismatches Detected: {stats['sensor_mismatches']}")

        time.sleep(PUBLISH_INTERVAL)

    except KeyboardInterrupt:
        print(f"\n\n⛔ Gateway stopped by user")
        break
    except Exception as e:
        print(f"❌ Error in iteration {iteration}: {e}")
        time.sleep(PUBLISH_INTERVAL)

# Cleanup
print("\n" + "=" * 70)
print("📊 FINAL GATEWAY STATISTICS")
print("=" * 70)
print(f"Total iterations: {iteration}")
print(f"Total messages processed: {stats['messages_received']}")
print(f"Sensor mismatches detected: {stats['sensor_mismatches']}")
if stats['messages_received'] > 0:
    mismatch_rate = (stats['sensor_mismatches'] / stats['messages_received']) * 100
    print(f"Mismatch rate: {mismatch_rate:.1f}%")
print("=" * 70 + "\n")

client.loop_stop()
client.disconnect()
print("✅ Gateway disconnected\n")