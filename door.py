# door_control.py
import time
import serial

# ----------------- ARDUINO CONFIG -----------------
ARDUINO_PORT = "COM4"      # Change this according to your PC
BAUD_RATE = 9600


def send_command_to_arduino(message):
    """
    Sends a message to Arduino over Serial.
    Message example:
        OPEN|John Doe|20240123|5
    """
    try:
        ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # Wait for Arduino reset
        ser.write((message + "\n").encode())
        ser.close()
        print(f"[ARDUINO] Sent: {message}")
    except Exception as e:
        print(f"[ARDUINO ERROR] {e}")


def unlock_door_with_lcd(name, student_id, duration=5):
    """
    This sends combined door unlock + LCD display command to Arduino.
    """
    msg = f"OPEN|{name}|{student_id}|{duration}"
    send_command_to_arduino(msg)