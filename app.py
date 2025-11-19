import cv2
import os
import json
import csv
import numpy as np
from PIL import Image as PILImage
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

# Create admins.json if missing
if not os.path.exists(admins_json):
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
    try:
        import cv2 as _cv2
        cascade_path = os.path.join(os.path.dirname(_cv2.__file__), "data", "haarcascade_frontalface_default.xml")
    except Exception:
        cascade_path = None

if cascade_path is None or not os.path.exists(cascade_path):
    message = ("haarcascade_frontalface_default.xml not found.\n"
               "Place it in Resources/ or install opencv and/or copy the cascade file.")
    print(message)

face_ref = cv2.CascadeClassifier(cascade_path) if cascade_path else None


# ------------------------------
# Helper: read users/admins/attendance
# ------------------------------
def load_users():
    with open(users_json, "r") as f:
        return json.load(f)

def save_users(users_dict):
    with open(users_json, "w") as f:
        json.dump(users_dict, f, indent=2)

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

def write_attendance_rows(rows):
    with open(attendance_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["User ID", "Name", "Time"])
        writer.writerows(rows)

def append_attendance(user_id, name):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(attendance_csv, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([user_id, name, now])
    return now


# ------------------------------
# Helper: Recursive click binding
# ------------------------------
def bind_click_recursive(widget, command):
    """Bind click event to widget and all its children"""
    widget.bind("<Button-1>", command)
    for child in widget.winfo_children():
        bind_click_recursive(child, command)

def update_bg_recursive(widget, color):
    """Update background color for widget and all children"""
    try:
        widget.config(bg=color)
    except:
        pass
    for child in widget.winfo_children():
        update_bg_recursive(child, color)


# ------------------------------
# DELETE USER FUNCTION
# ------------------------------
def delete_user(user_id, delete_attendance=False):
    """Delete user's face images, user record, and optionally attendance history"""
    users = load_users()
    
    if user_id not in users:
        return False, f"User ID {user_id} not found"
    
    user_name = users[user_id]
    deleted_files = 0
    
    # Delete face images
    for filename in os.listdir(data_folder):
        if filename.startswith(f"User.{user_id}.") and filename.endswith(".jpg"):
            try:
                os.remove(os.path.join(data_folder, filename))
                deleted_files += 1
            except Exception as e:
                print(f"Error deleting {filename}: {e}")
    
    # Remove from users.json
    del users[user_id]
    save_users(users)
    
    # Optionally delete attendance records
    deleted_records = 0
    if delete_attendance:
        rows = read_attendance_rows()
        filtered_rows = [r for r in rows if len(r) >= 1 and r[0] != user_id]
        deleted_records = len(rows) - len(filtered_rows)
        write_attendance_rows(filtered_rows)
    
    return True, f"Deleted user '{user_name}' (ID: {user_id})\n- {deleted_files} face images removed\n- {deleted_records} attendance records removed"


# ------------------------------
# REGISTER FACE
# ------------------------------
def register_face():
    if face_ref is None or face_ref.empty():
        messagebox.showerror("Error", "Face cascade not found. Put haarcascade_frontalface_default.xml in Resources/")
        return

    reg_win = Toplevel(app)
    reg_win.title("Register New User")
    reg_win.geometry("450x380")
    reg_win.configure(bg="#f0f0f0")
    
    # Center window
    reg_win.update_idletasks()
    x = (reg_win.winfo_screenwidth() // 2) - (450 // 2)
    y = (reg_win.winfo_screenheight() // 2) - (380 // 2)
    reg_win.geometry(f"450x380+{x}+{y}")

    # Header
    header = Frame(reg_win, bg="#2196F3", height=70)
    header.pack(fill=X)
    Label(header, text="📸 Register New User", font=("Segoe UI", 18, "bold"), 
          bg="#2196F3", fg="white").pack(pady=20)

    # Main content
    content = Frame(reg_win, bg="#f0f0f0")
    content.pack(fill=BOTH, expand=True, padx=30, pady=20)

    Label(content, text="User ID:", font=("Segoe UI", 11), bg="#f0f0f0", anchor="w").pack(fill=X, pady=(10,5))
    id_entry = Entry(content, font=("Segoe UI", 12), relief=SOLID, bd=1)
    id_entry.pack(fill=X, ipady=8)
    
    Label(content, text="Full Name:", font=("Segoe UI", 11), bg="#f0f0f0", anchor="w").pack(fill=X, pady=(15,5))
    name_entry = Entry(content, font=("Segoe UI", 12), relief=SOLID, bd=1)
    name_entry.pack(fill=X, ipady=8)

    info_frame = Frame(content, bg="#E3F2FD", relief=SOLID, bd=1)
    info_frame.pack(fill=X, pady=20)
    Label(info_frame, text="ℹ️ The camera will capture 50 images of your face.\nPress 'Q' to stop early.", 
          font=("Segoe UI", 9), bg="#E3F2FD", fg="#1976D2", justify=LEFT).pack(padx=10, pady=10)

    def start_capture():
        user_id = id_entry.get().strip()
        user_name = name_entry.get().strip()
        if not user_id or not user_name:
            messagebox.showerror("Error", "Please fill in both User ID and Name")
            return

        users = load_users()
        if user_id in users:
            if not messagebox.askyesno("User Exists", f"User ID {user_id} already exists. Overwrite?"):
                return
        
        users[user_id] = user_name
        save_users(users)

        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            messagebox.showerror("Camera Error", "Cannot open camera")
            return

        count = 0
        messagebox.showinfo("Ready", "Camera will start. Position your face in the frame.\nPress 'Q' to stop.")
        
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
                cv2.putText(frame, f"Captured: {count}/50", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
            
            cv2.putText(frame, "Press 'Q' to stop", (10, frame.shape[0]-20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
            cv2.imshow("Register Face", frame)
            
            if cv2.waitKey(1) & 0xFF == ord("q") or count >= 50:
                break
        
        cap.release()
        cv2.destroyAllWindows()
        messagebox.showinfo("Success", f"✓ Registration complete!\n\n{count} images captured for {user_name}\n\nReminder: Admin must train the model before attendance works.")
        reg_win.destroy()

    Button(content, text="Start Camera Capture", command=start_capture, 
           font=("Segoe UI", 12, "bold"), bg="#4CAF50", fg="white", 
           relief=FLAT, cursor="hand2", height=2).pack(fill=X, pady=(10,0))


# ------------------------------
# TRAIN MODEL
# ------------------------------
def train_model():
    if face_ref is None or face_ref.empty():
        messagebox.showerror("Error", "Face cascade not found.")
        return

    # Progress window
    progress_win = Toplevel(app)
    progress_win.title("Training Model")
    progress_win.geometry("400x200")
    progress_win.configure(bg="#f0f0f0")
    progress_win.transient(app)
    progress_win.grab_set()
    
    x = (progress_win.winfo_screenwidth() // 2) - 200
    y = (progress_win.winfo_screenheight() // 2) - 100
    progress_win.geometry(f"400x200+{x}+{y}")
    
    Label(progress_win, text="Training Model...", font=("Segoe UI", 14, "bold"), 
          bg="#f0f0f0").pack(pady=30)
    progress_label = Label(progress_win, text="Processing images...", 
                          font=("Segoe UI", 10), bg="#f0f0f0")
    progress_label.pack()
    
    progress_win.update()

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    image_files = [f for f in os.listdir(data_folder) if f.lower().endswith((".jpg", ".jpeg"))]
    faces, ids = [], []
    
    for idx, filename in enumerate(image_files):
        try:
            img_pil = PILImage.open(os.path.join(data_folder, filename)).convert("L")
        except Exception as e:
            print(f"Could not open {filename}: {e}")
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
        
        if idx % 10 == 0:
            progress_label.config(text=f"Processing: {idx+1}/{len(image_files)} images")
            progress_win.update()

    if len(faces) == 0:
        progress_win.destroy()
        messagebox.showerror("Error", "No training data found. Please register users first.")
        return

    progress_label.config(text="Training neural network...")
    progress_win.update()
    
    recognizer.train(faces, np.array(ids))
    recognizer.save(model_path)
    
    progress_win.destroy()
    messagebox.showinfo("Success", f"✓ Model trained successfully!\n\n{len(faces)} face samples processed\nSystem ready for attendance.")


# ------------------------------
# ATTENDANCE SYSTEM
# ------------------------------
def attendance_system():
    if face_ref is None or face_ref.empty():
        messagebox.showerror("Error", "Face cascade not found.")
        return

    if not os.path.exists(model_path):
        messagebox.showerror("Error", "Model not trained yet.\n\nPlease ask admin to train the model first.")
        return

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(model_path)
    users = load_users()

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        messagebox.showerror("Camera Error", "Cannot open camera")
        return

    messagebox.showinfo("Attendance Mode", "✓ Camera ready!\n\n• Position your face clearly\n• System will auto-detect and record\n• Press 'Q' to exit")

    recognized_users = set()  # Track who's been recognized this session

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detected = face_ref.detectMultiScale(gray, 1.3, 5)
        
        # Add instructions overlay
        cv2.putText(frame, "ATTENDANCE SYSTEM", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
        cv2.putText(frame, "Press 'Q' to exit", (10, frame.shape[0]-20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
        
        for (x,y,w,h) in detected:
            user_id, conf = recognizer.predict(gray[y:y+h, x:x+w])
            name = users.get(str(user_id), "Unknown")

            # Check if already attended today
            rows = read_attendance_rows()
            today_str = date.today().isoformat()
            already_today = False
            
            for r in rows:
                if len(r) >= 3:
                    if r[0] == str(user_id) and r[2].startswith(today_str):
                        already_today = True
                        break

            if name == "Unknown":
                cv2.rectangle(frame, (x,y),(x+w,y+h),(0,0,255),2)
                cv2.putText(frame, "Unknown", (x, y-10), 
                           cv2.FONT_HERSHEY_DUPLEX, 0.8, (0,0,255), 2)
            elif already_today:
                cv2.rectangle(frame, (x,y),(x+w,y+h),(255,165,0),2)
                cv2.putText(frame, f"{name} - Already recorded", (x, y-10), 
                           cv2.FONT_HERSHEY_DUPLEX, 0.7, (255,165,0), 2)
            else:
                # Record attendance only once per session
                if user_id not in recognized_users:
                    append_attendance(user_id, name)
                    recognized_users.add(user_id)
                
                cv2.rectangle(frame, (x,y),(x+w,y+h),(0,255,0),3)
                cv2.putText(frame, f"{name} - Recorded!", (x, y-10), 
                           cv2.FONT_HERSHEY_DUPLEX, 0.8, (0,255,0), 2)

        cv2.imshow("Attendance System", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    
    if recognized_users:
        messagebox.showinfo("Session Complete", f"✓ Attendance recorded for {len(recognized_users)} user(s)")


# ------------------------------
# DELETE USER WINDOW
# ------------------------------
def open_delete_user_window():
    del_win = Toplevel(app)
    del_win.title("Delete User")
    del_win.geometry("600x550")
    del_win.configure(bg="#f0f0f0")
    
    x = (del_win.winfo_screenwidth() // 2) - 300
    y = (del_win.winfo_screenheight() // 2) - 275
    del_win.geometry(f"600x550+{x}+{y}")

    # Header
    header = Frame(del_win, bg="#f44336", height=70)
    header.pack(fill=X)
    Label(header, text="🗑️ Delete User", font=("Segoe UI", 18, "bold"), 
          bg="#f44336", fg="white").pack(pady=20)

    users = load_users()
    if not users:
        Label(del_win, text="No users registered yet.", font=("Segoe UI", 12), 
              fg="#666", bg="#f0f0f0").pack(pady=50)
        return

    content = Frame(del_win, bg="#f0f0f0")
    content.pack(fill=BOTH, expand=True, padx=20, pady=20)

    Label(content, text="Select user to delete:", font=("Segoe UI", 11, "bold"), 
          bg="#f0f0f0").pack(anchor=W, pady=(0,10))

    # Listbox with scrollbar
    list_frame = Frame(content, relief=SOLID, bd=1)
    list_frame.pack(fill=BOTH, expand=True, pady=(0,15))

    scrollbar = Scrollbar(list_frame)
    scrollbar.pack(side=RIGHT, fill=Y)

    user_listbox = Listbox(list_frame, yscrollcommand=scrollbar.set, 
                          font=("Segoe UI", 10), relief=FLAT)
    user_listbox.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar.config(command=user_listbox.yview)

    user_items = []
    for uid, uname in sorted(users.items(), key=lambda x: x[0]):
        display_text = f"  ID: {uid:<8} | {uname}"
        user_listbox.insert(END, display_text)
        user_items.append(uid)

    # Options frame
    options_frame = Frame(content, bg="#FFF3E0", relief=SOLID, bd=1)
    options_frame.pack(fill=X, pady=(0,15))
    
    delete_attendance_var = BooleanVar(value=False)
    cb = Checkbutton(options_frame, text="⚠️ Also delete attendance history for this user", 
                    variable=delete_attendance_var, font=("Segoe UI", 10), 
                    bg="#FFF3E0", activebackground="#FFF3E0")
    cb.pack(anchor=W, padx=10, pady=10)

    def confirm_delete():
        selection = user_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a user to delete")
            return

        selected_uid = user_items[selection[0]]
        selected_name = users[selected_uid]

        confirm = messagebox.askyesno(
            "⚠️ Confirm Deletion",
            f"Delete this user?\n\nName: {selected_name}\nID: {selected_uid}\n\n" + 
            "This will remove:\n✗ All face images\n✗ User registration\n" + 
            ("✗ Attendance history\n" if delete_attendance_var.get() else "") +
            "\nThis action cannot be undone!"
        )

        if confirm:
            success, message = delete_user(selected_uid, delete_attendance_var.get())
            if success:
                messagebox.showinfo("Success", "✓ " + message)
                del_win.destroy()
                messagebox.showinfo("Reminder", "⚠️ Please retrain the model after deleting users!")
            else:
                messagebox.showerror("Error", message)

    # Buttons
    btn_frame = Frame(content, bg="#f0f0f0")
    btn_frame.pack(fill=X)
    
    Button(btn_frame, text="Delete Selected User", command=confirm_delete, 
           bg="#f44336", fg="white", font=("Segoe UI", 11, "bold"), 
           relief=FLAT, cursor="hand2", height=2).pack(side=LEFT, fill=X, expand=True, padx=(0,5))
    
    Button(btn_frame, text="Cancel", command=del_win.destroy, 
           bg="#757575", fg="white", font=("Segoe UI", 11), 
           relief=FLAT, cursor="hand2", height=2).pack(side=LEFT, fill=X, expand=True, padx=(5,0))


# ------------------------------
# ADMIN LOGIN
# ------------------------------
def admin_login():
    login_win = Toplevel(app)
    login_win.title("Admin Login")
    login_win.geometry("420x380")
    login_win.configure(bg="#f0f0f0")
    login_win.transient(app)
    login_win.grab_set()
    
    x = (login_win.winfo_screenwidth() // 2) - 210
    y = (login_win.winfo_screenheight() // 2) - 190
    login_win.geometry(f"420x380+{x}+{y}")

    # Header
    header = Frame(login_win, bg="#FF9800", height=80)
    header.pack(fill=X)
    Label(header, text="🔐 Admin Access", font=("Segoe UI", 20, "bold"), 
          bg="#FF9800", fg="white").pack(pady=25)

    content = Frame(login_win, bg="#f0f0f0")
    content.pack(fill=BOTH, expand=True, padx=40, pady=30)

    Label(content, text="Username:", font=("Segoe UI", 11), bg="#f0f0f0").pack(anchor=W, pady=(10,5))
    user_entry = Entry(content, font=("Segoe UI", 12), relief=SOLID, bd=1)
    user_entry.pack(fill=X, ipady=8)
    
    Label(content, text="Password:", font=("Segoe UI", 11), bg="#f0f0f0").pack(anchor=W, pady=(20,5))
    pass_entry = Entry(content, show="●", font=("Segoe UI", 12), relief=SOLID, bd=1)
    pass_entry.pack(fill=X, ipady=8)

    def do_login():
        uname = user_entry.get().strip()
        pwd = pass_entry.get().strip()
        admins = load_admins()
        if admins.get(uname) == pwd:
            login_win.destroy()
            open_admin_panel()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")
            pass_entry.delete(0, END)

    pass_entry.bind('<Return>', lambda e: do_login())

    Button(content, text="Login", command=do_login, 
           font=("Segoe UI", 12, "bold"), bg="#FF9800", fg="white", 
           relief=FLAT, cursor="hand2", height=2).pack(fill=X, pady=(30,10))
    
    Label(content, text="Default: admin / 1234", font=("Segoe UI", 8), 
          fg="#666", bg="#f0f0f0").pack()

    user_entry.focus()


# ------------------------------
# ADMIN PANEL
# ------------------------------
def open_admin_panel():
    panel = Toplevel(app)
    panel.title("Admin Control Panel")
    panel.geometry("900x650")
    panel.configure(bg="#f0f0f0")
    
    x = (panel.winfo_screenwidth() // 2) - 450
    y = (panel.winfo_screenheight() // 2) - 325
    panel.geometry(f"900x650+{x}+{y}")

    # Header
    header = Frame(panel, bg="#3F51B5", height=70)
    header.pack(fill=X)
    Label(header, text="⚙️ Admin Control Panel", font=("Segoe UI", 18, "bold"), 
          bg="#3F51B5", fg="white").pack(pady=20)

    content = Frame(panel, bg="#f0f0f0")
    content.pack(fill=BOTH, expand=True, padx=20, pady=20)

    # Action buttons
    btn_frame = Frame(content, bg="#f0f0f0")
    btn_frame.pack(fill=X, pady=(0,15))
    
    Button(btn_frame, text="🔄 Train Model", command=train_model, 
           font=("Segoe UI", 11, "bold"), bg="#4CAF50", fg="white", 
           relief=FLAT, cursor="hand2", height=2, width=15).pack(side=LEFT, padx=(0,10))
    
    Button(btn_frame, text="🗑️ Delete User", command=open_delete_user_window, 
           font=("Segoe UI", 11, "bold"), bg="#f44336", fg="white", 
           relief=FLAT, cursor="hand2", height=2, width=15).pack(side=LEFT, padx=(0,10))
    
    Button(btn_frame, text="🔃 Refresh", command=lambda: populate_treeview(tree), 
           font=("Segoe UI", 11), bg="#2196F3", fg="white", 
           relief=FLAT, cursor="hand2", height=2, width=12).pack(side=LEFT)

    # Filter section
    filter_frame = Frame(content, bg="#E8EAF6", relief=SOLID, bd=1)
    filter_frame.pack(fill=X, pady=(0,15))
    
    filter_inner = Frame(filter_frame, bg="#E8EAF6")
    filter_inner.pack(padx=15, pady=12)
    
    Label(filter_inner, text="📅 Filter by date:", font=("Segoe UI", 10, "bold"), 
          bg="#E8EAF6").pack(side=LEFT, padx=(0,10))
    
    date_entry = Entry(filter_inner, font=("Segoe UI", 10), width=15, relief=SOLID, bd=1)
    date_entry.pack(side=LEFT, padx=(0,10), ipady=4)
    date_entry.insert(0, date.today().isoformat())
    
    Button(filter_inner, text="Apply Filter", 
           command=lambda: populate_treeview(tree, date_entry.get().strip()),
           font=("Segoe UI", 9), bg="#3F51B5", fg="white", 
           relief=FLAT, cursor="hand2").pack(side=LEFT, padx=(0,10))
    
    Button(filter_inner, text="Clear Filter", 
           command=lambda: [date_entry.delete(0, END), populate_treeview(tree)],
           font=("Segoe UI", 9), bg="#757575", fg="white", 
           relief=FLAT, cursor="hand2").pack(side=LEFT)

    # Attendance records
    Label(content, text="📊 Attendance Records", font=("Segoe UI", 12, "bold"), 
          bg="#f0f0f0").pack(anchor=W, pady=(0,10))

    tree_frame = Frame(content, relief=SOLID, bd=1)
    tree_frame.pack(fill=BOTH, expand=True)

    # Scrollbars
    vsb = Scrollbar(tree_frame, orient="vertical")
    hsb = Scrollbar(tree_frame, orient="horizontal")
    
    # Treeview
    cols = ("user_id", "name", "time")
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings", 
                       yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    
    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)
    vsb.pack(side=RIGHT, fill=Y)
    hsb.pack(side=BOTTOM, fill=X)
    
    tree.heading("user_id", text="User ID")
    tree.heading("name", text="Name")
    tree.heading("time", text="Timestamp")
    
    tree.column("user_id", width=100, anchor=CENTER)
    tree.column("name", width=250)
    tree.column("time", width=200, anchor=CENTER)
    
    tree.pack(fill=BOTH, expand=True)

    # Style for treeview
    style = ttk.Style()
    style.configure("Treeview", font=("Segoe UI", 10), rowheight=28)
    style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    populate_treeview(tree)
    
    # Status bar
    status_frame = Frame(content, bg="#E0E0E0", height=30)
    status_frame.pack(fill=X, pady=(10,0))
    
    users = load_users()
    rows = read_attendance_rows()
    status_text = f"👥 Total Users: {len(users)}  |  📋 Total Records: {len(rows)}  |  📅 Today: {len([r for r in rows if len(r)>=3 and r[2].startswith(date.today().isoformat())])}"
    Label(status_frame, text=status_text, font=("Segoe UI", 9), 
          bg="#E0E0E0", fg="#424242").pack(pady=5)


def populate_treeview(tree, date_filter=""):
    # Clear existing
    for r in tree.get_children():
        tree.delete(r)
    
    rows = read_attendance_rows()
    count = 0
    
    for r in rows:
        if len(r) < 3:
            continue
        if date_filter and not r[2].startswith(date_filter):
            continue
        
        # Alternate row colors
        tag = 'evenrow' if count % 2 == 0 else 'oddrow'
        tree.insert("", "end", values=(r[0], r[1], r[2]), tags=(tag,))
        count += 1
    
    tree.tag_configure('evenrow', background='#f9f9f9')
    tree.tag_configure('oddrow', background='#ffffff')
    
    if count == 0 and date_filter:
        tree.insert("", "end", values=("", "No records found for this date", ""))


# ------------------------------
# MAIN GUI
# ------------------------------
app = Tk()
app.title("Face Recognition Attendance System")
app.geometry("600x700")
app.configure(bg="#f5f5f5")

# Center window
app.update_idletasks()
x = (app.winfo_screenwidth() // 2) - (600 // 2)
y = (app.winfo_screenheight() // 2) - (700 // 2)
app.geometry(f"600x700+{x}+{y}")

# Header Section
header = Frame(app, bg="#1976D2", height=120)
header.pack(fill=X)
header.pack_propagate(False)

Label(header, text="👤 Face Recognition", font=("Segoe UI", 24, "bold"), 
      bg="#1976D2", fg="white").pack(pady=(20,5))
Label(header, text="Attendance Management System", font=("Segoe UI", 14), 
      bg="#1976D2", fg="#E3F2FD").pack()

# Main content
content = Frame(app, bg="#f5f5f5")
content.pack(fill=BOTH, expand=True, padx=30, pady=30)

# Welcome message
welcome_frame = Frame(content, bg="#E3F2FD", relief=SOLID, bd=1)
welcome_frame.pack(fill=X, pady=(0,25))
Label(welcome_frame, text="Welcome! Choose an option below to get started", 
      font=("Segoe UI", 11), bg="#E3F2FD", fg="#1565C0").pack(pady=15)

# User section
Label(content, text="👥 User Functions", font=("Segoe UI", 13, "bold"), 
      bg="#f5f5f5", fg="#424242").pack(anchor=W, pady=(0,12))

user_frame = Frame(content, bg="#f5f5f5")
user_frame.pack(fill=X, pady=(0,20))

# ------------------------------
# REGISTER BUTTON (Clickable everywhere)
# ------------------------------
register_btn = Frame(user_frame, bg="white", relief=SOLID, bd=1, cursor="hand2")
register_btn.pack(fill=X, pady=(0,12))

def on_enter_register(e):
    update_bg_recursive(register_btn, "#E8F5E9")

def on_leave_register(e):
    update_bg_recursive(register_btn, "white")

register_btn.bind("<Enter>", on_enter_register)
register_btn.bind("<Leave>", on_leave_register)
bind_click_recursive(register_btn, lambda e: register_face())

register_icon = Label(register_btn, text="📸", font=("Segoe UI", 24), bg="white", cursor="hand2")
register_icon.pack(side=LEFT, padx=(20,15), pady=20)

info_frame = Frame(register_btn, bg="white", cursor="hand2")
info_frame.pack(side=LEFT, fill=BOTH, expand=True, pady=20)

Label(info_frame, text="Register New User", font=("Segoe UI", 13, "bold"), 
      bg="white", fg="#2E7D32", cursor="hand2").pack(anchor=W)
Label(info_frame, text="Capture face images for a new user", 
      font=("Segoe UI", 9), bg="white", fg="#666", cursor="hand2").pack(anchor=W)

# ------------------------------
# ATTENDANCE BUTTON (Clickable everywhere)
# ------------------------------
attend_btn = Frame(user_frame, bg="white", relief=SOLID, bd=1, cursor="hand2")
attend_btn.pack(fill=X)

def on_enter_attend(e):
    update_bg_recursive(attend_btn, "#E3F2FD")

def on_leave_attend(e):
    update_bg_recursive(attend_btn, "white")

attend_btn.bind("<Enter>", on_enter_attend)
attend_btn.bind("<Leave>", on_leave_attend)
bind_click_recursive(attend_btn, lambda e: attendance_system())

attend_icon = Label(attend_btn, text="✓", font=("Segoe UI", 28), bg="white", cursor="hand2")
attend_icon.pack(side=LEFT, padx=(20,15), pady=20)

info_frame2 = Frame(attend_btn, bg="white", cursor="hand2")
info_frame2.pack(side=LEFT, fill=BOTH, expand=True, pady=20)

Label(info_frame2, text="Mark Attendance", font=("Segoe UI", 13, "bold"), 
      bg="white", fg="#1976D2", cursor="hand2").pack(anchor=W)
Label(info_frame2, text="Scan your face to record attendance", 
      font=("Segoe UI", 9), bg="white", fg="#666", cursor="hand2").pack(anchor=W)

# Divider
Frame(content, height=2, bg="#E0E0E0").pack(fill=X, pady=25)

# Admin section
Label(content, text="⚙️ Administrator", font=("Segoe UI", 13, "bold"), 
      bg="#f5f5f5", fg="#424242").pack(anchor=W, pady=(0,12))

admin_frame = Frame(content, bg="#f5f5f5")
admin_frame.pack(fill=X)

# ------------------------------
# ADMIN BUTTON (Clickable everywhere)
# ------------------------------
admin_btn = Frame(admin_frame, bg="white", relief=SOLID, bd=1, cursor="hand2")
admin_btn.pack(fill=X)

def on_enter_admin(e):
    update_bg_recursive(admin_btn, "#FFF3E0")

def on_leave_admin(e):
    update_bg_recursive(admin_btn, "white")

admin_btn.bind("<Enter>", on_enter_admin)
admin_btn.bind("<Leave>", on_leave_admin)
bind_click_recursive(admin_btn, lambda e: admin_login())

admin_icon = Label(admin_btn, text="🔐", font=("Segoe UI", 24), bg="white", cursor="hand2")
admin_icon.pack(side=LEFT, padx=(20,15), pady=20)

info_frame3 = Frame(admin_btn, bg="white", cursor="hand2")
info_frame3.pack(side=LEFT, fill=BOTH, expand=True, pady=20)

Label(info_frame3, text="Admin Panel", font=("Segoe UI", 13, "bold"), 
      bg="white", fg="#F57C00", cursor="hand2").pack(anchor=W)
Label(info_frame3, text="Train model, manage users, view records", 
      font=("Segoe UI", 9), bg="white", fg="#666", cursor="hand2").pack(anchor=W)

# Footer
footer = Frame(app, bg="#EEEEEE", height=50)
footer.pack(side=BOTTOM, fill=X)
footer.pack_propagate(False)

Label(footer, text="💡 Tip: Register first, then admin must train model before attendance works", 
      font=("Segoe UI", 9), bg="#EEEEEE", fg="#616161").pack(pady=15)

app.mainloop()