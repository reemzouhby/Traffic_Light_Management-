
import random
import time
import json
import paho.mqtt.client as mqtt
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import BROKER, PORT, TOPIC_LANE_1, PUBLISH_INTERVAL, MAX_VEHICLES
# MQTT Setup
client = mqtt.Client()
client.connect(BROKER, PORT, 60)
client.loop_start()

print("Lane 1 Ultrasonic sensor simulation started...")
# Simulation Loop
while True:
    # Simulate vehicle density (number of vehicles in the lane)
    vehicle_count = random.randint(0, MAX_VEHICLES)

    # Prepare JSON payload
    data = {
        "lane": "Lane 1",
        "sensor": "Ultrasonic",
        "vehicle_count": vehicle_count
    }

    # Publish to MQTT
    client.publish(TOPIC_LANE_1, json.dumps(data))
    print(f"Published to {TOPIC_LANE_1}: {data}")

    time.sleep(PUBLISH_INTERVAL)