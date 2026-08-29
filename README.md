# The Smart Skills Academy Qalagay — Fee Voucher System (Flask)

A complete, local-first fee voucher / student management and financial reporting system for
**The Smart Skills Academy Qalagay** — built with Flask, SQLite, HTML/CSS/JS.

Built by **Rashid Zada — Full Stack Developer**
📱 WhatsApp: **0347-0983567** — message him if you need similar software.

---

## ✨ Features

- 🔐 **Admin-only login** (default `admin` or `rashid` / `admin123`), change password anytime in Settings
- 👁️ **Privacy Eye Toggle (Default Hidden/OFF)** — 1-click button in top header and sidebar to mask/unmask all sensitive financial amounts across the system (`Rs. •••••` / real numbers)
- 📊 **Dashboard & Metrics** — total students, teachers, courses, total collected, pending dues, and expected revenue
- 📘 **Courses & Revenue Tracking** — tracks tuition fee, one-time fees (ID card, DMC, exam, fund), enrolled students, total collected, pending dues, and total expected revenue per course with grand totals
- 👩‍🏫 **Teachers Management & Dues** — add/remove staff, view courses taught, enrolled students, and total fee dues per teacher
- 🎓 **Students Management** — enroll students, pick course & teacher, choose 1–4 installments; automatic installment generation and full dues tracking
- 🧾 **Real Two-Copy Voucher Slips** — Office Copy + Student Copy on one A4 page for printing and PDF generation
- 🖨️ **Print & PDF Downloads** — server-side generated voucher slips and clearance certificates
- 💬 **WhatsApp 1-Click Sharing** — opens direct chat with student's WhatsApp number with customized voucher breakdown pre-filled
- 📥 **Comprehensive 5-Sheet Excel Export & Import** — full backup including:
  - **Summary**: Key KPI metrics, recovery rates, and academy financial overview
  - **Courses**: Fee structures, enrolled students, total collections, dues, and table totals
  - **Students**: Complete profiles, course fees, total paid, dues, and clearance statuses
  - **Payments**: Full installment schedule per student with breakdown and statuses
  - **Teachers**: Course assignments, students taught, revenue generated, and dues
- 100% **local** — runs on your own PC, data stored securely in a local database file (`college.db`)

---

## 🚀 Setup (Windows / macOS / Linux)

1. Install **Python 3.9+** if you don't already have it: https://python.org
2. Open a terminal in this folder and install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:

   ```bash
   python app.py
   ```

4. Open your browser at **http://127.0.0.1:5000**
5. Log in with:
   - Username: `admin`
   - Password: `admin123`
6. Go to **Settings** and change the password immediately.

The database file `college.db` is created automatically on first run in the
same folder — just back it up (or use the Excel export) to keep your records safe.

---

## 📖 How to use it

1. **Teachers** → add your teaching staff first.
2. **Courses** → add each course (e.g. CCTV, 4 Months) with its total fee and
   one-time charges (ID Card / DMC / Exam / Fund fees — these are only added to
   the **first** installment).
3. **Students** → enroll a student, pick their course & teacher, choose how many
   installments (1–4), and the installment schedule + due dates are generated instantly.
4. Open a student's page to see their **installment schedule**. Click **Slip** on any
   installment to open the voucher — from there you can **Print**, **Download PDF**,
   or **Send to Student's WhatsApp**.
5. **Dashboard** always shows the latest pending dues across all students.
6. **Import / Export** → download a full Excel backup any time, or bulk-import
   students/courses/teachers from a spreadsheet (use the exported file as a template).

---

## 💬 About the WhatsApp & SMS features

- The **WhatsApp button** on each voucher opens `wa.me` with the student's number and a
  ready-made message (fee amount, due date, etc.). This uses WhatsApp's free "click to
  chat" link — the **only** thing it cannot do automatically is attach the PDF file,
  because that requires a paid WhatsApp Business API subscription. Simply click
  **Download PDF** first, then attach it in the chat that opens — takes two clicks.
- Real **SMS sending** (e.g. via Twilio) needs a paid SMS gateway account with its own
  API keys. This app doesn't fabricate that connection, but `app.py` is structured so a
  `send_sms()` function can be dropped in easily once you have gateway credentials —
  message the developer above if you'd like this added.

---

## 🗂️ Project Structure

```
college_voucher_system/
├── app.py                  # Flask app: routes, DB, auth, Excel import/export
├── pdf_generator.py         # Builds the two-copy voucher PDF (ReportLab)
├── requirements.txt
├── college.db               # Created automatically (SQLite database)
├── templates/                # All HTML pages (Jinja2)
└── static/
    ├── css/style.css         # App styling
    └── js/script.js
```

---

## 🔒 Security notes for real-world use

- Change `app.secret_key` in `app.py` before deploying anywhere beyond your own PC.
- Change the default admin password immediately after first login.
- This app is designed to run **locally** on one office computer. If you want it
  accessible over the internet or by multiple staff members at once, it should be
  deployed behind a proper WSGI server (e.g. gunicorn) with HTTPS — contact the
  developer above for help setting that up.

---

Need a custom version of this software (multi-branch, SMS/WhatsApp Business API,
online fee payment, etc.)? Contact **Rashid Zada — Full Stack Developer**
📱 **WhatsApp: 0347-0983567**
