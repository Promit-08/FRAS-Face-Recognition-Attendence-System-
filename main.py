import tkinter as tk
from tkinter import messagebox, Toplevel
from PIL import Image, ImageTk, ImageEnhance
from create_profile import open_create_profile
from train_model_interface import open_train_model_interface
from face_recognition import open_face_recognition_window
from check_attendance import open_check_attendance_window
from profile_management import open_profile_management
from settings_interface import open_settings_interface

# -----------------------------
# Window Functions
# -----------------------------
def create_profile(): 
    open_create_profile(root)

def train_model():
    open_train_model_interface()

def recognize_face():
    open_face_recognition_window()

def check_attendance():
    open_check_attendance_window()

def manage_profiles():
    open_profile_management(root)

def open_settings():
    open_settings_interface()


# -----------------------------
# Hover Effects for Buttons
# -----------------------------
def on_enter(e):
    e.widget['background'] = e.widget.hover_bg

def on_leave(e):
    e.widget['background'] = e.widget.default_bg


# -----------------------------
# Main Window Setup
# -----------------------------
root = tk.Tk()
root.title("Face Recognition Attendance System")

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.geometry(f"{screen_width}x{screen_height}")
root.state('zoomed')
root.resizable(True, True)

# -----------------------------
# Background Setup
# -----------------------------
try:
    bg = Image.open("background2.jpg")
    bg = bg.resize((screen_width, screen_height), Image.LANCZOS)
    bg = ImageEnhance.Brightness(bg).enhance(0.85)
    bg_photo = ImageTk.PhotoImage(bg)
    bg_label = tk.Label(root, image=bg_photo)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
except Exception as e:
    print("Error loading background:", e)
    root.configure(bg="#f0f0f0")

# -----------------------------
# Title Label
# -----------------------------
title_label = tk.Label(
    root,
    text="FACE RECOGNITION ATTENDANCE SYSTEM",
    font=("Arial", 28, "bold"),
    bg="#000000",
    fg="#ffffff",
    bd=6,
    relief="ridge",
    padx=25,
    pady=15
)
title_label.place(relx=0.5, rely=0.1, anchor="center")

# -----------------------------
# Buttons Section (2×3 Grid)
# -----------------------------
button_frame = tk.Frame(root, bg="", bd=0)
button_frame.place(relx=0.5, rely=0.55, anchor="center")

button_style = {
    "width": 18,
    "height": 4,
    "font": ("Arial", 14, "bold"),
    "fg": "white",
    "relief": "raised",
    "bd": 5,
    "cursor": "hand2"
}

# Define Buttons
buttons = [
    ("Create\nProfile", "#4CAF50", "#45A049", create_profile),
    ("Train\nModel", "#2196F3", "#1E88E5", train_model),
    ("Recognize\nFace", "#FF9800", "#FB8C00", recognize_face),
    ("Check\nAttendance", "#9C27B0", "#8E24AA", check_attendance),
    ("Manage\nProfiles", "#9B9851", "#9B9851", manage_profiles),
    ("Settings", "#455A64", "#37474F", open_settings)
]

# Place Buttons in 2x3 Grid
row, col = 0, 0
for text, color, hover, cmd in buttons:
    btn = tk.Button(button_frame, text=text, bg=color, command=cmd, **button_style)
    btn.default_bg = color
    btn.hover_bg = hover
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    btn.grid(row=row, column=col, padx=50, pady=30)
    col += 1
    if col > 2:
        col = 0
        row += 1


root._bg_photo = bg_photo
root.mainloop()
