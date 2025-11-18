# app.py
import cv2
import os
import json
import csv
import numpy as np
from PIL import Image
import sys
from datetime import datetime, date
from tkinter import *
from tkinter import messagebox, simpledialog, ttk

# ------------------------------
# EXE SUPPORT: resource_path()
# ------------------------------
def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# ------------------------------
# Paths & Ensure Folders/Files
# ------------------------------
data_folder = resource_path("Data")
resource_folder = resource_path("Resources")

os.makedirs(data_folder, exist_ok=True)
os.makedirs(resource_folder, exist_ok=True)

users_json = resource_path("users.json")
admins_json = resource_path("admins.json")
attendance_csv = resource_path("attendance.csv")
cascade_path = resource_path("Resources/haarcascade_frontalface_default.xml")
model_path = resource_path("Resources/dataset_model.xml")

# Create users.json if missing
if not os.path.exists(users_json):
    with open(users_json, "w") as f:
        json.dump({}, f)

# Create admins.json if missing (method B: admins.json editable)
if not os.path.exists(admins_json):
    # default admin: admin / 1234
    with open(admins_json, "w") as f:
        json.dump({"admin": "1234"}, f)

# Create attendance.csv if missing
if not os.path.exists(attendance_csv):
    with open(attendance_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["User ID", "Name", "Time"])


# ------------------------------
# Load Cascade (graceful if missing)
# ------------------------------
if not os.path.exists(cascade_path):
    # Try to find OpenCV's bundled cascade (if user didn't copy)
    try:
        import cv2 as _cv2
        cascade_path = os.path.join(os.path.dirname(_cv2.__file__), "data", "haarcascade_frontalface_default.xml")
    except Exception:
        cascade_path = None

if cascade_path is None or not os.path.exists(cascade_path):
    message = ("haarcascade_frontalface_default.xml not found.\n"
               "Place it in Resources/ or install opencv and/or copy the cascade file.")
    # If running as script, show messagebox; in headless build this still raises early.
    print(message)
    # Continue — functions will show errors when trying to use cascade
face_ref = cv2.CascadeClassifier(cascade_path) if cascade_path else None


# ------------------------------
# Helper: read users/admins/attendance
# ------------------------------
def load_users():
    with open(users_json, "r") as f:
        return json.load(f)

def load_admins():
    with open(admins_json, "r") as f:
        return json.load(f)

def read_attendance_rows():
    rows = []
    if os.path.exists(attendance_csv):
        with open(attendance_csv, "r", newline="") as f:
            reader = csv.reader(f)
            next(reader, None)
            for r in reader:
                rows.append(r)
    return rows

def append_attendance(user_id, name):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(attendance_csv, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([user_id, name, now])
    return now


# ------------------------------
# REGISTER FACE (open to all)
# ------------------------------
def register_face():
    if face_ref is None or face_ref.empty():
        messagebox.showerror("Error", "Face cascade not found. Put haarcascade_frontalface_default.xml in Resources/")
        return

    reg_win = Toplevel(app)
    reg_win.title("Register Face")
    reg_win.geometry("320x220")

    Label(reg_win, text="User ID:").pack(pady=(10,0))
    id_entry = Entry(reg_win); id_entry.pack()
    Label(reg_win, text="Name:").pack(pady=(6,0))
    name_entry = Entry(reg_win); name_entry.pack()

    def start_capture():
        user_id = id_entry.get().strip()
        user_name = name_entry.get().strip()
        if not user_id or not user_name:
            messagebox.showerror("Error", "ID dan Nama harus diisi")
            return

        users = load_users()
        users[user_id] = user_name
        with open(users_json, "w") as f:
            json.dump(users, f)

        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            messagebox.showerror("Camera Error", "Tidak dapat membuka kamera")
            return

        count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_ref.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                count += 1
                path = os.path.join(data_folder, f"User.{user_id}.{count}.jpg")
                cv2.imwrite(path, gray[y:y+h, x:x+w])
                cv2.rectangle(frame, (x,y),(x+w,y+h),(0,255,0),2)
            cv2.imshow("Register Face - Press Q to stop", frame)
            if cv2.waitKey(1) & 0xFF == ord("q") or count >= 50:
                break
        cap.release()
        cv2.destroyAllWindows()
        messagebox.showinfo("Success", f"Dataset selesai ({count} images) for {user_name}")
        reg_win.destroy()

    Button(reg_win, text="Start Capture", command=start_capture).pack(pady=12)


# ------------------------------
# TRAIN MODEL (admin-protected)
# ------------------------------
def train_model():
    if face_ref is None or face_ref.empty():
        messagebox.showerror("Error", "Face cascade not found.")
        return

    recognizer = cv2.face.LBPHFaceRecognizer_create()

    image_files = [f for f in os.listdir(data_folder) if f.lower().endswith((".jpg", ".jpg", ".jpeg"))]
    faces, ids = [], []
    for filename in image_files:
        try:
            img_pil = Image.open(os.path.join(data_folder, filename)).convert("L")
        except:
            continue
        img_np = np.array(img_pil, "uint8")
        try:
            user_id = int(filename.split(".")[1])
        except:
            continue
        det = face_ref.detectMultiScale(img_np)
        for (x,y,w,h) in det:
            faces.append(img_np[y:y+h, x:x+w])
            ids.append(user_id)

    if len(faces) == 0:
        messagebox.showerror("Error", "Tidak ada dataset untuk dilatih.")
        return

    recognizer.train(faces, np.array(ids))
    recognizer.save(model_path)
    messagebox.showinfo("Success", "Model training selesai!")


# ------------------------------
# ATTENDANCE (admin-protected for viewer; taking attendance open)
# Enforce one attendance per day rule
# ------------------------------
def attendance_system():
    if face_ref is None or face_ref.empty():
        messagebox.showerror("Error", "Face cascade not found.")
        return

    if not os.path.exists(model_path):
        messagebox.showerror("Error", "Model belum dilatih. Gunakan Train Model dulu.")
        return

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(model_path)
    users = load_users()

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        messagebox.showerror("Camera Error", "Tidak dapat membuka kamera")
        return

    messagebox.showinfo("Info", "Tekan Q untuk keluar. Sistem akan mencatat otomatis saat wajah dikenali.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detected = face_ref.detectMultiScale(gray, 1.3, 5)
        for (x,y,w,h) in detected:
            user_id, conf = recognizer.predict(gray[y:y+h, x:x+w])
            name = users.get(str(user_id), "Unknown")

            # check if already attended today
            rows = read_attendance_rows()
            today_str = date.today().isoformat()  # yyyy-mm-dd
            already = False
            for r in rows:
                if len(r) >= 3:
                    rid, rname, rtime = r[0], r[1], r[2]
                    if rid == str(user_id) and rtime.startswith(today_str):
                        already = True
                        break

            if already:
                cv2.putText(frame, f"{name} (Already today)", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255),2)
            else:
                now = append_attendance(user_id, name)
                cv2.putText(frame, f"{name} (OK)", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0),2)

            cv2.rectangle(frame, (x,y),(x+w,y+h),(255,0,0),2)

        cv2.imshow("Attendance - Press Q to quit", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


# ------------------------------
# ADMIN LOGIN -> opens a restricted admin panel
# ------------------------------
def admin_login():
    login_win = Toplevel(app)
    login_win.title("Admin Login")
    login_win.geometry("300x180")

    Label(login_win, text="Admin Username:").pack(pady=(10,0))
    user_entry = Entry(login_win); user_entry.pack()
    Label(login_win, text="Password:").pack(pady=(6,0))
    pass_entry = Entry(login_win, show="*"); pass_entry.pack()

    def do_login():
        uname = user_entry.get().strip()
        pwd = pass_entry.get().strip()
        admins = load_admins()
        if admins.get(uname) == pwd:
            login_win.destroy()
            open_admin_panel()
        else:
            messagebox.showerror("Login Failed", "Username atau password salah")

    Button(login_win, text="Login", command=do_login).pack(pady=12)


# ------------------------------
# ADMIN PANEL: Train + View Attendance
# ------------------------------
def open_admin_panel():
    panel = Toplevel(app)
    panel.title("Admin Panel")
    panel.geometry("700x500")

    Label(panel, text="Admin Panel", font=("Arial", 14)).pack(pady=8)

    # Buttons
    btn_frame = Frame(panel)
    btn_frame.pack(pady=6)
    Button(btn_frame, text="Train Model", command=train_model, width=18).pack(side=LEFT, padx=6)
    Button(btn_frame, text="Refresh View", command=lambda: populate_treeview(tree), width=14).pack(side=LEFT, padx=6)

    # Date filter
    filter_frame = Frame(panel)
    filter_frame.pack(pady=6, fill=X)
    Label(filter_frame, text="Filter date (YYYY-MM-DD):").pack(side=LEFT, padx=(6,4))
    date_entry = Entry(filter_frame); date_entry.pack(side=LEFT)
    Button(filter_frame, text="Apply", command=lambda: populate_treeview(tree, date_entry.get().strip())).pack(side=LEFT, padx=6)

    # Treeview for attendance
    cols = ("user_id", "name", "time")
    tree = ttk.Treeview(panel, columns=cols, show="headings")
    tree.heading("user_id", text="User ID")
    tree.heading("name", text="Name")
    tree.heading("time", text="Time")
    tree.pack(expand=True, fill=BOTH, padx=8, pady=8)

    populate_treeview(tree)


def populate_treeview(tree, date_filter=""):
    # clear
    for r in tree.get_children():
        tree.delete(r)
    rows = read_attendance_rows()
    # apply date filter if given
    for r in rows:
        if len(r) < 3:
            continue
        if date_filter:
            if not r[2].startswith(date_filter):
                continue
        tree.insert("", "end", values=(r[0], r[1], r[2]))


# ------------------------------
# MAIN GUI
# ------------------------------
app = Tk()
app.title("Face Recognition Attendance System")
app.geometry("420x300")

Label(app, text="Face Recognition Attendance", font=("Arial", 16)).pack(pady=14)

# Buttons: Register (open to all), Attendance (open to all), Admin login (train + viewer)
Button(app, text="Register Face", width=22, command=register_face).pack(pady=8)
Button(app, text="Attendance (Scan)", width=22, command=attendance_system).pack(pady=6)
Button(app, text="Admin Login (Train / Viewer)", width=22, command=admin_login).pack(pady=6)

Label(app, text="(Admins stored in admins.json)", font=("Arial", 8)).pack(pady=(10,0))

app.mainloop()
