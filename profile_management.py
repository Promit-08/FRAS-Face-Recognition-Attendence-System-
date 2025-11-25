import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os

DB_FILE = "profiles.db"

def open_profile_management(parent):
    # -----------------------------
    # Ensure database and table exist
    # -----------------------------
    def ensure_db():
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

    ensure_db()

    # -----------------------------
    # Window setup
    # -----------------------------
    window = tk.Toplevel(parent)
    window.title("Profile Management")
    window.geometry("750x600")
    window.config(bg="#f1f3f4")

    tk.Label(window, text="Profile Management",
             font=("Arial", 20, "bold"), bg="#1a73e8", fg="white",
             pady=10).pack(fill="x")

    frame = tk.Frame(window, bg="#f1f3f4", padx=20, pady=20)
    frame.pack(fill="both", expand=True)

    # -----------------------------
    # Table setup
    # -----------------------------
    columns = ("id", "student_id", "name", "department")
    tree = ttk.Treeview(frame, columns=columns, show="headings")

    tree.heading("id", text="ID")
    tree.heading("student_id", text="Student ID")
    tree.heading("name", text="Name")
    tree.heading("department", text="Department")

    tree.column("id", width=60, anchor="center")
    tree.column("student_id", width=150, anchor="center")
    tree.column("name", width=180, anchor="center")
    tree.column("department", width=150, anchor="center")

    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(fill="both", expand=True)

    # -----------------------------
    # Form fields for editing
    # -----------------------------
    form_frame = tk.Frame(window, bg="#f1f3f4", pady=10)
    form_frame.pack()

    tk.Label(form_frame, text="Student ID:", bg="#f1f3f4", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5, sticky="e")
    student_id_var = tk.StringVar()
    tk.Entry(form_frame, textvariable=student_id_var, font=("Arial", 12), width=25).grid(row=0, column=1, padx=5, pady=5)

    tk.Label(form_frame, text="Name:", bg="#f1f3f4", font=("Arial", 12)).grid(row=1, column=0, padx=5, pady=5, sticky="e")
    name_var = tk.StringVar()
    tk.Entry(form_frame, textvariable=name_var, font=("Arial", 12), width=25).grid(row=1, column=1, padx=5, pady=5)

    tk.Label(form_frame, text="Department:", bg="#f1f3f4", font=("Arial", 12)).grid(row=2, column=0, padx=5, pady=5, sticky="e")
    dept_var = tk.StringVar()
    tk.Entry(form_frame, textvariable=dept_var, font=("Arial", 12), width=25).grid(row=2, column=1, padx=5, pady=5)

    # -----------------------------
    # Database functions
    # -----------------------------
    def show_message(kind, title, msg):
        """Show messagebox over the current window."""
        window.attributes('-topmost', True)
        if kind == "info":
            messagebox.showinfo(title, msg, parent=window)
        elif kind == "warning":
            messagebox.showwarning(title, msg, parent=window)
        elif kind == "error":
            messagebox.showerror(title, msg, parent=window)
        window.attributes('-topmost', False)

    def load_profiles():
        if not os.path.exists(DB_FILE):
            show_message("warning", "Database Missing", "No profile data found yet.")
            return

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, student_id, name, department FROM profiles")
        rows = cursor.fetchall()
        conn.close()

        tree.delete(*tree.get_children())
        for row in rows:
            tree.insert("", "end", values=row)

    def update_profile():
        selected = tree.focus()
        if not selected:
            show_message("warning", "No Selection", "Please select a profile to update.")
            return

        values = tree.item(selected, "values")
        pid = values[0]
        new_student_id = student_id_var.get().strip()
        new_name = name_var.get().strip()
        new_dept = dept_var.get().strip()

        if not new_student_id or not new_name or not new_dept:
            show_message("warning", "Missing Data", "All fields are required.")
            return

        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE profiles
                SET student_id = ?, name = ?, department = ?
                WHERE id = ?
            """, (new_student_id, new_name, new_dept, pid))
            conn.commit()
            conn.close()

            load_profiles()
            show_message("info", "Updated", "Profile updated successfully.")
        except sqlite3.IntegrityError:
            show_message("error", "Duplicate Error", f"Student ID '{new_student_id}' already exists.\nUse a unique ID.")
        except Exception as e:
            show_message("error", "Error", f"Failed to update profile:\n{e}")

    def delete_profile():
        selected = tree.focus()
        if not selected:
            show_message("warning", "No Selection", "Please select a profile to delete.")
            return

        values = tree.item(selected, "values")
        pid = values[0]

        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete profile ID {pid}?", parent=window)
        if not confirm:
            return

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM profiles WHERE id=?", (pid,))
        conn.commit()
        conn.close()

        load_profiles()
        student_id_var.set("")
        name_var.set("")
        dept_var.set("")
        show_message("info", "Deleted", "Profile deleted successfully.")

    # -----------------------------
    # When user selects a row, load it into the form
    # -----------------------------
    def on_select(event):
        selected = tree.focus()
        if not selected:
            return
        values = tree.item(selected, "values")
        student_id_var.set(values[1])
        name_var.set(values[2])
        dept_var.set(values[3])

    tree.bind("<<TreeviewSelect>>", on_select)

    # -----------------------------
    # Buttons
    # -----------------------------
    btn_frame = tk.Frame(window, bg="#f1f3f4")
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Refresh", command=load_profiles,
              bg="#2196F3", fg="white", font=("Arial", 12, "bold"), width=12).grid(row=0, column=0, padx=10)

    tk.Button(btn_frame, text="Update", command=update_profile,
              bg="#FFA000", fg="white", font=("Arial", 12, "bold"), width=12).grid(row=0, column=1, padx=10)

    tk.Button(btn_frame, text="Delete", command=delete_profile,
              bg="#E53935", fg="white", font=("Arial", 12, "bold"), width=12).grid(row=0, column=2, padx=10)

    # -----------------------------
    # Initial data load
    # -----------------------------
    load_profiles()
