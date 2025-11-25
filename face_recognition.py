import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2, os
import sqlite3
import time
import threading
from collections import deque
from check_attendance import add_attendance_record
import serial

# --------------------- CONFIG ---------------------
DB_FILE = "profiles.db"
MODEL_FILE = "trainer.yml"
CONFIDENCE_THRESHOLD = 70
SMOOTHING_FRAMES = 15
COOLDOWN = 10
AUTO_OFF_DELAY = 10

# ------------------ SERIAL ARDUINO SETUP ------------------
arduino = serial.Serial('COM3', 9600, timeout=1)
time.sleep(2)

# ------------------ HELPER FUNCTIONS ------------------
def unlock_door_with_lcd(name, student_id, duration=5):
    try:
        command = f"OPEN|{name}|{student_id}|{duration}\n"
        arduino.write(command.encode())
        print(f"[INFO] Door unlock command sent for {name}")
    except Exception as e:
        print(f"[ERROR] Could not send command to Arduino: {e}")

def get_profile_from_db(student_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT name, department FROM profiles WHERE student_id = ?", (str(student_id),))
        row = cursor.fetchone()
        conn.close()
        return row if row else (None, None)
    except:
        return None, None

# --------------------- FACE RECOGNITION WINDOW ---------------------
def open_face_recognition_window():
    window = tk.Toplevel()
    window.title("Face Recognition - Attendance System")
    window.geometry("1150x720")
    window.configure(bg="#f5f5f5")
    window.resizable(False, False)

    header = tk.Label(window, text="Face Recognition System",
                      font=("Arial", 24, "bold"),
                      bg="#2196F3", fg="white", pady=15)
    header.pack(fill="x")

    # -------- Frame Layout --------
    frame = tk.Frame(window, bg="white", bd=2, relief="ridge")
    frame.place(relx=0.5, rely=0.52, anchor="center")

    cam_label = tk.Label(frame, bg="#000000", relief="ridge", width=640, height=480)
    cam_label.grid(row=0, column=0, padx=(30,10), pady=20)

    # Info Panel
    info_frame = tk.Frame(frame, bg="#f9f9f9", bd=2, relief="ridge")
    info_frame.grid(row=0, column=1, padx=(10,30), pady=20, sticky="n")

    tk.Label(info_frame, text="Person Information", font=("Arial",18,"bold"),
             bg="#f9f9f9").pack(pady=(15,10))

    tk.Label(info_frame, text="Name:", font=("Arial",14), bg="#f9f9f9").pack(anchor="w", padx=10)
    name_label = tk.Label(info_frame, text="N/A", font=("Arial",14,"bold"),
                          bg="#ffffff", width=28, relief="sunken", anchor="w", padx=5)
    name_label.pack(padx=10, pady=5)

    tk.Label(info_frame, text="Student ID:", font=("Arial",14), bg="#f9f9f9").pack(anchor="w", padx=10)
    id_label = tk.Label(info_frame, text="N/A", font=("Arial",14,"bold"),
                        bg="#ffffff", width=28, relief="sunken", anchor="w", padx=5)
    id_label.pack(padx=10, pady=5)

    tk.Label(info_frame, text="Department:", font=("Arial",14), bg="#f9f9f9").pack(anchor="w", padx=10)
    dept_label = tk.Label(info_frame, text="N/A", font=("Arial",14,"bold"),
                          bg="#ffffff", width=28, relief="sunken", anchor="w", padx=5)
    dept_label.pack(padx=10, pady=5)

    status_label = tk.Label(window, text="Recognition Stopped",
                            font=("Arial",14,"bold"), fg="red", bg="#f5f5f5")
    status_label.pack(pady=(0,10))

    # ---------------- Recognition Variables ----------------
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Error", "Could not open webcam.")
        window.destroy()
        return

    cap.set(3,640)
    cap.set(4,480)

    recognizer = None
    running = False
    last_logged = {}
    recent_ids = deque(maxlen=SMOOTHING_FRAMES)
    last_detection_time = 0

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    # ---------------- Start Recognition ----------------
    def start_scan():
        nonlocal running, recognizer
        if running:
            return
        try:
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            recognizer.read(MODEL_FILE)
        except Exception as e:
            messagebox.showerror("Error", f"Could not load model:\n{e}")
            return

        running = True
        status_label.config(text="Recognition Active", fg="green")
        print("[INFO] Recognition started (Manual or Ultrasonic Trigger)")

    # ---------------- Stop Recognition ----------------
    def stop_scan():
        nonlocal running
        running = False
        name_label.config(text="N/A")
        id_label.config(text="N/A")
        dept_label.config(text="N/A")
        status_label.config(text="Recognition Stopped", fg="red")
        print("[INFO] Recognition stopped")

    # ⭐ NEW — Start Button ⭐
    start_btn = tk.Button(window, text="START RECOGNITION",
                          font=("Arial", 14, "bold"),
                          bg="#4CAF50", fg="white",
                          padx=20, pady=10,
                          command=start_scan)
    start_btn.pack(pady=5)

    # ---------------- Listen to Arduino ----------------
    def listen_to_arduino():
        nonlocal last_detection_time
        while True:
            try:
                if arduino.in_waiting:
                    msg = arduino.readline().decode().strip()

                    if msg == "PERSON_DETECTED":
                        print("[ULTRASONIC] Person detected — starting scan.")
                        start_scan()
                        last_detection_time = time.time()

                    elif msg == "SCAN":
                        start_scan()
                        last_detection_time = time.time()

                    elif msg == "CLEAR":
                        last_detection_time = 0

            except:
                pass

            time.sleep(0.1)

    threading.Thread(target=listen_to_arduino, daemon=True).start()

    # ---------------- Camera Loop ----------------
    def update_camera():
        nonlocal last_detection_time, running

        ret, frame = cap.read()
        if ret:
            display_frame = frame.copy()
            detected_faces = []

            if running and recognizer:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.equalizeHist(gray)
                faces = face_cascade.detectMultiScale(gray, 1.1, 6)

                for (x, y, w, h) in faces:
                    face_roi = cv2.resize(gray[y:y+h, x:x+w], (200,200))
                    face_roi = cv2.equalizeHist(face_roi)
                    id_, confidence = recognizer.predict(face_roi)

                    if confidence < CONFIDENCE_THRESHOLD:
                        recent_ids.append(id_)
                    else:
                        recent_ids.append("Unknown")

                    final_id = max(set(recent_ids), key=recent_ids.count)

                    if final_id != "Unknown":
                        name, dept = get_profile_from_db(final_id)
                        if name:
                            detected_faces.append((x, y, w, h, name, final_id, dept))
                            now = time.time()
                            if (final_id not in last_logged) or (now - last_logged[final_id] > COOLDOWN):
                                add_attendance_record(name, final_id, dept)
                                last_logged[final_id] = now
                                unlock_door_with_lcd(name, final_id, 5)
                            last_detection_time = time.time()
                    else:
                        detected_faces.append((x, y, w, h, "Unknown", "", ""))

            # Update GUI labels
            if detected_faces:
                first = detected_faces[0]
                name_label.config(text=first[4])
                id_label.config(text=str(first[5]))
                dept_label.config(text=first[6])
            else:
                name_label.config(text="N/A")
                id_label.config(text="N/A")
                dept_label.config(text="N/A")

            # Draw boxes
            for (x, y, w, h, name, _, _) in detected_faces:
                color = (0,255,0) if name != "Unknown" else (0,0,255)
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), color, 2)
                cv2.putText(display_frame, name, (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            frame_resized = cv2.resize(display_frame, (640,480))
            img_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            img_tk = ImageTk.PhotoImage(Image.fromarray(img_rgb))
            cam_label.img_tk = img_tk
            cam_label.config(image=img_tk)

            # Auto stop
            if running and last_detection_time and (time.time() - last_detection_time > AUTO_OFF_DELAY):
                stop_scan()
                last_detection_time = 0

        cam_label.after(5, update_camera)

    update_camera()

    def on_close():
        cap.release()
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", on_close)
    window.mainloop()

# --------------------- MAIN ---------------------
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    open_face_recognition_window()
