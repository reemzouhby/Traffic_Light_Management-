# main_launcher.py - MASTER LAUNCHER FOR ENTIRE SYSTEM

import subprocess
import time
import sys
import os
from threading import Thread

# List of all sensor simulation files to run
SENSOR_SCRIPTS = [
    r"C:\Users\Omen\PycharmProjects\Traffic_Light_Management\.venv\sensors\lane1_ir.py",
    r"C:\Users\Omen\PycharmProjects\Traffic_Light_Management\.venv\sensors\lane1_ultrasonic.py",
    r"C:\Users\Omen\PycharmProjects\Traffic_Light_Management\.venv\sensors\lane2_ir.py",
    r"C:\Users\Omen\PycharmProjects\Traffic_Light_Management\.venv\sensors\lane2_ultrasonic.py",
    r"C:\Users\Omen\PycharmProjects\Traffic_Light_Management\.venv\sensors\rfid.py",
    r"C:\Users\Omen\PycharmProjects\Traffic_Light_Management\.venv\gateway\gateway_publsiher.py",
    r"C:\Users\Omen\PycharmProjects\Traffic_Light_Management\.venv\cloud\traffic_logic.py"
]

# Store process references
processes = []


def launch_sensor(script_name):
    """Launch a sensor simulation script in a separate process"""
    try:
        print(f"🚀 Starting {script_name}...")
        process = subprocess.Popen(
            [sys.executable, script_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1
        )

        processes.append(process)

        # Print output in real-time
        for line in process.stdout:
            print(f"[{script_name}] {line.strip()}")
    except Exception as e:
        print(f"❌ Error launching {script_name}: {e}")


def main():
    print("\n" + "=" * 70)
    print("🚦 SMART TRAFFIC CONTROL SYSTEM - MASTER LAUNCHER")
    print("=" * 70 + "\n")

    print("📊 Starting all sensor simulations...")

    # Launch all sensor scripts in separate threads (non-blocking)
    threads = []
    for script in SENSOR_SCRIPTS:
        t = Thread(target=launch_sensor, args=(script,), daemon=True)
        t.start()
        threads.append(t)
        time.sleep(0.5)  # Stagger startup

    print(f"\n✅ All sensor simulations started!")
    print("⏳ Waiting 3 seconds for sensors to establish MQTT connections...\n")
    time.sleep(3)

    print("=" * 70)
    print("🎯 Launching DASHBOARD in main window...")
    print("=" * 70 + "\n")

    # Launch dashboard in main process (blocking)
    try:
        subprocess.run([sys.executable, r"C:\Users\Omen\PycharmProjects\Traffic_Light_Management\.venv\dashboard.py"])
    except KeyboardInterrupt:
        print("\n\n⛔ Shutting down all processes...")
    finally:
        # Kill all sensor processes
        for process in processes:
            process.terminate()
        print("✅ All processes terminated.")


if __name__ == "__main__":
    main()