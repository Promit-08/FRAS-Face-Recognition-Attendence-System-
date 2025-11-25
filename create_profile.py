import tkinter as tk
from tkinter import messagebox, Toplevel
import sqlite3
import os
import cv2
import time

DB_FILE = "profiles.db"

# -------------------------------------
# Helper: Capture video frames (updated)
# -------------------------------------
def capture_video_and_save(name, student_id, parent):
    folder_name = f"{name.replace(' ', '_')}_{student_id}"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Camera Error", "Could not open webcam.", parent=parent)
        return False

    messagebox.showinfo("Recording", "Recording started for 30 seconds. Press 'q' to stop early.", parent=parent)
    start_time = time.time()
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Resize frame to speed up processing
        frame_resized = cv2.resize(frame, (640, 480))
        frame_path = os.path.join(folder_name, f"frame_{frame_count:04d}.jpg")
        cv2.imwrite(frame_path, frame_resized)
        frame_count += 1

        # Optional: Draw rectangle around detected face in real-time
        gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(80, 80))
        for (x, y, w, h) in faces:
            cv2.rectangle(frame_resized, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.imshow("Recording...", frame_resized)

        # Stop after 30 seconds or 'q'
        if time.time() - start_time > 30:
            break
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    parent.attributes('-topmost', True)
    messagebox.showinfo("Recording Done", f"Saved {frame_count} frames in '{folder_name}'.", parent=parent)
    parent.attributes('-topmost', False)

    extract_faces_from_folder(folder_name, parent)
    return True

# -------------------------------------
# Helper: Extract faces from captured frames (updated)
# -------------------------------------
def extract_faces_from_folder(folder_name, parent):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    files = [f for f in os.listdir(folder_name) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]

    if not files:
        parent.attributes('-topmost', True)
        messagebox.showerror("No Images", "No images found in the folder.", parent=parent)
        parent.attributes('-topmost', False)
        return

    processed = 0
    for filename in files:
        file_path = os.path.join(folder_name, filename)
        img = cv2.imread(file_path)
        if img is None:
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=6,
            minSize=(80, 80),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        if len(faces) == 0:
            continue

        # Crop and save all detected faces
        for (x, y, w, h) in faces:
            face_crop = img[y:y + h, x:x + w]
            crop_path = os.path.join(folder_name, f"face_{processed:04d}.jpg")
            cv2.imwrite(crop_path, face_crop)
            processed += 1

    parent.attributes('-topmost', True)
    messagebox.showinfo("Processing Done", f"✅ Cropped faces in {processed} frames from '{folder_name}'.", parent=parent)
    parent.attributes('-topmost', False)

# -------------------------------------
# Main Create Profile Window
# -------------------------------------
def open_create_profile(parent):
    # --- Database Setup ---
    def init_db():
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                department TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    init_db()

    # --- UI Setup ---
    profile_window = Toplevel(parent)
    profile_window.title("Create Profile")
    profile_window.geometry("500x600")
    profile_window.config(bg="#e8f0fe")

    tk.Label(profile_window, text="Create New Profile",
             font=("Arial", 20, "bold"), bg="#1a73e8", fg="white",
             pady=10).pack(fill="x")

    form = tk.Frame(profile_window, bg="#e8f0fe", padx=30, pady=30)
    form.pack(fill="both", expand=True)

    # --- Input fields ---
    tk.Label(form, text="Name:", font=("Arial", 14), bg="#e8f0fe").grid(row=0, column=0, sticky="w", pady=10)
    name_entry = tk.Entry(form, font=("Arial", 14), width=25)
    name_entry.grid(row=0, column=1)

    tk.Label(form, text="Student ID:", font=("Arial", 14), bg="#e8f0fe").grid(row=1, column=0, sticky="w", pady=10)
    student_id_entry = tk.Entry(form, font=("Arial", 14), width=25)
    student_id_entry.grid(row=1, column=1)

    tk.Label(form, text="Department:", font=("Arial", 14), bg="#e8f0fe").grid(row=2, column=0, sticky="w", pady=10)
    dept_entry = tk.Entry(form, font=("Arial", 14), width=25)
    dept_entry.grid(row=2, column=1)

    # --- Face capture flag ---
    face_captured = {"status": False}

    # --- Capture Face Sample ---
    def capture_face():
        name = name_entry.get().strip()
        student_id = student_id_entry.get().strip()
        if not name or not student_id:
            profile_window.attributes('-topmost', True)
            messagebox.showwarning("Missing Info", "Please enter Name and Student ID before capturing.", parent=profile_window)
            profile_window.attributes('-topmost', False)
            return
        result = capture_video_and_save(name, student_id, parent=profile_window)
        if result:
            face_captured["status"] = True

    capture_btn = tk.Button(form, text="Capture Face Sample",
                            font=("Arial", 14, "bold"), bg="#34a853", fg="white",
                            width=20, height=2, command=capture_face)
    capture_btn.grid(row=3, column=0, columnspan=2, pady=20)

    # --- Save Profile ---
    def save_profile():
        name = name_entry.get().strip()
        student_id = student_id_entry.get().strip()
        dept = dept_entry.get().strip()

        if not name or not student_id or not dept:
            profile_window.attributes('-topmost', True)
            messagebox.showwarning("Input Error", "Please fill all fields.", parent=profile_window)
            profile_window.attributes('-topmost', False)
            return

        if not face_captured["status"]:
            profile_window.attributes('-topmost', True)
            messagebox.showwarning("Face Required", "You must capture a face sample before saving the profile.", parent=profile_window)
            profile_window.attributes('-topmost', False)
            return

        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO profiles (student_id, name, department) VALUES (?, ?, ?)",
                           (student_id, name, dept))
            conn.commit()
            conn.close()

            profile_window.attributes('-topmost', True)
            messagebox.showinfo("Success", f"Profile created for {name} (ID: {student_id})", parent=profile_window)
            profile_window.attributes('-topmost', False)
            profile_window.destroy()

        except sqlite3.IntegrityError:
            profile_window.attributes('-topmost', True)
            messagebox.showerror("Duplicate Entry", f"Student ID '{student_id}' already exists.", parent=profile_window)
            profile_window.attributes('-topmost', False)
        except Exception as e:
            profile_window.attributes('-topmost', True)
            messagebox.showerror("Error", str(e), parent=profile_window)
            profile_window.attributes('-topmost', False)

    save_btn = tk.Button(form, text="Save Profile",
                         font=("Arial", 14, "bold"), bg="#1a73e8", fg="white",
                         width=20, height=2, command=save_profile)
    save_btn.grid(row=4, column=0, columnspan=2, pady=10)


# --- Main App ---
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Student Profile System")
    root.geometry("400x300")
    tk.Button(root, text="Create Profile", font=("Arial", 16), width=20,
              command=lambda: open_create_profile(root)).pack(pady=50)
    root.mainloop()
