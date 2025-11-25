import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv
from datetime import datetime

DB_FILE = "attendance.db"

# -----------------------------
# Ensure DB Exists
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            student_id TEXT,
            department TEXT,
            date TEXT,
            time TEXT,
            status TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            student_id TEXT NOT NULL UNIQUE,
            department TEXT
        )
    ''')
    conn.commit()
    conn.close()

# -----------------------------
# Insert Attendance Record
# -----------------------------
def add_attendance_record(name, student_id, department, status="Present"):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")

    cursor.execute('''
        SELECT * FROM attendance_records 
        WHERE student_id=? AND date=? 
    ''', (student_id, date_str))
    record = cursor.fetchone()

    if record:
        cursor.execute('''
            UPDATE attendance_records 
            SET status=?, time=? 
            WHERE student_id=? AND date=?
        ''', (status, time_str, student_id, date_str))
    else:
        cursor.execute('''
            INSERT INTO attendance_records (name, student_id, department, date, time, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, student_id, department, date_str, time_str, status))
    conn.commit()
    conn.close()

# -----------------------------
# Auto mark absent for past days
# -----------------------------
def mark_absent_for_past_days():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT student_id, name, department FROM students")
    students = cursor.fetchall()
    cursor.execute("SELECT DISTINCT date FROM attendance_records")
    existing_dates = [row[0] for row in cursor.fetchall()]
    today = datetime.now().strftime("%Y-%m-%d")

    for student_id, name, department in students:
        cursor.execute("SELECT date FROM attendance_records WHERE student_id=?", (student_id,))
        student_dates = [row[0] for row in cursor.fetchall()]
        for date in existing_dates:
            if date < today and date not in student_dates:
                cursor.execute('''
                    INSERT INTO attendance_records (name, student_id, department, date, time, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, student_id, department, date, "00:00:00", "Absent"))
    conn.commit()
    conn.close()

# -----------------------------
# Check Attendance Window
# -----------------------------
def open_check_attendance_window():
    init_db()
    mark_absent_for_past_days()

    window = tk.Toplevel()
    window.title("Check Attendance - Attendance System")
    window.geometry("1000x750")
    window.configure(bg="#f5f5f5")
    window.resizable(False, False)

    def show_message(kind, title, msg):
        window.attributes('-topmost', True)
        if kind == "info":
            messagebox.showinfo(title, msg, parent=window)
        elif kind == "warning":
            messagebox.showwarning(title, msg, parent=window)
        elif kind == "error":
            messagebox.showerror(title, msg, parent=window)
        window.attributes('-topmost', False)

    header = tk.Label(window, text="Attendance Record Viewer",
                      font=("Arial", 24, "bold"),
                      bg="#9C27B0", fg="white", pady=15)
    header.pack(fill="x")

    # -----------------------------
    # Filter Panel
    # -----------------------------
    filter_frame = tk.Frame(window, bg="#f5f5f5", pady=10)
    filter_frame.pack(fill="x")

    tk.Label(filter_frame, text="Filter by:", bg="#f5f5f5", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=5)
    filter_var = tk.StringVar(value="All Records")
    filter_menu = ttk.Combobox(filter_frame, textvariable=filter_var,
                               values=["All Records", "Today's Records"], state="readonly", width=20)
    filter_menu.grid(row=0, column=1, padx=5)

    tk.Label(filter_frame, text="Department:", bg="#f5f5f5", font=("Arial", 12)).grid(row=0, column=2, padx=5)
    dept_var = tk.StringVar()
    tk.Entry(filter_frame, textvariable=dept_var, width=20).grid(row=0, column=3, padx=5)

    tk.Label(filter_frame, text="Status:", bg="#f5f5f5", font=("Arial", 12)).grid(row=0, column=4, padx=5)
    status_var = tk.StringVar(value="All")
    ttk.Combobox(filter_frame, textvariable=status_var,
                 values=["All", "Present", "Absent"], state="readonly", width=20).grid(row=0, column=5, padx=5)

    # -----------------------------
    # Table Section
    # -----------------------------
    frame = tk.Frame(window, bg="white", bd=2, relief="ridge")
    frame.place(relx=0.5, rely=0.55, anchor="center", width=950, height=520)

    columns = ("id", "name", "student_id", "department", "date", "time", "status")
    table = ttk.Treeview(frame, columns=columns, show="headings", height=15)

    for col in columns:
        table.heading(col, text=col.capitalize())
        table.column(col, width=130, anchor="center")

    table.pack(fill="both", expand=True, padx=20, pady=20)

    vsb = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
    vsb.pack(side="right", fill="y")
    table.configure(yscrollcommand=vsb.set)

    # Style configuration
    style = ttk.Style()
    style.configure("Treeview", rowheight=25, foreground="black")

    table.tag_configure("present_status", foreground="green")
    table.tag_configure("absent_status", foreground="red")

    # -----------------------------
    # Functions
    # -----------------------------
    def insert_with_color(row):
        # all black first
        values = list(row)
        tags = None
        if row[-1].lower() == "present":
            tags = ("present_status",)
        elif row[-1].lower() == "absent":
            tags = ("absent_status",)
        table.insert("", "end", values=values, tags=tags)

    def load_attendance():
        table.delete(*table.get_children())
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM attendance_records ORDER BY date DESC, time DESC")
        for row in cursor.fetchall():
            insert_with_color(row)
        conn.close()

    def filter_attendance(*args):
        table.delete(*table.get_children())
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        query = "SELECT * FROM attendance_records WHERE 1=1"
        params = []
        if filter_var.get() == "Today's Records":
            today = datetime.now().strftime("%Y-%m-%d")
            query += " AND date=?"
            params.append(today)
        if dept_var.get().strip():
            query += " AND department LIKE ?"
            params.append(f"%{dept_var.get().strip()}%")
        if status_var.get() != "All":
            query += " AND status=?"
            params.append(status_var.get())
        query += " ORDER BY date DESC, time DESC"
        cursor.execute(query, params)
        for row in cursor.fetchall():
            insert_with_color(row)
        conn.close()

    def export_attendance():
        file_path = filedialog.asksaveasfilename(parent=window, defaultextension=".csv",
                                                 filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM attendance_records")
        rows = cursor.fetchall()
        conn.close()
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name", "Student ID", "Department", "Date", "Time", "Status"])
            writer.writerows(rows)
        show_message("info", "Success", f"Attendance exported successfully to {file_path}")

    def refresh():
        filter_attendance()
        show_message("info", "Refreshed", "Attendance data refreshed!")

    filter_var.trace_add("write", filter_attendance)
    dept_var.trace_add("write", filter_attendance)
    status_var.trace_add("write", filter_attendance)

    btn_frame = tk.Frame(window, bg="#f5f5f5")
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Load Attendance", bg="#2196F3", fg="white",
              font=("Arial", 14, "bold"), width=17, command=load_attendance).grid(row=0, column=0, padx=20)
    tk.Button(btn_frame, text="Export Data", bg="#4CAF50", fg="white",
              font=("Arial", 14, "bold"), width=17, command=export_attendance).grid(row=0, column=1, padx=20)
    tk.Button(btn_frame, text="Refresh Table", bg="#FF9800", fg="white",
              font=("Arial", 14, "bold"), width=17, command=refresh).grid(row=0, column=2, padx=20)

    filter_attendance()

# -----------------------------
# Run for testing
# -----------------------------
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    open_check_attendance_window()
