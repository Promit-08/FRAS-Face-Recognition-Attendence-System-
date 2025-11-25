import os
import cv2
import numpy as np
from PIL import Image
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from threading import Thread

MODEL_FILE = "trainer.yml"
DATASET_DIR = os.getcwd()  # all profile folders are in current working directory

def open_train_model_interface():
    window = tk.Toplevel()
    window.title("Train Face Recognition Model - Attendance System")
    window.geometry("1000x700")
    window.configure(bg="#f5f5f5")
    window.resizable(False, False)

    # ----------------------------- Header -----------------------------
    header = tk.Label(window, text="Train Face Recognition Model",
                      font=("Arial", 24, "bold"),
                      bg="#2196F3", fg="white", pady=15)
    header.pack(fill="x")

    # ----------------------------- Main Frame -----------------------------
    frame = tk.Frame(window, bg="white", bd=2, relief="ridge")
    frame.place(relx=0.5, rely=0.52, anchor="center", width=900, height=500)

    desc = tk.Label(frame, text=(
        "All profiles will be retrained together every time training is started.\n"
        "Model accuracy has been improved with preprocessing for distance and lighting."
    ),
    font=("Arial", 14), bg="white", justify="center", fg="#333")
    desc.pack(pady=40)

    progress_label = tk.Label(frame, text="Training Progress:",
                              font=("Arial", 14, "bold"), bg="white")
    progress_label.pack(pady=(20, 10))

    progress = ttk.Progressbar(frame, orient="horizontal", length=600, mode="determinate")
    progress.pack(pady=10)

    status_label = tk.Label(frame, text="Waiting to start training...",
                            font=("Arial", 12, "italic"), bg="white", fg="#555")
    status_label.pack(pady=5)

    # ----------------------------- Buttons Frame -----------------------------
    btn_frame = tk.Frame(window, bg="#f5f5f5")
    btn_frame.pack(pady=20)

    log_messages = []
    log_win = None
    log_box = None
    stop_flag = False
    training_thread = None

    # ----------------------------- Log Window -----------------------------
    def view_log():
        nonlocal log_win, log_box
        if log_win is None or not tk.Toplevel.winfo_exists(log_win):
            log_win = tk.Toplevel(window)
            log_win.title("Training Log")
            log_win.geometry("600x400")
            log_win.configure(bg="#f5f5f5")
            log_win.transient(window)
            log_win.grab_set()

            log_box = scrolledtext.ScrolledText(log_win, font=("Arial", 12), bg="#f0f0f0")
            log_box.pack(fill="both", expand=True, padx=10, pady=10)
            log_box.config(state="disabled")

        update_log_box()

    def update_log_box():
        if log_box:
            log_box.config(state="normal")
            log_box.delete(1.0, tk.END)
            log_box.insert(tk.END, "\n".join(log_messages))
            log_box.config(state="disabled")
            log_box.yview(tk.END)

        if training_thread and training_thread.is_alive():
            window.after(500, update_log_box)

    # ----------------------------- Profile Viewer -----------------------------
    def view_profiles():
        profiles_win = tk.Toplevel(window)
        profiles_win.title("Profile Status")
        profiles_win.geometry("500x500")
        profiles_win.configure(bg="#f5f5f5")
        profiles_win.transient(window)
        profiles_win.grab_set()

        list_box = tk.Listbox(profiles_win, font=("Arial", 12))
        list_box.pack(fill="both", expand=True, padx=10, pady=(10,0))

        def refresh_profiles():
            list_box.delete(0, tk.END)
            profile_folders = [
                f for f in os.listdir(DATASET_DIR)
                if os.path.isdir(os.path.join(DATASET_DIR, f))
                and any(img.lower().endswith(('.jpg', '.jpeg', '.png'))
                        for img in os.listdir(os.path.join(DATASET_DIR, f)))
            ]
            for folder in profile_folders:
                list_box.insert(tk.END, f"{folder}  - Ready")
                list_box.itemconfig(tk.END, fg="green")

        refresh_btn = tk.Button(profiles_win, text="Refresh", bg="#2196F3", fg="white",
                                font=("Arial", 12, "bold"), command=refresh_profiles)
        refresh_btn.pack(pady=(0,10))

        refresh_profiles()

    # ----------------------------- FACE PREPROCESSING -----------------------------
    def preprocess_face(img):
        # Equalize histogram (lighting correction)
        img = cv2.equalizeHist(img)

        # Reduce noise
        img = cv2.GaussianBlur(img, (3, 3), 0)

        # Resize to standard LBPH size
        img = cv2.resize(img, (200, 200))

        return img

    # ----------------------------- LABEL EXTRACTOR -----------------------------
    def extract_label(folder_name):
        digits = ''.join(filter(str.isdigit, folder_name))
        if digits.isdigit():
            return int(digits)
        return abs(hash(folder_name)) % 10000

    # ----------------------------- MAIN TRAINING FUNCTION -----------------------------
    def train_model():
        nonlocal stop_flag, log_messages
        stop_flag = False
        log_messages.clear()

        recognizer = cv2.face.LBPHFaceRecognizer_create(radius=1, neighbors=8,
                                                        grid_x=8, grid_y=8)

        detector = cv2.CascadeClassifier(cv2.data.haarcascades +
                                         "haarcascade_frontalface_default.xml")

        # Collect folders
        folders = [
            f for f in os.listdir(DATASET_DIR)
            if os.path.isdir(os.path.join(DATASET_DIR, f))
            and any(img.lower().endswith(('.jpg', '.jpeg', '.png'))
                    for img in os.listdir(os.path.join(DATASET_DIR, f)))
        ]

        if not folders:
            status_label.config(text="No training folders found!")
            return

        total_images = sum(
            len([img for img in os.listdir(os.path.join(DATASET_DIR, f))
                 if img.lower().endswith(('.jpg', '.jpeg', '.png'))])
            for f in folders
        )

        progress["maximum"] = total_images
        progress["value"] = 0

        face_samples, ids = [], []

        log_messages.append(f"🔹 Training {len(folders)} profiles...")

        # ----------------------------- Collect Images -----------------------------
        for folder in folders:
            folder_path = os.path.join(DATASET_DIR, folder)
            label = extract_label(folder)

            for img_name in os.listdir(folder_path):
                if stop_flag: return

                if not img_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                    continue

                img_path = os.path.join(folder_path, img_name)
                try:
                    pil_img = Image.open(img_path).convert('L')
                except:
                    log_messages.append(f"⚠️ Skipped corrupted file: {img_name}")
                    continue

                img_np = np.array(pil_img, 'uint8')

                # Detect faces, allow small faces for distance variation
                faces = detector.detectMultiScale(img_np, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))

                if len(faces) == 0:
                    log_messages.append(f"❌ No face detected in {img_name}")
                else:
                    for (x, y, w, h) in faces:
                        face = img_np[y:y+h, x:x+w]
                        face = preprocess_face(face)

                        face_samples.append(face)
                        ids.append(label)
                        log_messages.append(f"✅ Face added from {img_name}")
                        break  # Only one face per image

                progress["value"] += 1
                window.update_idletasks()

        if not face_samples:
            status_label.config(text="Training failed: No valid faces!")
            log_messages.append("❌ No valid faces found.")
            return

        # ----------------------------- Train Model -----------------------------
        status_label.config(text="Training model...")
        log_messages.append("🔹 Training LBPH model...")

        recognizer.train(face_samples, np.array(ids))
        recognizer.save(MODEL_FILE)

        status_label.config(text="✅ Training completed successfully!")
        log_messages.append("✅ Model saved as trainer.yml")

    # ----------------------------- Stop Training -----------------------------
    def stop_training():
        nonlocal stop_flag
        stop_flag = True
        status_label.config(text="Stopping training...")
        log_messages.append("⚠️ Stop requested by user.")

    # ----------------------------- Buttons -----------------------------
    tk.Button(btn_frame, text="Start Training", bg="#4CAF50", fg="white",
              font=("Arial", 14, "bold"), width=20,
              command=lambda: Thread(target=train_model).start()).grid(row=0, column=0, padx=20)

    tk.Button(btn_frame, text="Stop Training", bg="#F44336", fg="white",
              font=("Arial", 14, "bold"), width=20,
              command=stop_training).grid(row=0, column=1, padx=20)

    tk.Button(btn_frame, text="View Profiles/Log", bg="#2196F3", fg="white",
              font=("Arial", 14, "bold"), width=20,
              command=view_profiles).grid(row=0, column=2, padx=20)

    window.mainloop()


# ----------------------------- Run Directly -----------------------------
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    open_train_model_interface()
