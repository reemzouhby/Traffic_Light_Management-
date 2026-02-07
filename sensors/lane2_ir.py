
import random
import time
import json
import paho.mqtt.client as mqtt
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import BROKER, PORT, TOPIC_LANE_2, PUBLISH_INTERVAL

# MQTT Setup
client = mqtt.Client()
client.connect(BROKER, PORT, 60)
client.loop_start()

print("Lane 2 IR sensor simulation started...")

# Simulation Loop
while True:
    #  0 = no vehicle, 1 = vehicle detected
    vehicle_detected = random.choice([0, 1])

    # Prepare JSON payload
    data = {
        "lane": "Lane 2",
        "sensor": "IR",
        "vehicle_detected": vehicle_detected
    }

    # Publish to MQTT
    client.publish(TOPIC_LANE_2, json.dumps(data))
    print(f"Published to {TOPIC_LANE_2}: {data}")

    time.sleep(PUBLISH_INTERVAL)
