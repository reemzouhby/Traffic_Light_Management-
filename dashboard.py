# dashboard.py - FIXED VERSION WITH ACCURATE COUNTDOWN

import tkinter as tk
from tkinter import ttk
import json
import paho.mqtt.client as mqtt
from datetime import datetime
import time
from config import BROKER, PORT, TOPIC_SUMMARY, DASHBOARD_UPDATE_INTERVAL

# Try to play ambulance sound on Windows
try:
    import winsound


    def play_ambulance_sound():
        try:
            winsound.PlaySound("ambulance.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
        except:

            pass
except ImportError:
    def play_ambulance_sound():
        pass


latest_data = {
    "lane1_vehicles": 0,
    "lane2_vehicles": 0,
    "emergency": 0,
    "emergency_lane": None,
    "green_light": "Lane 1",
    "green_duration": 0
}

stats = {
    "total_cycles": 0,
    "emergency_events": 0,
    "lane1_total_green": 0,
    "lane2_total_green": 0
}

#  Track green light timing
green_light_start_time = None
current_green_duration = 0
last_green_light = None
last_emergency_status = 0



def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✓ Connected to MQTT broker")
        client.subscribe(TOPIC_SUMMARY)
    else:
        print(f"✗ Connection failed: {rc}")


def on_message(client, userdata, msg):
    global latest_data
    try:
        payload = json.loads(msg.payload.decode())
        latest_data.update(payload)
    except Exception as e:
        print(f"Error parsing message: {e}")


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.loop_start()
# GUI SETUP


root = tk.Tk()
root.title("🚦 Smart Traffic Control System")
root.geometry("1200x700")
root.configure(bg="#1e1e1e")

style = ttk.Style()
style.theme_use('clam')
style.configure("TFrame", background="#1e1e1e")
style.configure("TLabel", background="#1e1e1e", foreground="#ffffff")

# HEADER
header_frame = tk.Frame(root, bg="#2d2d2d", height=60)
header_frame.pack(fill=tk.X)
header_frame.pack_propagate(False)

tk.Label(header_frame, text="🚦 SMART TRAFFIC CONTROL SYSTEM",
         font=("Arial", 18, "bold"), bg="#2d2d2d", fg="#00ff00").pack(side=tk.LEFT, padx=20, pady=10)
tk.Label(header_frame, text="● LIVE",
         font=("Arial", 12, "bold"), bg="#2d2d2d", fg="#00ff00").pack(side=tk.RIGHT, padx=20, pady=10)

# MAIN FRAME
main_frame = tk.Frame(root, bg="#1e1e1e")
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)


# =====================================================================
# LANE STATUS (LEFT)
# =====================================================================

def create_lane_frame(parent, lane_name, bg_color, fg_color):
    frame = tk.Frame(parent, bg=bg_color, relief=tk.SUNKEN, bd=2)
    tk.Label(frame, text=lane_name, font=("Arial", 11, "bold"), bg=bg_color, fg="#ffffff").pack(pady=5)
    vehicles_label = tk.Label(frame, text="🚗 Vehicles: 0", font=("Arial", 14, "bold"), bg=bg_color, fg=fg_color)
    vehicles_label.pack(pady=5)
    light_canvas = tk.Canvas(frame, width=150, height=100, bg="#1a1a1a", highlightthickness=0)
    light_canvas.pack(pady=10)
    return frame, vehicles_label, light_canvas


lane_section = tk.Frame(main_frame, bg="#2d2d2d", relief=tk.RAISED, bd=2)
lane_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
tk.Label(lane_section, text="🛣️  LANE STATUS", font=("Arial", 12, "bold"), bg="#2d2d2d", fg="#00ff00").pack(pady=10)

lane1_frame, lane1_vehicles_label, lane1_light_canvas = create_lane_frame(lane_section, "LANE 1", "#1a3a1a", "#00ff00")
lane1_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

lane2_frame, lane2_vehicles_label, lane2_light_canvas = create_lane_frame(lane_section, "LANE 2", "#3a1a1a", "#ff6b6b")
lane2_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

# =====================================================================
# CONTROL & EMERGENCY (MIDDLE)
# =====================================================================

control_section = tk.Frame(main_frame, bg="#2d2d2d", relief=tk.RAISED, bd=2)
control_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
tk.Label(control_section, text="⚙️  TRAFFIC CONTROL", font=("Arial", 12, "bold"), bg="#2d2d2d", fg="#00ff00").pack(
    pady=10)

# GREEN LIGHT
green_frame = tk.Frame(control_section, bg="#1a3a1a", relief=tk.SUNKEN, bd=2)
green_frame.pack(fill=tk.X, padx=10, pady=5)
tk.Label(green_frame, text="✅ GREEN LIGHT", font=("Arial", 10, "bold"), bg="#1a3a1a", fg="#00ff00").pack(pady=5)
green_light_label = tk.Label(green_frame, text="Lane 1", font=("Arial", 16, "bold"), bg="#1a3a1a", fg="#00ff00")
green_light_label.pack(pady=5)

# DURATION - UPDATED TO SHOW COUNTDOWN
duration_frame = tk.Frame(control_section, bg="#1a1a2e", relief=tk.SUNKEN, bd=2)
duration_frame.pack(fill=tk.X, padx=10, pady=5)
tk.Label(duration_frame, text="⏱️  GREEN DURATION COUNTDOWN", font=("Arial", 10, "bold"), bg="#1a1a2e",
         fg="#ffd700").pack(pady=5)
duration_label = tk.Label(duration_frame, text="0.0 / 45 seconds", font=("Arial", 14, "bold"), bg="#1a1a2e",
                          fg="#ffd700")
duration_label.pack(pady=5)
duration_progress = ttk.Progressbar(duration_frame, length=200, mode='determinate', value=0)
duration_progress.pack(pady=5, padx=10)

# EMERGENCY
emergency_frame = tk.Frame(control_section, bg="#3a1a1a", relief=tk.SUNKEN, bd=3)
emergency_frame.pack(fill=tk.X, padx=10, pady=10)
tk.Label(emergency_frame, text="🚨 EMERGENCY STATUS", font=("Arial", 10, "bold"), bg="#3a1a1a", fg="#ff0000").pack(
    pady=5)
emergency_status_label = tk.Label(emergency_frame, text="✓ NONE", font=("Arial", 12, "bold"), bg="#3a1a1a",
                                  fg="#00ff00")
emergency_status_label.pack(pady=5)
emergency_action_label = tk.Label(emergency_frame, text="No emergency vehicles", font=("Arial", 10), bg="#3a1a1a",
                                  fg="#ffffff")
emergency_action_label.pack(pady=5)

# =====================================================================
# STATISTICS (RIGHT)
# =====================================================================

stats_section = tk.Frame(main_frame, bg="#2d2d2d", relief=tk.RAISED, bd=2)
stats_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
tk.Label(stats_section, text="📊 STATISTICS", font=("Arial", 12, "bold"), bg="#2d2d2d", fg="#00ff00").pack(pady=10)


def create_stat_frame(parent, label_text, fg_color="#00ff00"):
    frame = tk.Frame(parent, bg="#1a1a2e", relief=tk.SUNKEN, bd=2)
    frame.pack(fill=tk.X, padx=10, pady=5)
    tk.Label(frame, text=label_text, font=("Arial", 9, "bold"), bg="#1a1a2e", fg=fg_color).pack(side=tk.LEFT, padx=10,
                                                                                                pady=5)
    value_label = tk.Label(frame, text="0", font=("Arial", 12, "bold"), bg="#1a1a2e", fg=fg_color)
    value_label.pack(side=tk.RIGHT, padx=10, pady=5)
    return value_label


cycle_count_label = create_stat_frame(stats_section, "Total Cycles")
emergency_count_label = create_stat_frame(stats_section, "Emergencies", fg_color="#ff0000")
lane1_green_label = create_stat_frame(stats_section, "Lane 1 Green")
lane2_green_label = create_stat_frame(stats_section, "Lane 2 Green")

time_label = tk.Label(stats_section, text="Last Update: --:--:--", font=("Arial", 9), bg="#2d2d2d", fg="#888888")
time_label.pack(pady=10)

# FOOTER
footer_frame = tk.Frame(root, bg="#2d2d2d", height=40)
footer_frame.pack(fill=tk.X)
footer_frame.pack_propagate(False)
tk.Label(footer_frame, text="Developed by: Reem, Maryam, Sourour", font=("Arial", 10, "italic"), bg="#2d2d2d",
         fg="#888888").pack(side=tk.RIGHT, padx=20, pady=10)


# =====================================================================
# TRAFFIC LIGHT DRAWING
# =====================================================================

def draw_traffic_light(canvas, color):
    canvas.delete("all")
    radius = 40
    x, y = 75, 50
    canvas.create_oval(x - radius, y - radius, x + radius, y + radius, outline="#444444", width=3, fill="#111111")

    if color == "green":
        canvas.create_oval(x - 30, y - 30, x + 30, y + 30, fill="#00ff00", outline="#00aa00", width=2)
    elif color == "red":
        canvas.create_oval(x - 30, y - 30, x + 30, y + 30, fill="#ff0000", outline="#aa0000", width=2)
    else:
        canvas.create_oval(x - 30, y - 30, x + 30, y + 30, fill="#333333", outline="#555555", width=2)




def update_dashboard():
    """
    Update dashboard with real-time countdown


    1. Countdown timer counts down every second (accurate)
    2. Synchronized with actual green light duration
    3. Total cycles counted when lane changes
    """
    global green_light_start_time, current_green_duration
    global last_green_light, last_emergency_status, stats

    # ===== UPDATE VEHICLE COUNTS =====
    lane1_vehicles_label.config(text=f"🚗 Vehicles: {latest_data['lane1_vehicles']}")
    lane2_vehicles_label.config(text=f"🚗 Vehicles: {latest_data['lane2_vehicles']}")

    # ===== DETECT LANE CHANGE (New Cycle) =====
    if latest_data["green_light"] != last_green_light:
        # LANE CHANGED = NEW CYCLE
        stats["total_cycles"] += 1

        # Record start time of new green light
        green_light_start_time = time.time()
        current_green_duration = latest_data["green_duration"]

        # Add to total green time for that lane
        if latest_data["green_light"] == "Lane 1":
            stats["lane1_total_green"] += current_green_duration
        else:
            stats["lane2_total_green"] += current_green_duration

        last_green_light = latest_data["green_light"]

        print(f"🔄 NEW CYCLE {stats['total_cycles']}: {latest_data['green_light']} gets {current_green_duration}s")

    # ===== TRAFFIC LIGHTS =====
    if latest_data["green_light"] == "Lane 1":
        draw_traffic_light(lane1_light_canvas, "green")
        draw_traffic_light(lane2_light_canvas, "red")
        lane1_frame.config(bg="#1a3a1a")
        lane2_frame.config(bg="#3a1a1a")
    else:
        draw_traffic_light(lane1_light_canvas, "red")
        draw_traffic_light(lane2_light_canvas, "green")
        lane1_frame.config(bg="#3a1a1a")
        lane2_frame.config(bg="#1a3a1a")

    green_light_label.config(text=latest_data["green_light"])

    # ===== ACCURATE COUNTDOWN TIMER =====
    if green_light_start_time is not None:
        # Calculate how much time has ELAPSED since green light started
        elapsed_time = time.time() - green_light_start_time

        # Calculate REMAINING time
        remaining_time = current_green_duration - elapsed_time

        # Make sure it doesn't go negative
        remaining_time = max(0, remaining_time)

        # Display countdown
        duration_label.config(text=f"{remaining_time:.1f} / {current_green_duration} seconds")

        # Update progress bar
        if current_green_duration > 0:
            progress = (remaining_time / current_green_duration) * 100
            duration_progress['value'] = progress
        else:
            duration_progress['value'] = 0

    # ===== EMERGENCY HANDLING =====
    # Only count emergency ONCE per event (when it changes from 0 to 1)
    if latest_data["emergency"] == 1 and last_emergency_status == 0:
        stats["emergency_events"] += 1
        play_ambulance_sound()
        print(f"🚨 EMERGENCY EVENT #{stats['emergency_events']}: {latest_data['emergency_lane']}")

    last_emergency_status = latest_data["emergency"]

    if latest_data["emergency"] == 1:
        emergency_status_label.config(text="🚨 ACTIVE", fg="#ff0000")
        emergency_action_label.config(text=f"→ Green given to {latest_data['emergency_lane']}")
        emergency_frame.config(bg="#661a1a")
    else:
        emergency_status_label.config(text="✓ NONE", fg="#00ff00")
        emergency_action_label.config(text="No emergency vehicles")
        emergency_frame.config(bg="#3a1a1a")

    # ===== UPDATE STATISTICS LABELS =====
    cycle_count_label.config(text=str(stats["total_cycles"]))
    emergency_count_label.config(text=str(stats["emergency_events"]))
    lane1_green_label.config(text=f"{stats['lane1_total_green']}s")
    lane2_green_label.config(text=f"{stats['lane2_total_green']}s")

    # ===== TIMESTAMP =====
    time_label.config(text=f"Last Update: {datetime.now().strftime('%H:%M:%S')}")

    # Schedule next update (fast refresh for smooth countdown)
    root.after(500, update_dashboard)  # Update every 500ms for smooth countdown




update_dashboard()
print("Dashboard started...")
print("\nDASHBOARD FEATURES:")
print("  ✓ Real-time countdown timer (accurate)")
print("  ✓ Synchronized with actual green light duration")
print("  ✓ Total cycles = number of lane changes")
print("  ✓ Emergency event tracking")
print("  ✓ Total green time per lane")
print()
root.mainloop()