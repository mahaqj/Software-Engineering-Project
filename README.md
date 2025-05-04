# SupplyCraft: A Warehouse Inventory Management System  
### CS3009: Software Engineering Project  
**Developed by Amna Amir & Maha Qaiser**

![image](https://github.com/user-attachments/assets/799f94c0-4646-41d0-8552-7c2f4d353cb4)

This is a Django-based web application designed to streamline inventory management between  a **warehouse manager** and **restaurant managers**.

Follow the steps below to run the project locally on your machine.

### Step 1: Unzip the Archive

Unzip the project archive you downloaded or cloned.

### Step 2: Open in Code Editor

Open the folder `Software-Engineering-Project` in a code editor such as [Visual Studio Code](https://code.visualstudio.com/).

### Step 3: Run the Server

In the terminal, execute the following commands:

```bash
.\env\Scripts\activate
cd backend
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

### Step 4: Access the App

Visit [http://127.0.0.1:8000/login](http://127.0.0.1:8000/login) in your browser.

- Create an account as a **restaurant manager**.
- Note: Your account must be **approved by a warehouse manager** before you can log in.

### Optional (First-Time Setup Only)

If you're running the project for the first time and no warehouse manager account exists:

1. Go to [http://127.0.0.1:8000/warehouse_signup/](http://127.0.0.1:8000/warehouse_signup/)
2. Create a **warehouse manager** account.
 - Note: Only **one** warehouse manager account is allowed.

---

## Features

- Restaurant Manager Signup/Login
- Food Item Management (Add/Edit/Delete)
- Order Placement & Tracking
- Inventory Restocking
- Billing & Payment Reports
- Notification System

---

## Tech Stack

- **Backend**: Django (Python)
- **Frontend**: HTML, CSS (via Django templates)
- **Database**: SQLite (default with Django)

---

