
import random
import time
import json
import paho.mqtt.client as mqtt
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import BROKER, PORT, TOPIC_LANE_1, PUBLISH_INTERVAL


# MQTT Setup , we need for this broker
client = mqtt.Client() # create a new mqtt client instance
client.connect(BROKER, PORT, 60) # connect to HiveMqq broker
client.loop_start()#starts a background thread so the client can handle network traffic, reconnections, and callbacks automatically

print("Lane 1 IR sensor simulation started...")

# Simulation Loop

while True: # to keep the simulation alive until we stop it manually
    #  0 = no vehicle, 1 = vehicle detected
    vehicle_detected = random.choice([0, 1])

    # Prepare JSON payload , convert to json to make it ready for mqtt broker
    data = {
        "lane": "Lane 1",
        "sensor": "IR",
        "vehicle_detected": vehicle_detected
    }

    # Publish to MQTT
    client.publish(TOPIC_LANE_1, json.dumps(data)) # send data to broker
    print(f"Published to {TOPIC_LANE_1}: {data}")

    time.sleep(PUBLISH_INTERVAL)
