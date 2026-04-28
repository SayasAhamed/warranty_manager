# 📄 Warranty Manager System 

A fully-featured **desktop-based Warranty & Invoice Management System** built using **Python + PyQt6**, designed for real-world business workflows.

This system handles invoice tracking, warranty lifecycle automation, PDF stamping, and secure user management — all within a modern GUI.

---

## 🔥 Core Features

### 🖥️ Full Desktop GUI

* Built with **PyQt6**
* Clean, modern interface with tabs and dashboards 
* Login screen with background & branding 
<br>
<div>
  <img src="Screenshots\login.png">
</div>
<br>
---

### 🔐 Authentication System

* Secure login system
* Password hashing using PBKDF2
* Role-based access (Admin/User)
* Forgot password with security questions

<br>
<div>
  <img src="Screenshots\user management.png">
</div>
<br>

---

### 📂 Invoice Management

* Import multiple PDF invoices
* Auto-organize into folders:

  * `NonPaid`
  * `Paid`
  * `Warranty Ended`
* Safe file naming & duplicate handling

<br>
<div>
  <img src="Screenshots\Add Invoice.png">
  <img src="Screenshots\Non-paid.png">
  <img src="Screenshots\paid.png">
  <img src="Screenshots\under warranty.png">
</div>
<br>

---

### 📅 Warranty Automation

* Calculates warranty duration
* Tracks:

  * Active warranties
  * Expired warranties
* Automatically moves expired invoices

---

### ✅ Payment Processing

* Mark invoices as **PAID**
* Automatically:

  * Adds watermark
  * Adds seal
  * Adds payment date

<br>
<div>
  <img src="Screenshots\paid Seal.png">
</div>
<br>

---

### 🔖 Warranty Expiry System

* Adds **WARRANTY ENDED** seal
* Moves expired invoices automatically
* Background maintenance process

<br>
<div>
  <img src="Screenshots\Warranty Ended.png">
</div>
<br>

---

### 📊 Admin Panel

* Add / delete users
* Reset passwords
* Edit usernames
* View all users

---

### 🧮 Warranty Calculator Tool

* Standalone calculator window
* Shows:

  * End date
  * Remaining days
  * Status (Active / Expired)

---

### 📜 Logging System

* Rotating log files
* Tracks:

  * App startup
  * Database initialization
  * User login

---
### ## 🔐 Default Login Credentials

You can use the following default accounts to access the system:

### 👑 Admin Account

* **Username:** admin
* **Password:** admin123

👉 Full access (Admin Panel, User Management, All Features)

---

### 👤 User Account

* **Username:** user
* **Password:** user

👉 Limited access (Invoice Management & Warranty Tracking)

---

> ⚠️ For security, it is recommended to change these credentials after first login.


👉 Implemented in: 2025 - 2026    

---

## 🛠️ Tech Stack

* 🐍 Python
* 🖥️ PyQt6 (GUI) 
* 🗄️ SQLite Database
* 📄 PyPDF2 (PDF reading) 
* 🧾 ReportLab (PDF stamping) 
* 🔐 PBKDF2 (Password hashing)

---

## 📁 Project Structure

```id="w3l9f8"
Warranty-Manager/
│
├── actions/
│   ├── db_actions.py
│   ├── invoice_actions.py
│   ├── pdf_actions.py
│   └── warranty_actions.py
│
├── gui/
│   ├── main_app.py
│   └── login.py
│
├── assets/
│   ├── business_logo.png
│   ├── paid_logo.png
│   └── warranty_end_seal.png
│
├── invoices/
│   ├── NonPaid/
│   ├── Paid/
│   └── Warranty Ended/
│
├── logs/
│   └── app.log
│
├── main.py
├── requirements.txt
└── warranty_manager.db
```

---

## ⚙️ Installation

### 1️⃣ Clone Repository

```bash id="kz3d9s"
git clone https://github.com/SayasAhamed/Warranty-Manager.git
cd Warranty-Manager
```

---

### 2️⃣ Install Dependencies

```bash id="6p0v3m"
pip install -r requirements.txt
```

---

### 3️⃣ Run Application

```bash id="b6j2xa"
python main.py
```

---

## 🔐 Default Login

```id="k9z1xq"
Username: admin
Password: admin123
```

---

## 🧪 Debug & Testing Scripts

### Check Login System

```bash id="h9d8fp"
python check_login.py
```

👉 Validates users & login credentials 

---

### Reset Admin Password

```bash id="2f0l3k"
python verify_admin.py
```

👉 Forces admin password reset 

---

## ⚡ System Workflow

```id="x9v2lm"
Login → Dashboard
      ↓
Import Invoice PDF
      ↓
Store in Database + Folder
      ↓
Track Warranty Period
      ↓
Mark as Paid → Apply Stamp
      ↓
Warranty Expired → Auto Move + Stamp
```

---

## 📸 Screenshots

> ⚠️ Add screenshots here (UI, dashboard, login, etc.)

---

## 🚧 Future Improvements

* ☁️ Cloud database integration
* 📱 Mobile version
* 🔔 Email/SMS notifications
* 📊 Analytics dashboard
* 🤖 AI-based invoice data extraction

---

## 👨‍💻 Author

**M.M. Sayas Ahamed**
🎓 Undergraduate | BICT
💻 Developer | Tech Creator

---

## ⭐ Support

If you like this project:

* ⭐ Star this repo
* 🍴 Fork it
* 🛠️ Contribute

---

## 📄 License

This project is for educational and personal use.
