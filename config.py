

BROKER = "broker.hivemq.com"
PORT = 1883

# Topics
TOPIC_LANE_1 = "traffic/lane1"
TOPIC_LANE_2 = "traffic/lane2"
TOPIC_RFID = "traffic/emergency"
TOPIC_SUMMARY = "traffic/summary"

# Sensor & Traffic settings
PUBLISH_INTERVAL = 2   # seconds
GREEN_MIN = 10
GREEN_MAX = 45
MAX_VEHICLES = 20

EMERGENCY_PROBABILITY = 0.05  # 5% chance per sensor read


# New settings for better visualization
DASHBOARD_UPDATE_INTERVAL = 2000  # milliseconds
LANE_1_PRIORITY = "Lane 1"  # Which lane gets priority for emergency
LANE_2_PRIORITY = "Lane 2"