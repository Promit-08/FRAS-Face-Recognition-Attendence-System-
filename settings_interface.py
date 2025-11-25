import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os

SETTINGS_FILE = "settings.json"

# -----------------------------
# Load or Initialize Settings
# -----------------------------
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {
        "camera_source": "0",
        "threshold": 0.6,
        "model_path": "models/",
        "attendance_log_path": "attendance_logs/"
    }

# -----------------------------
# Save Settings
# -----------------------------
def save_settings(settings, parent=None):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)
    # Messagebox attached to parent window
    messagebox.showinfo("Settings Saved", "Your settings have been saved successfully!", parent=parent)

# -----------------------------
# Browse folders
# -----------------------------
def browse_model_path(var, parent):
    folder = filedialog.askdirectory(parent=parent, title="Select Model Storage Folder")
    if folder:
        var.set(folder)

def browse_log_path(var, parent):
    folder = filedialog.askdirectory(parent=parent, title="Select Attendance Log Folder")
    if folder:
        var.set(folder)

# -----------------------------
# Main Settings Window
# -----------------------------
def open_settings_interface():
    settings = load_settings()

    win = tk.Toplevel()
    win.title("Settings")
    win.geometry("600x500")
    win.configure(bg="#f0f0f0")

    tk.Label(win, text="System Settings", font=("Arial", 20, "bold"),
             bg="#333", fg="white", pady=10).pack(fill=tk.X, pady=(0, 20))

    # -----------------------------
    # Camera Source
    # -----------------------------
    frame_camera = tk.Frame(win, bg="#f0f0f0")
    frame_camera.pack(pady=10, fill=tk.X, padx=30)
    tk.Label(frame_camera, text="Camera Source (0 for default):",
             font=("Arial", 12), bg="#f0f0f0").grid(row=0, column=0, sticky="w")
    camera_var = tk.StringVar(value=settings["camera_source"])
    tk.Entry(frame_camera, textvariable=camera_var, font=("Arial", 12), width=25).grid(row=0, column=1, padx=10)

    # -----------------------------
    # Recognition Threshold
    # -----------------------------
    frame_threshold = tk.Frame(win, bg="#f0f0f0")
    frame_threshold.pack(pady=10, fill=tk.X, padx=30)
    tk.Label(frame_threshold, text="Recognition Threshold:",
             font=("Arial", 12), bg="#f0f0f0").grid(row=0, column=0, sticky="w")
    threshold_var = tk.DoubleVar(value=settings["threshold"])
    slider = tk.Scale(frame_threshold, from_=0.1, to=1.0, orient="horizontal",
                      resolution=0.05, variable=threshold_var, length=250, bg="#f0f0f0")
    slider.grid(row=0, column=1, padx=10)

    # -----------------------------
    # Model Storage Path
    # -----------------------------
    frame_model = tk.Frame(win, bg="#f0f0f0")
    frame_model.pack(pady=10, fill=tk.X, padx=30)
    tk.Label(frame_model, text="Model Storage Path:", font=("Arial", 12), bg="#f0f0f0").grid(row=0, column=0, sticky="w")
    model_var = tk.StringVar(value=settings["model_path"])
    tk.Entry(frame_model, textvariable=model_var, font=("Arial", 12), width=30).grid(row=0, column=1, padx=10)
    tk.Button(frame_model, text="Browse", command=lambda: browse_model_path(model_var, win),
              bg="#2196F3", fg="white", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=10)

    # -----------------------------
    # Attendance Log Path
    # -----------------------------
    frame_log = tk.Frame(win, bg="#f0f0f0")
    frame_log.pack(pady=10, fill=tk.X, padx=30)
    tk.Label(frame_log, text="Attendance Log Save Path:", font=("Arial", 12), bg="#f0f0f0").grid(row=0, column=0, sticky="w")
    log_var = tk.StringVar(value=settings["attendance_log_path"])
    tk.Entry(frame_log, textvariable=log_var, font=("Arial", 12), width=30).grid(row=0, column=1, padx=10)
    tk.Button(frame_log, text="Browse", command=lambda: browse_log_path(log_var, win),
              bg="#2196F3", fg="white", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=10)

    # -----------------------------
    # Save Button
    # -----------------------------
    def save_changes():
        new_settings = {
            "camera_source": camera_var.get(),
            "threshold": threshold_var.get(),
            "model_path": model_var.get(),
            "attendance_log_path": log_var.get()
        }
        save_settings(new_settings, parent=win)  # attach messagebox to this window

    tk.Button(win, text="Save Settings", command=save_changes,
              bg="#4CAF50", fg="white", font=("Arial", 14, "bold"),
              width=20, height=2).pack(pady=30)

    win.mainloop()


# -----------------------------
# Run standalone for testing
# -----------------------------
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    open_settings_interface()
