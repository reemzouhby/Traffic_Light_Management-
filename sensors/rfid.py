# rfid.py - FIXED VERSION

import random
import time
import json
import paho.mqtt.client as mqtt
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import BROKER, PORT, TOPIC_RFID, PUBLISH_INTERVAL, EMERGENCY_PROBABILITY

# MQTT Setup
client = mqtt.Client()
client.connect(BROKER, PORT, 60)
client.loop_start()

print("RFID Emergency sensor simulation started...")

# Simulation Loop
while True:

    emergency = 1 if random.random() < EMERGENCY_PROBABILITY else 0
    if emergency == 1:
        # Randomly assign emergency to either lane for demo
        emergency_lane = random.choice(["Lane 1", "Lane 2"])
    else:
        emergency_lane = None

    # Prepare JSON payload
    data = {
        "sensor": "RFID",
        "emergency": emergency,
        "emergency_lane": emergency_lane  #  Which lane has the emergency
    }

    # Publish to MQTT
    client.publish(TOPIC_RFID, json.dumps(data))

    if emergency == 1:
        print(f"🚨 EMERGENCY DETECTED in {emergency_lane}! Published: {data}")
    else:
        print(f"Published to {TOPIC_RFID}: {data}")

    time.sleep(PUBLISH_INTERVAL)