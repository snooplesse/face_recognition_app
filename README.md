# Face Recognition Attendance System

A simple desktop application that uses **OpenCV**, **LBPH Face Recognition**, and **Tkinter GUI** to register faces, train a model, and record attendance automatically using face scanning.

---

## 📌 Features

### 👤 1. Register Face
- Capture up to 50 face images per user.
- Images stored in `/Data/` folder automatically.
- User IDs and names stored in `users.json`.

### 🧠 2. Train Model (Admin Only)
- Uses **LBPHFaceRecognizer**.
- Trains from dataset inside `/Data/`.
- Saves model as:  
  ```
  /Resources/dataset_model.xml
  ```

### 📸 3. Live Attendance (Face Recognition)
- Detects and identifies faces from webcam.
- Records attendance in:
  ```
  attendance.csv
  ```
- Automatically prevents double attendance on the same day.

### 🔐 4. Admin Login
- Credentials stored in `admins.json`
- Admin menu can:
  - Train model
  - View attendance with date filter

---

## 📂 Folder Structure

```
face_recognition_app/
│
├── app.py
├── users.json
├── admins.json
├── attendance.csv
│
├── Data/                 ← dataset wajah tersimpan
│    └── User.<id>.<n>.jpg
│
├── Resources/
│    ├── haarcascade_frontalface_default.xml
│    └── dataset_model.xml (auto-generated after training)
│
└── README.md
```

---

## 💻 Requirements

Install dependencies from `requirements.txt`:

```
pip install -r requirements.txt
```

Libraries:
- opencv-python
- opencv-contrib-python
- pillow
- numpy
- tkinter (built-in on Windows)
- json & csv (built-in)

---

## ▶️ Running the App

```
python app.py
```

---

## 🧪 Training Notes (Important)

To avoid error:

```
AttributeError: module 'cv2.face' has no attribute 'LBPHFaceRecognizer_create'
```

You **must install OpenCV Contrib**, not the regular OpenCV.

Install:

```
pip uninstall opencv-python -y
pip install opencv-contrib-python
```

---

## 🍎 Packaging to EXE (PyInstaller)

```
pyinstaller --noconsole --onefile --add-data "Resources;Resources" app.py
```

Check final EXE inside `/dist/`.

---

## 📝 Author

Created by **Adji Bayu**  
Face Recognition Attendance System

---

## 📜 License

This project is open-source. You may modify or distribute it freely.
