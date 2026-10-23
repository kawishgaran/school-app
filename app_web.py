import sys
import sqlite3
import shutil
import os
import re
import jdatetime
from PyQt6.QtWidgets import (
QApplication, QMainWindow, QWidget, QLabel, QLineEdit,
QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox, QTabWidget,
QTableWidget, QTableWidgetItem, QComboBox, QGroupBox,
QGridLayout, QCheckBox, QHeaderView, QScrollArea, QDialog, QFileDialog, QTextBrowser, QMenu
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QWheelEvent, QTextDocument, QShortcut, QKeySequence, QCursor
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

==============================================================================

1. CUSTOM WIDGETS & DATABASE INITIALIZATION

==============================================================================

class ZoomableLineEdit(QLineEdit):
"""
Custom QLineEdit supporting Ctrl+MouseWheel zoom and automated text alignment based on character set.
"""
def init(self, text="", parent=None):
super().init(text, parent)
self.zoom_level = 13
self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
self.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
self.textChanged.connect(self.update_text_alignment)
self.update_style()
if text:
self.update_text_alignment(text)

def update_text_alignment(self, text):
    self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    clean_text = text.strip()
    if not clean_text:
        self.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return
    first_char = clean_text[0]
    if re.search(r'[a-zA-Z0-9]', first_char) and not re.search(r'[\u0600-\u06FF]', first_char):
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    else:
        self.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

def update_style(self):
    self.setStyleSheet(f"""
        QLineEdit {{
            font-size: {self.zoom_level}px; 
            padding: 6px 10px; 
            border: 1.5px solid #1976d2; 
            border-radius: 8px; 
            background-color: #ffffff; 
            color: #2c3e50;
            selection-background-color: #1976d2;
            selection-color: #ffffff;
        }}
        QLineEdit:focus {{
            border: 2.5px solid #d32f2f;
            background-color: #fff8e1;
        }}
    """)

def wheelEvent(self, event: QWheelEvent):
    if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
        if event.angleDelta().y() > 0:
            self.zoom_level = min(22, self.zoom_level + 2)
        else:
            self.zoom_level = max(10, self.zoom_level - 2)
        self.update_style()
        event.accept()
    else:
        super().wheelEvent(event)


def init_db():
conn = sqlite3.connect("school_finance.db")
cursor = conn.cursor()

# Users Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL
    )
''')

# Students Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_no TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        father_name TEXT NOT NULL,
        grandfather_name TEXT NOT NULL,
        class_name TEXT NOT NULL,
        standard_fee REAL NOT NULL,
        is_free INTEGER DEFAULT 0,
        father_phone TEXT DEFAULT '',
        mother_phone TEXT DEFAULT '',
        uses_transport INTEGER DEFAULT 0,
        transport_route TEXT DEFAULT '',
        transport_fee REAL DEFAULT 0,
        takes_books INTEGER DEFAULT 0,
        books_fee REAL DEFAULT 0,
        books_payment_status TEXT DEFAULT 'پرداخت شده',
        takes_uniform INTEGER DEFAULT 0,
        uniform_fee REAL DEFAULT 0,
        uniform_payment_status TEXT DEFAULT 'پرداخت شده',
        initial_previous_debt REAL DEFAULT 0,
        initial_tuition_debt REAL DEFAULT 0,
        initial_books_debt REAL DEFAULT 0,
        initial_uniform_debt REAL DEFAULT 0,
        initial_transport_debt REAL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'فعال',
        registration_date TEXT DEFAULT ''
    )
''')

# Student Breaks / Leaves Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS student_breaks (
        break_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        start_month TEXT NOT NULL,
        end_month TEXT NOT NULL,
        reason TEXT,
        FOREIGN KEY(student_id) REFERENCES students(student_id)
    )
''')

# Daily Attendance Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        date TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY(student_id) REFERENCES students(student_id)
    )
''')

# Student Evaluation Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS evaluations (
        evaluation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        date TEXT NOT NULL,
        notebook_check INTEGER DEFAULT 0,
        diary_check INTEGER DEFAULT 0,
        dictation INTEGER DEFAULT 0,
        learning_level INTEGER DEFAULT 0,
        homework INTEGER DEFAULT 0,
        other_cases INTEGER DEFAULT 0,
        total_score INTEGER DEFAULT 0,
        FOREIGN KEY(student_id) REFERENCES students(student_id)
    )
''')

# Staff / Teachers Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS staff (
        staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
        staff_no TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        role_type TEXT NOT NULL,
        phone TEXT DEFAULT '',
        salary REAL DEFAULT 0,
        registration_date TEXT DEFAULT ''
    )
''')

# Staff Payments Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS staff_payments (
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        staff_id INTEGER,
        date TEXT NOT NULL,
        trans_type TEXT DEFAULT 'پرداخت حقوق',
        amount REAL NOT NULL,
        description TEXT,
        user_name TEXT,
        FOREIGN KEY(staff_id) REFERENCES staff(staff_id)
    )
''')

# Student Payments Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS student_payments (
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        date TEXT NOT NULL,
        trans_type TEXT DEFAULT 'دریافت وجه',
        fee_type TEXT NOT NULL,
        amount REAL NOT NULL,
        description TEXT,
        user_name TEXT,
        FOREIGN KEY(student_id) REFERENCES students(student_id)
    )
''')

# Cashbox Log Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS cashbox (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        type TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        description TEXT,
        user_name TEXT DEFAULT ''
    )
''')

# Settings Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
''')

# Classes Master List
cursor.execute('''
    CREATE TABLE IF NOT EXISTS classes (
        class_id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_name TEXT UNIQUE NOT NULL
    )
''')

# Expense Categories Master List
cursor.execute('''
    CREATE TABLE IF NOT EXISTS expense_categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name TEXT UNIQUE NOT NULL
    )
''')

# Seed default users
cursor.execute("SELECT COUNT(*) FROM users")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO users (username, password, full_name, role) VALUES ('admin', 'admin123', 'مدیر کل سیستم', 'Admin')")
    cursor.execute("INSERT INTO users (username, password, full_name, role) VALUES ('finance', 'finance123', 'مدیر مالی', 'Financial_Manager')")

# Seed default classes
cursor.execute("SELECT COUNT(*) FROM classes")
if cursor.fetchone()[0] == 0:
    default_classes = ["صنف اول", "صنف دوم", "صنف سوم", "صنف چهارم", "صنف پنجم", "صنف ششم", "صنف هفتم", "صنف هشتم", "صنف نهم", "صنف دهم", "صنف یازدهم", "صنف دوازدهم", "آمادگی"]
    for c in default_classes:
        cursor.execute("INSERT OR IGNORE INTO classes (class_name) VALUES (?)", (c,))

# Seed default expense categories
cursor.execute("SELECT COUNT(*) FROM expense_categories")
if cursor.fetchone()[0] == 0:
    default_cats = ["خرید وسایل و تجهیزات", "ترمیم وسایط و موترها", "مصارف برق و آب", "لوازم‌التحریر", "سایر مصارف"]
    for cat in default_cats:
        cursor.execute("INSERT OR IGNORE INTO expense_categories (category_name) VALUES (?)", (cat,))

conn.commit()
conn.close()


def get_setting(key, default=""):
conn = sqlite3.connect("school_finance.db")
cursor = conn.cursor()
cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
row = cursor.fetchone()
conn.close()
return row[0] if row else default

def set_setting(key, value):
conn = sqlite3.connect("school_finance.db")
cursor = conn.cursor()
cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
conn.commit()
conn.close()

def parse_shamsi_date(date_str):
try:
clean_str = date_str.replace('-', '/').strip()
parts = clean_str.split('/')
if len(parts) >= 3:
return int(parts[0]), int(parts[1]), int(parts[2])
elif len(parts) == 2:
return int(parts[0]), int(parts[1]), 1
except:
pass
return None, None, None

def calculate_active_months(student_id, reg_date_str):
ry, rm, rd = parse_shamsi_date(reg_date_str)
if not ry or not rm:
return 1

now = jdatetime.date.today()
current_y, current_m, current_d = now.year, now.month, now.day

total_months_passed = (current_y - ry) * 12 + (current_m - rm)
if current_d >= 29:
    total_months_passed += 1

if total_months_passed < 1:
    total_months_passed = 1

conn = sqlite3.connect("school_finance.db")
cursor = conn.cursor()
cursor.execute("SELECT start_month, end_month FROM student_breaks WHERE student_id = ?", (student_id,))
break_ranges = cursor.fetchall()
conn.close()

total_break_months = 0
for b_start, b_end in break_ranges:
    sy, sm, _ = parse_shamsi_date(b_start)
    ey, em, _ = parse_shamsi_date(b_end)
    if sy and sm and ey and em:
        b_months = (ey - sy) * 12 + (em - sm)
        if b_months <= 0:
            b_months = 1
        total_break_months += b_months

active = total_months_passed - total_break_months
return max(0, active)


==============================================================================

2. LOGIN DIALOG & CUSTOMIZATION

==============================================================================

class LoginDialog(QDialog):
def init(self):
super().init()
self.setWindowTitle("ورود به سیستم - مکتب خصوصی کاوشگران دانش بلخ")
self.showMaximized()
self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
self.setFont(QFont("Tahoma", 12))

    main_layout = QVBoxLayout(self)
    main_layout.setContentsMargins(0, 0, 0, 0)
    
    self.bg_container = QWidget(self)
    self.update_background_style()
    
    container_layout = QVBoxLayout(self.bg_container)
    container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    card = QWidget()
    card.setFixedSize(420, 500)
    card.setStyleSheet("QWidget { background-color: rgba(255, 255, 255, 0.96); border-radius: 18px; }")
    
    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(35, 30, 35, 30)
    card_layout.setSpacing(12)
    
    icon_label = QLabel("🏫")
    icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon_label.setStyleSheet("font-size: 45px; background: transparent;")
    card_layout.addWidget(icon_label)
    
    title_label = QLabel("مکتب خصوصی کاوشگران دانش بلخ")
    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title_label.setStyleSheet("font-size: 17px; font-weight: bold; color: #0d47a1; background: transparent;")
    card_layout.addWidget(title_label)
    
    subtitle = QLabel("سیستم جامع مدیریت مالی و اداری")
    subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
    subtitle.setStyleSheet("font-size: 12px; color: #546e7a; margin-bottom: 10px; background: transparent;")
    card_layout.addWidget(subtitle)
    
    lbl_user = QLabel("👤 نام کاربری")
    lbl_user.setStyleSheet("font-size: 12px; font-weight: bold; color: #2c3e50; background: transparent;")
    self.txt_user = ZoomableLineEdit()
    self.txt_user.setPlaceholderText("نام کاربری را وارد کنید...")
    card_layout.addWidget(lbl_user)
    card_layout.addWidget(self.txt_user)
    
    lbl_pass = QLabel("🔒 رمز عبور")
    lbl_pass.setStyleSheet("font-size: 12px; font-weight: bold; color: #2c3e50; background: transparent;")
    self.txt_pass = ZoomableLineEdit()
    self.txt_pass.setPlaceholderText("رمز عبور را وارد کنید...")
    self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
    card_layout.addWidget(lbl_pass)
    card_layout.addWidget(self.txt_pass)
    
    btn_login = QPushButton("ورود به سیستم")
    btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_login.setStyleSheet("QPushButton { background-color: #0d47a1; color: white; font-weight: bold; font-size: 14px; padding: 10px; border-radius: 8px; margin-top: 10px; } QPushButton:hover { background-color: #1565c0; }")
    btn_login.clicked.connect(self.handle_login)
    card_layout.addWidget(btn_login)

    btn_bg = QPushButton("🖼️ تغییر تصویر پس‌زمینه")
    btn_bg.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_bg.setStyleSheet("QPushButton { background-color: transparent; color: #546e7a; font-size: 11px; border: none; margin-top: 2px; } QPushButton:hover { color: #0d47a1; text-decoration: underline; }")
    btn_bg.clicked.connect(self.change_login_background)
    card_layout.addWidget(btn_bg)
    
    container_layout.addWidget(card)
    main_layout.addWidget(self.bg_container)
    self.user_info = None

def update_background_style(self):
    bg_path = get_setting("login_bg", "")
    if bg_path and os.path.exists(bg_path):
        self.bg_container.setStyleSheet(f"background-image: url('{bg_path}'); background-position: center; background-repeat: no-repeat; background-size: cover;")
    else:
        self.bg_container.setStyleSheet("background: linear-gradient(135deg, #0d47a1 0%, #1e3c72 100%);")

def change_login_background(self):
    file_path, _ = QFileDialog.getOpenFileName(self, "انتخاب تصویر پس‌زمینه", "", "Image Files (*.png *.jpg *.jpeg)")
    if file_path:
        set_setting("login_bg", file_path)
        self.update_background_style()
        QMessageBox.information(self, "موفقیت", "تصویر پس‌زمینه با موفقیت تغییر کرد.")
    
def handle_login(self):
    u = self.txt_user.text().strip()
    p = self.txt_pass.text().strip()
    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT full_name, role FROM users WHERE username = ? AND password = ?", (u, p))
    user = cursor.fetchone()
    conn.close()
    if user:
        self.user_info = user
        self.accept()
    else:
        QMessageBox.warning(self, "خطا", "نام کاربری یا رمز عبور اشتباه است!")


==============================================================================

3. STUDENT PROFILE & EDITING DIALOGS

==============================================================================

class EditStudentDialog(QDialog):
def init(self, student_id, parent=None):
super().init(parent)
self.student_id = student_id
self.setWindowTitle("ویرایش مشخصات دانش‌آموز")
self.resize(600, 700)
self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
self.setFont(QFont("Tahoma", 12))

    layout = QVBoxLayout(self)
    grid = QGridLayout()
    
    self.txt_no = ZoomableLineEdit()
    self.txt_name = ZoomableLineEdit()
    self.txt_father = ZoomableLineEdit()
    self.txt_gfather = ZoomableLineEdit()
    self.combo_class = QComboBox()
    self.txt_fee = ZoomableLineEdit()
    
    self.chk_free = QCheckBox("شاگرد رایگان (معاف از شهریه)")
    self.chk_free.setStyleSheet("font-weight: bold; color: #2e7d32; font-size: 13px;")
    self.chk_free.toggled.connect(self.toggle_free_status)

    self.txt_fphone = ZoomableLineEdit()
    self.txt_mphone = ZoomableLineEdit()
    self.txt_prev_debt = ZoomableLineEdit()
    self.txt_reg_date = ZoomableLineEdit()

    self.load_classes()

    grid.addWidget(QLabel("آی‌دی:"), 0, 0); grid.addWidget(self.txt_no, 0, 1)
    grid.addWidget(QLabel("نام کامل:"), 1, 0); grid.addWidget(self.txt_name, 1, 1)
    grid.addWidget(QLabel("نام پدر:"), 2, 0); grid.addWidget(self.txt_father, 2, 1)
    grid.addWidget(QLabel("نام پدرکلان:"), 3, 0); grid.addWidget(self.txt_gfather, 3, 1)
    grid.addWidget(QLabel("صنف:"), 4, 0); grid.addWidget(self.combo_class, 4, 1)
    grid.addWidget(QLabel("شهریه ماهانه:"), 5, 0); grid.addWidget(self.txt_fee, 5, 1)
    grid.addWidget(self.chk_free, 6, 0, 1, 2)
    grid.addWidget(QLabel("تلفن پدر:"), 7, 0); grid.addWidget(self.txt_fphone, 7, 1)
    grid.addWidget(QLabel("تلفن مادر:"), 8, 0); grid.addWidget(self.txt_mphone, 8, 1)
    grid.addWidget(QLabel("باقی‌داری قبلی:"), 9, 0); grid.addWidget(self.txt_prev_debt, 9, 1)
    grid.addWidget(QLabel("تاریخ ثبت‌نام:"), 10, 0); grid.addWidget(self.txt_reg_date, 10, 1)

    layout.addLayout(grid)

    btn_save = QPushButton("💾 ذخیره تغییرات")
    btn_save.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 10px; border-radius: 8px;")
    btn_save.clicked.connect(self.save_changes)
    layout.addWidget(btn_save)

    self.load_student_data()

def toggle_free_status(self, checked):
    if checked:
        self.txt_fee.setText("0")
        self.txt_fee.setEnabled(False)
    else:
        self.txt_fee.setEnabled(True)

def load_classes(self):
    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT class_name FROM classes")
    classes = [r[0] for r in cursor.fetchall()]
    conn.close()
    self.combo_class.addItems(classes)

def load_student_data(self):
    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT student_no, full_name, father_name, grandfather_name, class_name, standard_fee, is_free, father_phone, mother_phone, initial_previous_debt, registration_date
        FROM students WHERE student_id = ?
    ''', (self.student_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        self.txt_no.setText(str(row[0]))
        self.txt_name.setText(str(row[1]))
        self.txt_father.setText(str(row[2]))
        self.txt_gfather.setText(str(row[3]))
        self.combo_class.setCurrentText(str(row[4]))
        self.txt_fee.setText(str(row[5]))
        is_f = row[6]
        if is_f == 1:
            self.chk_free.setChecked(True)
            self.txt_fee.setText("0")
            self.txt_fee.setEnabled(False)
        self.txt_fphone.setText(str(row[7]))
        self.txt_mphone.setText(str(row[8]))
        self.txt_prev_debt.setText(str(row[9]))
        self.txt_reg_date.setText(str(row[10]))

def save_changes(self):
    no = self.txt_no.text().strip()
    name = self.txt_name.text().strip()
    is_free = 1 if self.chk_free.isChecked() else 0
    fee = 0.0 if is_free else float(self.txt_fee.text().strip() or 0)
    reg_date = self.txt_reg_date.text().strip()
    
    if not no or not name or not reg_date:
        QMessageBox.warning(self, "خطا", "اطلاعات ضروری نباید خالی باشند.")
        return

    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE students SET student_no=?, full_name=?, father_name=?, grandfather_name=?, class_name=?, standard_fee=?, is_free=?, father_phone=?, mother_phone=?, initial_previous_debt=?, registration_date=?
        WHERE student_id=?
    ''', (no, name, self.txt_father.text().strip(), self.txt_gfather.text().strip(), self.combo_class.currentText(), fee, is_free, self.txt_fphone.text().strip(), self.txt_mphone.text().strip(), float(self.txt_prev_debt.text().strip() or 0), reg_date, self.student_id))
    conn.commit(); conn.close()
    QMessageBox.information(self, "موفقیت", "اطلاعات دانش‌آموز ویرایش شد.")
    self.accept()


class StudentProfileWindow(QDialog):
def init(self, student_id, user_full_name, parent=None):
super().init(parent)
self.student_id = student_id
self.user_full_name = user_full_name
self.setWindowTitle("پرونده و حساب مالی دانش‌آموز")
self.resize(1100, 850)
self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
self.setFont(QFont("Tahoma", 13))

    scroll = QScrollArea(); scroll.setWidgetResizable(True)
    self.content_widget = QWidget()
    self.layout = QVBoxLayout(self.content_widget)
    self.layout.setContentsMargins(20, 20, 20, 20)
    
    self.load_student_info()
    scroll.setWidget(self.content_widget)
    main_layout = QVBoxLayout(self); main_layout.addWidget(scroll)
    self.setLayout(main_layout)

def load_student_info(self):
    while self.layout.count():
        item = self.layout.takeAt(0)
        if item.widget(): item.widget().deleteLater()

    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT student_no, full_name, father_name, grandfather_name, class_name, standard_fee, is_free, 
               uses_transport, transport_fee, father_phone,
               initial_previous_debt, initial_tuition_debt, initial_books_debt, initial_uniform_debt, initial_transport_debt, registration_date
        FROM students WHERE student_id = ?
    ''', (self.student_id,))
    s = cursor.fetchone()

    if not s: 
        conn.close()
        return

    no, name, father, gfather, cls, fee, is_free, uses_t, t_fee, fphone, p_debt, t_debt, b_debt, u_debt, tr_debt, reg_date = s
    
    if is_free == 1:
        fee = 0.0

    active_months = calculate_active_months(self.student_id, reg_date)
    calculated_tuition = fee * active_months
    calculated_transport = (t_fee * active_months) if uses_t == 1 else 0.0
    
    gross_debt = p_debt + calculated_tuition + calculated_transport + b_debt + u_debt + tr_debt
    
    cursor.execute("SELECT SUM(amount) FROM student_payments WHERE student_id = ?", (self.student_id,))
    total_payments_made = cursor.fetchone()[0] or 0.0
    
    conn.close()
    
    if total_payments_made > gross_debt:
        net_debt = 0.0
        advance_payment = total_payments_made - gross_debt
    else:
        net_debt = gross_debt - total_payments_made
        advance_payment = 0.0

    info_box = QGroupBox("مشخصات و تفکیک حساب‌های دانش‌آموز")
    info_box.setStyleSheet("font-weight: bold; color: #0d47a1; background-color: #f5f5f5; border: 1px solid #1976d2; font-size: 14px;")
    info_layout = QGridLayout()
    info_layout.addWidget(QLabel(f"نمبر آی‌دی: {no}"), 0, 0)
    info_layout.addWidget(QLabel(f"نام کامل: {name} {'(رایگان/معاف)' if is_free == 1 else ''}"), 0, 1)
    info_layout.addWidget(QLabel(f"نام پدر: {father} ({gfather})"), 0, 2)
    
    info_layout.addWidget(QLabel(f"صنف: {cls}"), 1, 0)
    info_layout.addWidget(QLabel(f"تلفن پدر: {fphone}"), 1, 1)
    info_layout.addWidget(QLabel(f"تاریخ ثبت‌نام: {reg_date}"), 1, 2)
    
    lbl_fixed_fee = QLabel(f"💵 فیس ماهانه قراردادی: {fee:,.2f} افغانی")
    lbl_fixed_fee.setStyleSheet("color: #1565c0; font-weight: bold; font-size: 14px; background-color: #e3f2fd; padding: 4px; border-radius: 4px;")
    info_layout.addWidget(lbl_fixed_fee, 2, 0)

    lbl_advance = QLabel(f"💰 پیش‌پرداخت / بستانکاری: {advance_payment:,.2f} افغانی")
    lbl_advance.setStyleSheet("color: #2e7d32; font-weight: bold; font-size: 14px; background-color: #e8f5e9; padding: 4px; border-radius: 4px;")
    info_layout.addWidget(lbl_advance, 2, 1)

    lbl_debt = QLabel(f"مجموع کل باقی‌داری: {net_debt:,.2f} افغانی")
    lbl_debt.setStyleSheet("color: #c62828; font-weight: bold; font-size: 15px;")
    info_layout.addWidget(lbl_debt, 2, 2)
    
    details_debt = QLabel(f"ریز بدهی‌ها: [قبلی: {p_debt:,.2f}] | [شهریه ({active_months} ماه فعال): {calculated_tuition:,.2f}] | [ترانسپورت: {calculated_transport:,.2f}] | [کتاب: {b_debt:,.2f}] | [لباس: {u_debt:,.2f}]")
    details_debt.setStyleSheet("font-size: 13px;")
    info_layout.addWidget(details_debt, 3, 0, 1, 3)
    info_box.setLayout(info_layout)
    self.layout.addWidget(info_box)

    btn_print_profile = QPushButton("🖨️ چاپ کامل پرونده و صورتحساب شاگرد")
    btn_print_profile.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 10px; font-size: 14px; border-radius: 8px;")
    btn_print_profile.clicked.connect(self.print_student_profile)
    self.layout.addWidget(btn_print_profile)

    self.chk_show_break = QCheckBox("📌 نمایش / فعال‌سازی ثبت دوره عدم حضور (Break)")
    self.chk_show_break.setStyleSheet("font-weight: bold; color: #e65100; font-size: 14px; margin-top: 10px;")
    self.chk_show_break.toggled.connect(self.toggle_break_visibility)
    self.layout.addWidget(self.chk_show_break)

    self.break_container = QWidget()
    break_container_layout = QVBoxLayout(self.break_container)
    break_container_layout.setContentsMargins(0, 0, 0, 0)

    break_box = QGroupBox("تنظیم مرخصی / عدم حضور (Break) جهت کسر فیس در ماه‌های مشخص")
    break_box.setStyleSheet("font-weight: bold; color: #e65100; font-size: 13px; border: 1px solid #ffb74d;")
    break_layout = QHBoxLayout()
    self.txt_break_start = ZoomableLineEdit(); self.txt_break_start.setPlaceholderText("از ماه (1405/02/01)")
    self.txt_break_end = ZoomableLineEdit(); self.txt_break_end.setPlaceholderText("تا ماه (1405/03/01)")
    self.txt_break_reason = ZoomableLineEdit(); self.txt_break_reason.setPlaceholderText("دلیل (مریضی/رخصتی)...")
    
    btn_add_break = QPushButton("➕ ثبت عدم حضور (Break)")
    btn_add_break.setStyleSheet("background-color: #e65100; color: white; font-weight: bold; padding: 6px 12px; border-radius: 6px;")
    btn_add_break.clicked.connect(self.save_student_break)

    break_layout.addWidget(QLabel("از تاریخ/ماه:"))
    break_layout.addWidget(self.txt_break_start)
    break_layout.addWidget(QLabel("تا تاریخ/ماه:"))
    break_layout.addWidget(self.txt_break_end)
    break_layout.addWidget(QLabel("دلیل:"))
    break_layout.addWidget(self.txt_break_reason)
    break_layout.addWidget(btn_add_break)
    break_box.setLayout(break_layout)
    break_container_layout.addWidget(break_box)

    lbl_break_hist = QLabel("📋 سوابق مرخصی‌ها و عدم حضور (Break) ثبت شده برای این شاگرد:")
    lbl_break_hist.setStyleSheet("font-weight: bold; color: #e65100;")
    break_container_layout.addWidget(lbl_break_hist)
    
    self.break_table = QTableWidget()
    self.break_table.setColumnCount(5)
    self.break_table.setHorizontalHeaderLabels(["شناسه", "از تاریخ", "تا تاریخ", "دلیل عدم حضور / مرخصی", "حذف رکورد"])
    self.break_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    self.load_break_history()
    break_container_layout.addWidget(self.break_table)

    self.layout.addWidget(self.break_container)
    self.break_container.setVisible(False)

    pay_box = QGroupBox("دریافت وجه و فیس از دانش‌آموز")
    pay_box.setStyleSheet("font-weight: bold; color: #0d47a1; background-color: #ffffff; border: 1px solid #1976d2; font-size: 14px;")
    pay_layout = QGridLayout()
    
    self.combo_fee_type = QComboBox()
    self.combo_fee_type.setStyleSheet("font-size: 14px; padding: 6px; border-radius: 6px;")
    self.combo_fee_type.addItems(["شهریه ماه جاری", "باقی‌داری قبلی", "ترانسپورت", "کتاب", "لباس", "پیش‌پرداخت / بستانکاری"])
    self.txt_pay_amount = ZoomableLineEdit(); self.txt_pay_amount.setPlaceholderText("مبلغ پرداختی...")
    
    today_shamsi = jdatetime.date.today().strftime("%Y/%m/%d")
    self.txt_pay_date = ZoomableLineEdit(today_shamsi)
    
    self.txt_pay_desc = ZoomableLineEdit(); self.txt_pay_desc.setPlaceholderText("توضیحات اختیاری...")
    
    btn_receive = QPushButton("ثبت پرداخت و دریافت وجه")
    btn_receive.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 10px; font-size: 14px; border-radius: 8px;")
    btn_receive.clicked.connect(self.process_payment)

    pay_layout.addWidget(QLabel("نوع فیس:"), 0, 0); pay_layout.addWidget(self.combo_fee_type, 0, 1)
    pay_layout.addWidget(QLabel("مبلغ:"), 0, 2); pay_layout.addWidget(self.txt_pay_amount, 0, 3)
    pay_layout.addWidget(QLabel("تاریخ (اتومات/دستی):"), 1, 0); pay_layout.addWidget(self.txt_pay_date, 1, 1)
    pay_layout.addWidget(QLabel("توضیحات:"), 1, 2); pay_layout.addWidget(self.txt_pay_desc, 1, 3)
    pay_layout.addWidget(btn_receive, 2, 0, 1, 4)
    pay_box.setLayout(pay_layout)
    self.layout.addWidget(pay_box)

    self.layout.addWidget(QLabel("💳 سوابق پرداخت‌ها و دریافت وجه از شاگرد:"))
    self.pay_table = QTableWidget()
    self.pay_table.setColumnCount(7)
    self.pay_table.setHorizontalHeaderLabels(["شناسه", "تاریخ", "نوع تراکنش", "نوع فیس/بدهی", "مبلغ", "توضیحات", "حذف"])
    self.pay_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    self.load_payment_history()
    self.layout.addWidget(self.pay_table)

def toggle_break_visibility(self, checked):
    self.break_container.setVisible(checked)

def load_break_history(self):
    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT break_id, start_month, end_month, reason FROM student_breaks WHERE student_id = ?", (self.student_id,))
    rows = cursor.fetchall()
    conn.close()

    self.break_table.setRowCount(len(rows))
    for r_idx, row in enumerate(rows):
        b_id = row[0]
        self.break_table.setItem(r_idx, 0, QTableWidgetItem(str(row[0])))
        self.break_table.setItem(r_idx, 1, QTableWidgetItem(str(row[1])))
        self.break_table.setItem(r_idx, 2, QTableWidgetItem(str(row[2])))
        self.break_table.setItem(r_idx, 3, QTableWidgetItem(str(row[3] or 'ثبت نشده')))
        
        btn_del = QPushButton("❌ حذف Break")
        btn_del.setStyleSheet("background-color: #c62828; color: white; border-radius: 4px; font-weight: bold;")
        btn_del.clicked.connect(lambda checked, bid=b_id: self.delete_break(bid))
        self.break_table.setCellWidget(r_idx, 4, btn_del)

def delete_break(self, break_id):
    confirm = QMessageBox.question(self, "تایید حذف", "آیا از حذف این دوره عدم حضور (Break) اطمینان دارید؟", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    if confirm == QMessageBox.StandardButton.Yes:
        conn = sqlite3.connect("school_finance.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM student_breaks WHERE break_id = ?", (break_id,))
        conn.commit(); conn.close()
        QMessageBox.information(self, "موفقیت", "دوره مرخصی حذف شد و محاسبات فیس به‌روزرسانی گردید.")
        self.load_student_info()

def save_student_break(self):
    s_month = self.txt_break_start.text().strip()
    e_month = self.txt_break_end.text().strip()
    reason = self.txt_break_reason.text().strip()
    if not s_month or not e_month:
        QMessageBox.warning(self, "خطا", "لطفاً تاریخ شروع و پایان را وارد کنید.")
        return
    
    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO student_breaks (student_id, start_month, end_month, reason) VALUES (?, ?, ?, ?)",
                   (self.student_id, s_month, e_month, reason))
    conn.commit(); conn.close()
    QMessageBox.information(self, "موفقیت", "دوره عدم حضور (Break) با موفقیت ثبت شد.")
    self.txt_break_start.clear(); self.txt_break_end.clear(); self.txt_break_reason.clear()
    self.load_student_info()

def print_student_profile(self):
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    dialog = QPrintDialog(printer, self)
    if dialog.exec() == QPrintDialog.DialogCode.Accepted:
        document = QTextDocument()
        conn = sqlite3.connect("school_finance.db")
        cursor = conn.cursor()
        cursor.execute("SELECT student_no, full_name, father_name, grandfather_name, class_name, standard_fee, registration_date FROM students WHERE student_id = ?", (self.student_id,))
        s_data = cursor.fetchone()
        
        html = "<h1 style='text-align: center; font-size: 22px; font-weight: bold;'>مکتب خصوصی کاوشگران دانش بلخ</h1>"
        html += "<h2 style='text-align: center; font-size: 18px;'>پرونده و صورتحساب جامع دانش‌آموز</h2>"
        if s_data:
            html += f"<p style='font-size: 14px;'><b>نمبر آی‌دی:</b> {s_data[0]} | <b>نام کامل:</b> {s_data[1]} | <b>نام پدر:</b> {s_data[2]} ({s_data[3]}) | <b>صنف:</b> {s_data[4]} | <b>فیس ماهانه:</b> {s_data[5]:,.2f} افغانی | <b>تاریخ ثبت‌نام:</b> {s_data[6]}</p>"
        
        html += "<h3>ریز سوابق پرداخت‌ها و تراکنش‌ها:</h3>"
        html += "<table border='1' cellspacing='0' cellpadding='8' width='100%'" \
                " style='border-collapse: collapse; direction: rtl; font-size: 14px;'>"
        html += "<tr style='background-color: #f2f2f2; font-weight: bold;'>"
        html += "<th>تاریخ</th><th>نوع تراکنش</th><th>نوع فیس / بدهی</th><th>مبلغ (افغانی)</th><th>توضیحات</th><th>کاربر ثبت‌کننده</th>"
        html += "</tr>"
        
        cursor.execute("SELECT date, trans_type, fee_type, amount, description, user_name FROM student_payments WHERE student_id = ?", (self.student_id,))
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            html += "<tr>"
            for val in row:
                html += f"<td style='text-align: center; padding: 6px;'>{val if val is not None else ''}</td>"
            html += "</tr>"
        html += "</table>"
        
        document.setHtml(html)
        document.print(printer)
        QMessageBox.information(self, "موفقیت", "پرونده شاگرد برای چاپ ارسال شد.")

def load_payment_history(self):
    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT payment_id, date, trans_type, fee_type, amount, description FROM student_payments WHERE student_id = ?", (self.student_id,))
    rows = cursor.fetchall()
    conn.close()

    self.pay_table.setRowCount(len(rows))
    for r_idx, row in enumerate(rows):
        p_id = row[0]
        for c_idx in range(6):
            self.pay_table.setItem(r_idx, c_idx, QTableWidgetItem(str(row[c_idx] if row[c_idx] is not None else "")))
        
        btn_del = QPushButton("❌ حذف")
        btn_del.setStyleSheet("background-color: #c62828; color: white; border-radius: 4px;")
        btn_del.clicked.connect(lambda checked, pid=p_id: self.delete_payment(pid))
        self.pay_table.setCellWidget(r_idx, 6, btn_del)

def delete_payment(self, payment_id):
    confirm = QMessageBox.question(self, "تایید حذف", "با حذف این پرداخت، مبلغ آن از حساب کسر خواهد شد. آیا مطمئن هستید؟", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    if confirm == QMessageBox.StandardButton.Yes:
        conn = sqlite3.connect("school_finance.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT fee_type, amount FROM student_payments WHERE payment_id = ?", (payment_id,))
        p_row = cursor.fetchone()
        if p_row:
            fee_type, amount = p_row
            cursor.execute("INSERT INTO cashbox (date, type, category, amount, description, user_name) VALUES (date('now'), 'Outflow', 'برگشت پرداخت شاگرد', ?, 'حذف و برگشت پرداخت شاگرد ID:' || ?, ?)",
                           (amount, self.student_id, self.user_full_name))

        cursor.execute("DELETE FROM student_payments WHERE payment_id = ?", (payment_id,))
        conn.commit(); conn.close()
        QMessageBox.information(self, "موفقیت", "تراکنش حذف شد و حساب‌ها به‌روزرسانی گردیدند.")
        self.load_student_info()

def process_payment(self):
    amount = float(self.txt_pay_amount.text().strip() or 0)
    date_str = self.txt_pay_date.text().strip()
    if amount <= 0 or not date_str:
        QMessageBox.warning(self, "خطا", "لطفاً مبلغ و تاریخ معتبر وارد کنید.")
        return

    fee_type = self.combo_fee_type.currentText()
    desc = self.txt_pay_desc.text().strip()

    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()

    cursor.execute("INSERT INTO student_payments (student_id, date, trans_type, fee_type, amount, description, user_name) VALUES (?, ?, 'دریافت وجه', ?, ?, ?, ?)",
                   (self.student_id, date_str, fee_type, amount, desc, self.user_full_name))

    cursor.execute("INSERT INTO cashbox (date, type, category, amount, description, user_name) VALUES (?, 'Inflow', ?, ?, ?, ?)",
                   (date_str, f"دریافت {fee_type}", amount, f"پرداخت شاگرد ID:{self.student_id}\n{desc}", self.user_full_name))
    
    conn.commit()
    conn.close()
    QMessageBox.information(self, "موفقیت", "تراکنش با موفقیت ثبت شد.")
    self.txt_pay_amount.clear()
    self.txt_pay_desc.clear()
    self.load_student_info()


==============================================================================

4. MAIN APPLICATION WINDOW

==============================================================================

class MainWindow(QMainWindow):
def init(self, full_name, role):
super().init()
self.user_full_name = full_name
self.user_role = role
self.setWindowTitle(f"سیستم جامع مدیریت مالی - مکتب خصوصی کاوشگران دانش بلخ | کاربر: {full_name} ({role})")
self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
self.setFont(QFont("Tahoma", 13))

    self.tabs = QTabWidget()
    self.tabs.setStyleSheet("""
        QTabWidget::pane { border: 2px solid #0d47a1; background: #f0f4f8; }
        QTabBar::tab { background: #d0e1f9; padding: 10px 18px; font-weight: bold; color: #0d47a1; margin-left: 2px; font-size: 13px; border-top-left-radius: 8px; border-top-right-radius: 8px; }
        QTabBar::tab:selected { background: #0d47a1; color: white; }
    """)
    self.setCentralWidget(self.tabs)
    
    self.init_dashboard_tab()
    self.init_registration_tab()
    self.init_search_tab()
    self.init_attendance_tab()
    self.init_evaluations_tab()
    self.init_staff_tab()
    self.init_expenses_tab()
    self.init_reports_tab()
    self.init_cashbox_tab()
    self.init_settings_tab()
    self.init_help_tab()

# --------------------------------------------------------------------------
# TAB 1: DASHBOARD
# --------------------------------------------------------------------------
def init_dashboard_tab(self):
    tab = QWidget()
    layout = QVBoxLayout()
    layout.setContentsMargins(30, 20, 30, 20)
    
    title = QLabel("داشبورد مدیریتی مکتب خصوصی کاوشگران دانش بلخ")
    title.setStyleSheet("font-size: 24px; font-weight: bold; color: #0d47a1; margin-bottom: 10px;")
    layout.addWidget(title)

    stats_layout = QHBoxLayout()
    self.box_students = QGroupBox("دانش‌آموزان فعال")
    self.box_cash = QGroupBox("موجودی فعلی صندوق")
    self.box_debts = QGroupBox("مجموع باقی‌داری‌ها")
    
    for box in [self.box_students, self.box_cash, self.box_debts]:
        box.setStyleSheet("font-weight: bold; font-size: 14px; color: #0d47a1; background-color: #ffffff; border: 2px solid #bbdefb; border-radius: 10px; margin-top: 10px;")

    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM students WHERE status='فعال'")
    s_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(amount) FROM cashbox WHERE type='Inflow'")
    inflow = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(amount) FROM cashbox WHERE type='Outflow'")
    outflow = cursor.fetchone()[0] or 0
    total_cash = inflow - outflow
    
    cursor.execute("SELECT student_id, standard_fee, is_free, uses_transport, transport_fee, registration_date, initial_previous_debt, initial_books_debt, initial_uniform_debt, initial_transport_debt FROM students")
    all_st = cursor.fetchall()
    total_debts = 0
    for st_item in all_st:
        s_id, fee, is_free, uses_t, t_fee, reg_date, p_debt, b_debt, u_debt, tr_debt = st_item
        if is_free == 1:
            fee = 0.0
        active_m = calculate_active_months(s_id, reg_date)
        calc_tuition = fee * active_m
        calc_transport = (t_fee * active_m) if uses_t == 1 else 0.0

        cursor.execute("SELECT SUM(amount) FROM student_payments WHERE student_id = ?", (s_id,))
        paid_tot = cursor.fetchone()[0] or 0.0

        gross_d = (p_debt + calc_tuition + calc_transport + b_debt + u_debt + tr_debt)
        net_d = max(0, gross_d - paid_tot)
        total_debts += net_d

    conn.close()
    
    cash_layout = QVBoxLayout()
    self.lbl_cash = QLabel(f"{total_cash:,.2f} افغانی")
    self.lbl_cash.setStyleSheet("font-size: 20px; font-weight: bold; color: #2e7d32;")
    cash_layout.addWidget(self.lbl_cash)
    self.box_cash.setLayout(cash_layout)
    
    v1 = QVBoxLayout(); l1 = QLabel(f"{s_count} نفر"); l1.setStyleSheet("font-size: 22px; font-weight: bold; color: #1976d2;"); v1.addWidget(l1); self.box_students.setLayout(v1)
    v3 = QVBoxLayout(); l3 = QLabel(f"{total_debts:,.2f} افغانی"); l3.setStyleSheet("font-size: 22px; font-weight: bold; color: #c62828;"); v3.addWidget(l3); self.box_debts.setLayout(v3)
    
    stats_layout.addWidget(self.box_students); stats_layout.addWidget(self.box_cash); stats_layout.addWidget(self.box_debts)
    layout.addLayout(stats_layout)
    layout.addStretch()
    tab.setLayout(layout)
    self.tabs.addTab(tab, "📊 داشبورد")

# --------------------------------------------------------------------------
# TAB 2: STUDENT REGISTRATION
# --------------------------------------------------------------------------
def init_registration_tab(self):
    tab = QWidget()
    layout = QVBoxLayout()
    layout.setContentsMargins(20, 20, 20, 20)
    
    grid = QGridLayout()
    self.reg_no = ZoomableLineEdit()
    self.reg_name = ZoomableLineEdit()
    self.reg_father = ZoomableLineEdit()
    self.reg_gfather = ZoomableLineEdit()
    self.reg_class = QComboBox()
    self.load_classes_into_combo(self.reg_class)
    self.reg_fee = ZoomableLineEdit()
    
    self.chk_reg_free = QCheckBox("شاگرد رایگان (معاف از شهریه)")
    self.chk_reg_free.setStyleSheet("font-weight: bold; color: #2e7d32; font-size: 13px;")
    self.chk_reg_free.toggled.connect(self.toggle_reg_free_status)

    self.reg_fphone = ZoomableLineEdit()
    self.reg_mphone = ZoomableLineEdit()
    self.reg_prev_debt = ZoomableLineEdit("0")
    today_shamsi = jdatetime.date.today().strftime("%Y/%m/%d")
    self.reg_date = ZoomableLineEdit(today_shamsi)

    grid.addWidget(QLabel("نمبر آی‌دی:"), 0, 0); grid.addWidget(self.reg_no, 0, 1)
    grid.addWidget(QLabel("نام کامل:"), 1, 0); grid.addWidget(self.reg_name, 1, 1)
    grid.addWidget(QLabel("نام پدر:"), 2, 0); grid.addWidget(self.reg_father, 2, 1)
    grid.addWidget(QLabel("نام پدرکلان:"), 3, 0); grid.addWidget(self.reg_gfather, 3, 1)
    grid.addWidget(QLabel("صنف:"), 4, 0); grid.addWidget(self.reg_class, 4, 1)
    grid.addWidget(QLabel("شهریه ماهانه:"), 5, 0); grid.addWidget(self.reg_fee, 5, 1)
    grid.addWidget(self.chk_reg_free, 6, 0, 1, 2)
    grid.addWidget(QLabel("تلفن پدر:"), 7, 0); grid.addWidget(self.reg_fphone, 7, 1)
    grid.addWidget(QLabel("تلفن مادر:"), 8, 0); grid.addWidget(self.reg_mphone, 8, 1)
    grid.addWidget(QLabel("باقی‌داری قبلی:"), 9, 0); grid.addWidget(self.reg_prev_debt, 9, 1)
    grid.addWidget(QLabel("تاریخ ثبت‌نام:"), 10, 0); grid.addWidget(self.reg_date, 10, 1)

    btn_save = QPushButton("📝 ثبت نهایی دانش‌آموز")
    btn_save.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 12px; font-size: 14px; border-radius: 8px;")
    btn_save.clicked.connect(self.save_new_student)

    layout.addLayout(grid)
    layout.addWidget(btn_save)
    layout.addStretch()
    tab.setLayout(layout)
    self.tabs.addTab(tab, "➕ ثبت‌نام شاگرد جدید")

def toggle_reg_free_status(self, checked):
    if checked:
        self.reg_fee.setText("0")
        self.reg_fee.setEnabled(False)
    else:
        self.reg_fee.setEnabled(True)

def load_classes_into_combo(self, combo):
    combo.clear()
    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT class_name FROM classes")
    for r in cursor.fetchall():
        combo.addItem(r[0])
    conn.close()

def save_new_student(self):
    no = self.reg_no.text().strip(); name = self.reg_name.text().strip()
    is_free = 1 if self.chk_reg_free.isChecked() else 0
    fee = 0.0 if is_free else float(self.reg_fee.text().strip() or 0)
    
    if not no or not name:
        QMessageBox.warning(self, "خطا", "نمبر آی‌دی و نام کامل الزامی هستند.")
        return

    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO students (student_no, full_name, father_name, grandfather_name, class_name, standard_fee, is_free, father_phone, mother_phone, initial_previous_debt, registration_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (no, name, self.reg_father.text().strip(), self.reg_gfather.text().strip(), self.reg_class.currentText(), fee, is_free, self.reg_fphone.text().strip(), self.reg_mphone.text().strip(), float(self.reg_prev_debt.text().strip() or 0), self.reg_date.text().strip()))
        conn.commit()
        QMessageBox.information(self, "موفقیت", "دانش‌آموز جدید با موفقیت ثبت گردید.")
        self.reg_no.clear(); self.reg_name.clear(); self.reg_father.clear(); self.reg_gfather.clear(); self.reg_fee.clear(); self.reg_fphone.clear(); self.reg_mphone.clear()
    except Exception as e:
        QMessageBox.critical(self, "خطا", f"خطا در ثبت: {e}")
    finally:
        conn.close()

# --------------------------------------------------------------------------
# TAB 3: SEARCH & MANAGE STUDENTS
# --------------------------------------------------------------------------
def init_search_tab(self):
    tab = QWidget()
    layout = QVBoxLayout()
    layout.setContentsMargins(20, 20, 20, 20)
    
    self.txt_search = ZoomableLineEdit()
    self.txt_search.setPlaceholderText("جستجوی نام یا نمبر آی‌دی شاگرد...")
    self.txt_search.textChanged.connect(self.load_search_table)
    layout.addWidget(self.txt_search)
    
    self.search_table = QTableWidget()
    self.search_table.setColumnCount(8)
    self.search_table.setHorizontalHeaderLabels(["آی‌دی", "نام", "نام پدر", "صنف", "تلفن", "باقی‌داری کل", "پرونده", "ویرایش"])
    self.search_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    layout.addWidget(self.search_table)
    tab.setLayout(layout)
    self.tabs.addTab(tab, "🔍 جستجو و مشاهده شاگردان")
    self.load_search_table("")

def load_search_table(self, query=""):
    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    if query:
        cursor.execute("SELECT student_id, student_no, full_name, father_name, class_name, father_phone, standard_fee, is_free, uses_transport, transport_fee, registration_date, initial_previous_debt, initial_books_debt, initial_uniform_debt, initial_transport_debt FROM students WHERE full_name LIKE ? OR student_no LIKE ?", (f"%{query}%", f"%{query}%"))
    else:
        cursor.execute("SELECT student_id, student_no, full_name, father_name, class_name, father_phone, standard_fee, is_free, uses_transport, transport_fee, registration_date, initial_previous_debt, initial_books_debt, initial_uniform_debt, initial_transport_debt FROM students")
    raw_rows = cursor.fetchall()
    
    rows = []
    for r in raw_rows:
        s_id, no, name, father, cls, fphone, fee, is_free, uses_t, t_fee, reg_date, p_debt, b_debt, u_debt, tr_debt = r
        if is_free == 1:
            fee = 0.0
        active_m = calculate_active_months(s_id, reg_date)
        calc_tuition = fee * active_m
        calc_transport = (t_fee * active_m) if uses_t == 1 else 0.0

        cursor.execute("SELECT SUM(amount) FROM student_payments WHERE student_id = ?", (s_id,))
        paid_tot = cursor.fetchone()[0] or 0.0

        gross_d = (p_debt + calc_tuition + calc_transport + b_debt + u_debt + tr_debt)
        net_d = max(0, gross_d - paid_tot)
        display_name = name + " (رایگان)" if is_free == 1 else name
        rows.append((no, display_name, father, cls, fphone, net_d, s_id))

    conn.close()
    
    self.search_table.setRowCount(len(rows))
    for r_idx, row in enumerate(rows):
        s_id = row[6]
        for c_idx in range(6):
            val = row[c_idx]
            if c_idx == 5:
                val = f"{val:,.2f}"
            self.search_table.setItem(r_idx, c_idx, QTableWidgetItem(str(val)))
        
        btn_profile = QPushButton("📋 مشاهده پرونده")
        btn_profile.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold; border-radius: 6px;")
        btn_profile.clicked.connect(lambda checked, sid=s_id: StudentProfileWindow(sid, self.user_full_name, self).exec())
        self.search_table.setCellWidget(r_idx, 6, btn_profile)

        btn_edit = QPushButton("✏️ ویرایش")
        btn_edit.setStyleSheet("background-color: #f57c00; color: white; font-weight: bold; border-radius: 6px;")
        btn_edit.clicked.connect(lambda checked, sid=s_id: self.open_edit_dialog(sid))
        self.search_table.setCellWidget(r_idx, 7, btn_edit)

def open_edit_dialog(self, student_id):
    dlg = EditStudentDialog(student_id, self)
    if dlg.exec() == QDialog.DialogCode.Accepted:
        self.load_search_table(self.txt_search.text().strip())

# --------------------------------------------------------------------------
# TAB 4: DAILY ATTENDANCE
# --------------------------------------------------------------------------
def init_attendance_tab(self):
    tab = QWidget()
    layout = QVBoxLayout()
    layout.setContentsMargins(20, 20, 20, 20)
    
    filter_layout = QHBoxLayout()
    self.combo_att_class = QComboBox()
    self.load_classes_into_combo(self.combo_att_class)
    today_shamsi = jdatetime.date.today().strftime("%Y/%m/%d")
    self.txt_att_date = ZoomableLineEdit(today_shamsi)
    
    btn_load_att = QPushButton("بارگذاری شاگردان صنف")
    btn_load_att.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold; padding: 6px 12px; border-radius: 6px;")
    btn_load_att.clicked.connect(self.load_attendance_students)

    filter_layout.addWidget(QLabel("انتخاب صنف:"))
    filter_layout.addWidget(self.combo_att_class)
    filter_layout.addWidget(QLabel("تاریخ:"))
    filter_layout.addWidget(self.txt_att_date)
    filter_layout.addWidget(btn_load_att)
    layout.addLayout(filter_layout)

    self.att_table = QTableWidget()
    self.att_table.setColumnCount(5)
    self.att_table.setHorizontalHeaderLabels(["شناسه", "نمبر آی‌دی", "نام و تخلص", "نام پدر", "وضعیت حاضری"])
    self.att_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    layout.addWidget(self.att_table)

    btn_save_att = QPushButton("💾 ثبت نهایی حاضری")
    btn_save_att.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 10px; font-size: 14px; border-radius: 8px;")
    btn_save_att.clicked.connect(self.save_attendance)
    layout.addWidget(btn_save_att)

    tab.setLayout(layout)
    self.tabs.addTab(tab, "📝 حاضری شاگردان")

def load_attendance_students(self):
    cls = self.combo_att_class.currentText()
    date_str = self.txt_att_date.text().strip()
    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT student_id, student_no, full_name, father_name FROM students WHERE class_name = ? AND status='فعال'", (cls,))
    students = cursor.fetchall()
    
    self.att_table.setRowCount(len(students))
    for r_idx, st_data in enumerate(students):
        s_id, no, name, father = st_data
        self.att_table.setItem(r_idx, 0, QTableWidgetItem(str(s_id)))
        self.att_table.setItem(r_idx, 1, QTableWidgetItem(str(no)))
        self.att_table.setItem(r_idx, 2, QTableWidgetItem(str(name)))
        self.att_table.setItem(r_idx, 3, QTableWidgetItem(str(father)))
        
        combo_status = QComboBox()
        combo_status.addItems(["حاضر", "غیرحاضر", "مرخص", "تاخیر"])
        
        cursor.execute("SELECT status FROM attendance WHERE student_id = ? AND date = ?", (s_id, date_str))
        att_row = cursor.fetchone()
        if att_row:
            combo_status.setCurrentText(att_row[0])
        
        self.att_table.setCellWidget(r_idx, 4, combo_status)
    conn.close()

def save_attendance(self):
    date_str = self.txt_att_date.text().strip()
    if not date_str:
        QMessageBox.warning(self, "خطا", "لطفاً تاریخ معتبر وارد کنید.")
        return

    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    for r in range(self.att_table.rowCount()):
        s_id = int(self.att_table.item(r, 0).text())
        combo = self.att_table.cellWidget(r, 4)
        status = combo.currentText()
        
        cursor.execute("DELETE FROM attendance WHERE student_id = ? AND date = ?", (s_id, date_str))
        cursor.execute("INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)", (s_id, date_str, status))
    
    conn.commit(); conn.close()
    QMessageBox.information(self, "موفقیت", "حاضری صنف با موفقیت ثبت شد.")

# --------------------------------------------------------------------------
# TAB 5: STUDENT EVALUATIONS
# --------------------------------------------------------------------------
def init_evaluations_tab(self):
    tab = QWidget()
    layout = QVBoxLayout()
    layout.setContentsMargins(20, 20, 20, 20)
    
    filter_layout = QHBoxLayout()
    self.combo_eval_class = QComboBox()
    self.load_classes_into_combo(self.combo_eval_class)
    today_shamsi = jdatetime.date.today().strftime("%Y/%m/%d")
    self.txt_eval_date = ZoomableLineEdit(today_shamsi)
    
    btn_load_eval = QPushButton("بارگذاری لیست ارزیابی صنف")
    btn_load_eval.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold; padding: 6px 12px; border-radius: 6px;")
    btn_load_eval.clicked.connect(self.load_evaluations_students)

    filter_layout.addWidget(QLabel("انتخاب صنف:"))
    filter_layout.addWidget(self.combo_eval_class)
    filter_layout.addWidget(QLabel("تاریخ:"))
    filter_layout.addWidget(self.txt_eval_date)
    filter_layout.addWidget(btn_load_eval)
    layout.addLayout(filter_layout)

    self.eval_table = QTableWidget()
    self.eval_table.setColumnCount(10)
    self.eval_table.setHorizontalHeaderLabels(["شناسه", "نام شاگرد", "بررسی کتابچه", "بررسی اجندا", "املا/تکالیف", "سطح یادگیری", "کارخانگی", "سایر موارد", "مجموع نمره", "ثبت"])
    self.eval_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    layout.addWidget(self.eval_table)

    tab.setLayout(layout)
    self.tabs.addTab(tab, "⭐ ارزیابی روزانه شاگردان")

def load_evaluations_students(self):
    cls = self.combo_eval_class.currentText()
    date_str = self.txt_eval_date.text().strip()
    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT student_id, full_name FROM students WHERE class_name = ? AND status='فعال'", (cls,))
    students = cursor.fetchall()
    
    self.eval_table.setRowCount(len(students))
    for r_idx, st_data in enumerate(students):
        s_id, name = st_data
        self.eval_table.setItem(r_idx, 0, QTableWidgetItem(str(s_id)))
        self.eval_table.setItem(r_idx, 1, QTableWidgetItem(str(name)))
        
        cursor.execute("SELECT notebook_check, diary_check, dictation, learning_level, homework, other_cases, total_score FROM evaluations WHERE student_id = ? AND date = ?", (s_id, date_str))
        ev = cursor.fetchone() or (0, 0, 0, 0, 0, 0, 0)
        
        for c_idx in range(6):
            txt_input = ZoomableLineEdit(str(ev[c_idx]))
            self.eval_table.setCellWidget(r_idx, c_idx + 2, txt_input)
        
        self.eval_table.setItem(r_idx, 8, QTableWidgetItem(str(ev[6])))
        
        btn_save = QPushButton("💾 ثبت")
        btn_save.setStyleSheet("background-color: #2e7d32; color: white; border-radius: 4px; font-weight: bold;")
        btn_save.clicked.connect(lambda checked, row=r_idx: self.save_single_eval(row))
        self.eval_table.setCellWidget(r_idx, 9, btn_save)

    conn.close()

def save_single_eval(self, row):
    s_id = int(self.eval_table.item(row, 0).text())
    date_str = self.txt_eval_date.text().strip()
    
    scores = []
    for c in range(2, 8):
        widget = self.eval_table.cellWidget(row, c)
        val = int(widget.text().strip() or 0)
        scores.append(val)
    
    total_score = sum(scores)
    self.eval_table.setItem(row, 8, QTableWidgetItem(str(total_score)))

    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM evaluations WHERE student_id = ? AND date = ?", (s_id, date_str))
    cursor.execute('''
        INSERT INTO evaluations (student_id, date, notebook_check, diary_check, dictation, learning_level, homework, other_cases, total_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (s_id, date_str, scores[0], scores[1], scores[2], scores[3], scores[4], scores[5], total_score))
    conn.commit(); conn.close()
    QMessageBox.information(self, "موفقیت", "ارزیابی دانش‌آموز ثبت گردید.")

# --------------------------------------------------------------------------
# TAB 6: STAFF & PAYROLL
# --------------------------------------------------------------------------
def init_staff_tab(self):
    tab = QWidget()
    layout = QVBoxLayout()
    layout.setContentsMargins(20, 20, 20, 20)
    
    form_box = QGroupBox("ثبت استاد / پرسنل جدید")
    form_box.setStyleSheet("font-weight: bold; color: #0d47a1;")
    grid = QGridLayout()
    
    self.txt_staff_no = ZoomableLineEdit()
    self.txt_staff_name = ZoomableLineEdit()
    self.combo_staff_role = QComboBox()
    self.combo_staff_role.addItems(["استاد", "اداری", "خدماتی", "تحویل‌دار", "مدیر"])
    self.txt_staff_phone = ZoomableLineEdit()
    self.txt_staff_salary = ZoomableLineEdit()
    today_shamsi = jdatetime.date.today().strftime("%Y/%m/%d")
    self.txt_staff_regdate = ZoomableLineEdit(today_shamsi)

    grid.addWidget(QLabel("نمبر آی‌دی/کد:"), 0, 0); grid.addWidget(self.txt_staff_no, 0, 1)
    grid.addWidget(QLabel("نام کامل:"), 0, 2); grid.addWidget(self.txt_staff_name, 0, 3)
    grid.addWidget(QLabel("سمت/وظیفه:"), 1, 0); grid.addWidget(self.combo_staff_role, 1, 1)
    grid.addWidget(QLabel("شماره تماس:"), 1, 2); grid.addWidget(self.txt_staff_phone, 1, 3)
    grid.addWidget(QLabel("معاش ماهانه:"), 2, 0); grid.addWidget(self.txt_staff_salary, 2, 1)
    grid.addWidget(QLabel("تاریخ استخدام:"), 2, 2); grid.addWidget(self.txt_staff_regdate, 2, 3)

    btn_add_staff = QPushButton("➕ ثبت پرسنل جدید")
    btn_add_staff.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 8px;")
    btn_add_staff.clicked.connect(self.save_staff)
    grid.addWidget(btn_add_staff, 3, 0, 1, 4)

    form_box.setLayout(grid)
    layout.addWidget(form_box)

    layout.addWidget(QLabel("👨‍🏫 لیست اساتید و کارمندان مکتب:"))
    self.staff_table = QTableWidget()
    self.staff_table.setColumnCount(7)
    self.staff_table.setHorizontalHeaderLabels(["شناسه", "کد", "نام کامل", "سمت", "تلفن", "معاش", "پرداخت معاش"])
    self.staff_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    layout.addWidget(self.staff_table)

    tab.setLayout(layout)
    self.tabs.addTab(tab, "👨‍🏫 پرسنل و اساتید")
    self.load_staff_table()

def save_staff(self):
    s_no = self.txt_staff_no.text().strip()
    name = self.txt_staff_name.text().strip()
    salary = float(self.txt_staff_salary.text().strip() or 0)
    
    if not s_no or not name:
        QMessageBox.warning(self, "خطا", "کد و نام پرسنل ضروری است.")
        return

    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO staff (staff_no, full_name, role_type, phone, salary, registration_date) VALUES (?, ?, ?, ?, ?, ?)",
                       (s_no, name, self.combo_staff_role.currentText(), self.txt_staff_phone.text().strip(), salary, self.txt_staff_regdate.text().strip()))
        conn.commit()
        QMessageBox.information(self, "موفقیت", "پرونده پرسنل ثبت گردید.")
        self.txt_staff_no.clear(); self.txt_staff_name.clear(); self.txt_staff_salary.clear(); self.txt_staff_phone.clear()
        self.load_staff_table()
    except Exception as e:
        QMessageBox.critical(self, "خطا", f"خطا در ثبت: {e}")
    finally:
        conn.close()

def load_staff_table(self):
    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT staff_id, staff_no, full_name, role_type, phone, salary FROM staff")
    rows = cursor.fetchall()
    conn.close()

    self.staff_table.setRowCount(len(rows))
    for r_idx, row in enumerate(rows):
        st_id = row[0]
        for c_idx in range(6):
            val = row[c_idx]
            if c_idx == 5: val = f"{val:,.2f}"
            self.staff_table.setItem(r_idx, c_idx, QTableWidgetItem(str(val)))
        
        btn_pay = QPushButton("💸 پرداخت معاش")
        btn_pay.setStyleSheet("background-color: #1976d2; color: white; border-radius: 4px; font-weight: bold;")
        btn_pay.clicked.connect(lambda checked, sid=st_id: self.pay_staff_salary(sid))
        self.staff_table.setCellWidget(r_idx, 6, btn_pay)

def pay_staff_salary(self, staff_id):
    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT full_name, salary FROM staff WHERE staff_id = ?", (staff_id,))
    s_data = cursor.fetchone()
    conn.close()

    if not s_data: return
    name, default_salary = s_data

    dlg = QDialog(self)
    dlg.setWindowTitle(f"پرداخت معاش به {name}")
    dlg.resize(400, 250)
    dlg_layout = QVBoxLayout(dlg)

    txt_amt = ZoomableLineEdit(str(default_salary))
    today_shamsi = jdatetime.date.today().strftime("%Y/%m/%d")
    txt_d = ZoomableLineEdit(today_shamsi)
    txt_desc = ZoomableLineEdit("پرداخت بابت حقوق/معاش ماهانه")

    dlg_layout.addWidget(QLabel(f"مبلغ پرداختی به {name}:")); dlg_layout.addWidget(txt_amt)
    dlg_layout.addWidget(QLabel("تاریخ:")); dlg_layout.addWidget(txt_d)
    dlg_layout.addWidget(QLabel("توضیحات:")); dlg_layout.addWidget(txt_desc)

    btn_confirm = QPushButton("ثبت و کسر از صندوق")
    btn_confirm.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 8px;")
    
    def process_staff_pay():
        amt = float(txt_amt.text().strip() or 0)
        d_str = txt_d.text().strip()
        if amt <= 0: return
        
        conn = sqlite3.connect("school_finance.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO staff_payments (staff_id, date, trans_type, amount, description, user_name) VALUES (?, ?, 'پرداخت حقوق', ?, ?, ?)",
                       (staff_id, d_str, amt, txt_desc.text().strip(), self.user_full_name))
        
        cursor.execute("INSERT INTO cashbox (date, type, category, amount, description, user_name) VALUES (?, 'Outflow', 'پرداخت پرسنل', ?, ?, ?)",
                       (d_str, amt, f"پرداخت معاش به {name} - {txt_desc.text().strip()}", self.user_full_name))
        conn.commit(); conn.close()
        QMessageBox.information(dlg, "موفقیت", "معاش با موفقیت پرداخت و در صندوق ثبت شد.")
        dlg.accept()

    btn_confirm.clicked.connect(process_staff_pay)
    dlg_layout.addWidget(btn_confirm)
    dlg.exec()

# --------------------------------------------------------------------------
# TAB 7: SCHOOL EXPENSES
# --------------------------------------------------------------------------
def init_expenses_tab(self):
    tab = QWidget()
    layout = QVBoxLayout()
    layout.setContentsMargins(20, 20, 20, 20)
    
    form_box = QGroupBox("ثبت مصرف جدید")
    form_box.setStyleSheet("font-weight: bold; color: #c62828;")
    grid = QGridLayout()

    self.combo_exp_cat = QComboBox()
    self.load_expense_categories()
    self.txt_exp_amount = ZoomableLineEdit()
    today_shamsi = jdatetime.date.today().strftime("%Y/%m/%d")
    self.txt_exp_date = ZoomableLineEdit(today_shamsi)
    self.txt_exp_desc = ZoomableLineEdit()

    grid.addWidget(QLabel("دسته‌بندی مصرف:"), 0, 0); grid.addWidget(self.combo_exp_cat, 0, 1)
    grid.addWidget(QLabel("مبلغ (افغانی):"), 0, 2); grid.addWidget(self.txt_exp_amount, 0, 3)
    grid.addWidget(QLabel("تاریخ:"), 1, 0); grid.addWidget(self.txt_exp_date, 1, 1)
    grid.addWidget(QLabel("شرح/توضیحات:"), 1, 2); grid.addWidget(self.txt_exp_desc, 1, 3)

    btn_save_exp = QPushButton("💸 ثبت مصرف و کسر از صندوق")
    btn_save_exp.setStyleSheet("background-color: #c62828; color: white; font-weight: bold; padding: 10px; border-radius: 8px;")
    btn_save_exp.clicked.connect(self.save_expense)
    grid.addWidget(btn_save_exp, 2, 0, 1, 4)

    form_box.setLayout(grid)
    layout.addWidget(form_box)

    layout.addWidget(QLabel("📋 سوابق مصارف مکتب:"))
    self.exp_table = QTableWidget()
    self.exp_table.setColumnCount(5)
    self.exp_table.setHorizontalHeaderLabels(["تاریخ", "دسته‌بندی", "مبلغ", "توضیحات", "ثبت‌کننده"])
    self.exp_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    layout.addWidget(self.exp_table)

    tab.setLayout(layout)
    self.tabs.addTab(tab, "💸 ثبت مصارف مکتب")
    self.load_expenses_table()

def load_expense_categories(self):
    self.combo_exp_cat.clear()
    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT category_name FROM expense_categories")
    for r in cursor.fetchall():
        self.combo_exp_cat.addItem(r[0])
    conn.close()

def save_expense(self):
    amt = float(self.txt_exp_amount.text().strip() or 0)
    date_str = self.txt_exp_date.text().strip()
    cat = self.combo_exp_cat.currentText()
    desc = self.txt_exp_desc.text().strip()

    if amt <= 0 or not date_str:
        QMessageBox.warning(self, "خطا", "لطفاً مبلغ و تاریخ معتبر وارد کنید.")
        return

    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO cashbox (date, type, category, amount, description, user_name) VALUES (?, 'Outflow', ?, ?, ?, ?)",
                   (date_str, cat, amt, desc, self.user_full_name))
    conn.commit(); conn.close()
    
    QMessageBox.information(self, "موفقیت", "مصرف با موفقیت ثبت گردید.")
    self.txt_exp_amount.clear(); self.txt_exp_desc.clear()
    self.load_expenses_table()

def load_expenses_table(self):
    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT date, category, amount, description, user_name FROM cashbox WHERE type='Outflow' AND category != 'پرداخت پرسنل'")
    rows = cursor.fetchall()
    conn.close()

    self.exp_table.setRowCount(len(rows))
    for r_idx, row in enumerate(rows):
        for c_idx, val in enumerate(row):
            if c_idx == 2: val = f"{val:,.2f}"
            self.exp_table.setItem(r_idx, c_idx, QTableWidgetItem(str(val)))

# --------------------------------------------------------------------------
# TAB 8: ADVANCED REPORTS
# --------------------------------------------------------------------------
def init_reports_tab(self):
    tab = QWidget()
    layout = QVBoxLayout()
    layout.setContentsMargins(20, 20, 20, 20)
    
    filter_layout = QHBoxLayout()
    self.combo_rep_type = QComboBox()
    self.combo_rep_type.setStyleSheet("font-size: 13px; padding: 5px; border-radius: 6px;")
    self.combo_rep_type.addItems([
        "گزارش لیست دانش‌آموزان (با تاریخ ثبت‌نام)", 
        "گزارش باقی‌داری شاگردان (از بیشترین به کمترین)",
        "گزارش مصارف مکتب",
        "گزارش پرداختی‌ها و درآمدها"
    ])

    btn_gen_rep = QPushButton("نمایش گزارش")
    btn_gen_rep.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold; padding: 8px 16px; font-size: 13px; border-radius: 6px;")
    btn_gen_rep.clicked.connect(self.generate_reports)
    
    btn_print_rep = QPushButton("🖨️ چاپ این گزارش")
    btn_print_rep.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 8px 16px; font-size: 13px; border-radius: 6px;")
    btn_print_rep.clicked.connect(self.print_current_report)

    filter_layout.addWidget(QLabel("نوع گزارش:"))
    filter_layout.addWidget(self.combo_rep_type)
    filter_layout.addWidget(btn_gen_rep)
    filter_layout.addWidget(btn_print_rep)
    layout.addLayout(filter_layout)

    self.rep_table = QTableWidget()
    self.rep_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    self.rep_table.itemDoubleClicked.connect(self.on_report_item_double_clicked)
    
    layout.addWidget(self.rep_table)
    tab.setLayout(layout)
    self.tabs.addTab(tab, "📈 گزارش‌گیری و مشاهده")
    self.generate_reports()

def on_report_item_double_clicked(self, item):
    row = item.row()
    rep_type = self.combo_rep_type.currentText()
    if "دانش‌آموزان" in rep_type or "باقی‌داری شاگردان" in rep_type:
        student_id = self.rep_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if student_id:
            StudentProfileWindow(student_id, self.user_full_name, self).exec()

def generate_reports(self):
    rep_type = self.combo_rep_type.currentText()
    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    
    if "دانش‌آموزان (با تاریخ ثبت‌نام)" in rep_type:
        cursor.execute("SELECT student_id, student_no, full_name, father_name, class_name, standard_fee, is_free, uses_transport, transport_fee, registration_date, initial_previous_debt, initial_books_debt, initial_uniform_debt, initial_transport_debt FROM students")
        raw_rows = cursor.fetchall()
        rows = []
        for r in raw_rows:
            s_id, no, name, father, cls, fee, is_free, uses_t, t_fee, reg_date, p_debt, b_debt, u_debt, tr_debt = r
            if is_free == 1:
                fee = 0.0
            active_m = calculate_active_months(s_id, reg_date)
            calc_tuition = fee * active_m
            calc_transport = (t_fee * active_m) if uses_t == 1 else 0.0

            cursor.execute("SELECT SUM(amount) FROM student_payments WHERE student_id = ?", (s_id,))
            paid_tot = cursor.fetchone()[0] or 0.0

            gross_d = (p_debt + calc_tuition + calc_transport + b_debt + u_debt + tr_debt)
            net_d = max(0, gross_d - paid_tot)
            d_name = name + " (رایگان)" if is_free == 1 else name
            rows.append((no, d_name, father, cls, reg_date, f"{net_d:,.2f}", s_id))

        self.rep_table.setColumnCount(7)
        self.rep_table.setHorizontalHeaderLabels(["نمبر آی‌دی", "نام کامل", "نام پدر", "صنف", "تاریخ ثبت‌نام", "مجموع باقی‌داری", "پرونده"])

    elif "باقی‌داری شاگردان (از بیشترین به کمترین)" in rep_type:
        cursor.execute("SELECT student_id, student_no, full_name, father_name, father_phone, standard_fee, is_free, uses_transport, transport_fee, registration_date, initial_previous_debt, initial_books_debt, initial_uniform_debt, initial_transport_debt FROM students")
        raw_rows = cursor.fetchall()
        rows = []
        for r in raw_rows:
            s_id, no, name, father, fphone, fee, is_free, uses_t, t_fee, reg_date, p_debt, b_debt, u_debt, tr_debt = r
            if is_free == 1:
                fee = 0.0
            active_m = calculate_active_months(s_id, reg_date)
            calc_tuition = fee * active_m
            calc_transport = (t_fee * active_m) if uses_t == 1 else 0.0

            cursor.execute("SELECT SUM(amount) FROM student_payments WHERE student_id = ?", (s_id,))
            paid_tot = cursor.fetchone()[0] or 0.0

            gross_d = (p_debt + calc_tuition + calc_transport + b_debt + u_debt + tr_debt)
            net_d = max(0, gross_d - paid_tot)
            d_name = name + " (رایگان)" if is_free == 1 else name
            rows.append((no, d_name, father, fphone, net_d, s_id))
        
        rows.sort(key=lambda x: x[4], reverse=True)
        rows = [(r[0], r[1], r[2], r[3], f"{r[4]:,.2f}", r[5]) for r in rows]

        self.rep_table.setColumnCount(6)
        self.rep_table.setHorizontalHeaderLabels(["آی‌دی", "نام کامل", "نام پدر", "تلفن پدر", "مقدار کل باقی‌داری", "پرونده"])

    elif "مصارف مکتب" in rep_type:
        cursor.execute("SELECT date, category, amount, description, user_name FROM cashbox WHERE type='Outflow' AND category != 'پرداخت پرسنل'")
        rows = cursor.fetchall()
        self.rep_table.setColumnCount(5)
        self.rep_table.setHorizontalHeaderLabels(["تاریخ", "دسته‌بندی مصرف", "مبلغ", "تشریحات", "کاربر"])

    elif "پرداختی‌ها و درآمدها" in rep_type:
        cursor.execute("SELECT date, category, amount, description, user_name FROM cashbox WHERE type='Inflow'")
        rows = cursor.fetchall()
        self.rep_table.setColumnCount(5)
        self.rep_table.setHorizontalHeaderLabels(["تاریخ", "نوع درآمد / فیس", "مبلغ", "توضیحات", "کاربر"])

    conn.close()

    self.rep_table.setRowCount(len(rows))
    is_student_rep = ("دانش‌آموزان" in rep_type or "باقی‌داری شاگردان" in rep_type)

    for r_idx, row in enumerate(rows):
        col_limit = (len(row) - 1) if is_student_rep else len(row)
        
        for c_idx in range(col_limit):
            item = QTableWidgetItem(str(row[c_idx]))
            if is_student_rep:
                s_id = row[-1]
                item.setData(Qt.ItemDataRole.UserRole, s_id)
            self.rep_table.setItem(r_idx, c_idx, item)

        if is_student_rep:
            s_id = row[-1]
            btn_profile = QPushButton("📋 مشاهده پرونده")
            btn_profile.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold; border-radius: 6px; padding: 4px;")
            btn_profile.clicked.connect(lambda checked, sid=s_id: StudentProfileWindow(sid, self.user_full_name, self).exec())
            self.rep_table.setCellWidget(r_idx, col_limit, btn_profile)

def print_current_report(self):
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    dialog = QPrintDialog(printer, self)
    if dialog.exec() == QPrintDialog.DialogCode.Accepted:
        document = QTextDocument()
        rep_title = self.combo_rep_type.currentText()
        
        html = f"<h1 style='text-align: center;'>مکتب خصوصی کاوشگران دانش بلخ</h1>"
        html += f"<h2 style='text-align: center;'>{rep_title}</h2>"
        html += "<table border='1' cellspacing='0' cellpadding='6' width='100%' style='border-collapse: collapse; direction: rtl;'>"
        html += "<tr style='background-color: #f2f2f2; font-weight: bold;'>"
        
        for c in range(self.rep_table.columnCount()):
            html += f"<th>{self.rep_table.horizontalHeaderItem(c).text()}</th>"
        html += "</tr>"
        
        for r in range(self.rep_table.rowCount()):
            html += "<tr>"
            for c in range(self.rep_table.columnCount()):
                widget = self.rep_table.cellWidget(r, c)
                val = "پرونده" if widget else (self.rep_table.item(r, c).text() if self.rep_table.item(r, c) else "")
                html += f"<td style='text-align: center;'>{val}</td>"
            html += "</tr>"
        html += "</table>"
        
        document.setHtml(html)
        document.print(printer)
        QMessageBox.information(self, "موفقیت", "گزارش برای چاپ ارسال گردید.")

# --------------------------------------------------------------------------
# TAB 9: CASHBOX LOGS
# --------------------------------------------------------------------------
def init_cashbox_tab(self):
    tab = QWidget()
    layout = QVBoxLayout()
    layout.setContentsMargins(20, 20, 20, 20)
    
    layout.addWidget(QLabel("💰 صورتحساب و گردش صندوق:"))
    self.cash_table = QTableWidget()
    self.cash_table.setColumnCount(6)
    self.cash_table.setHorizontalHeaderLabels(["تاریخ", "نوع", "دسته‌بندی", "مبلغ (افغانی)", "توضیحات", "کاربر ثبت‌کننده"])
    self.cash_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    
    layout.addWidget(self.cash_table)
    tab.setLayout(layout)
    self.tabs.addTab(tab, "💰 مدیریت صندوق")
    self.load_cashbox_table()

def load_cashbox_table(self):
    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT date, type, category, amount, description, user_name FROM cashbox ORDER BY transaction_id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    self.cash_table.setRowCount(len(rows))
    for r_idx, row in enumerate(rows):
        for c_idx, val in enumerate(row):
            if c_idx == 1:
                val = "درآمد (+)" if val == "Inflow" else "مصرف (-)"
            elif c_idx == 3:
                val = f"{val:,.2f}"
            self.cash_table.setItem(r_idx, c_idx, QTableWidgetItem(str(val)))

# --------------------------------------------------------------------------
# TAB 10: SETTINGS & BACKUPS
# --------------------------------------------------------------------------
def init_settings_tab(self):
    tab = QWidget()
    layout = QVBoxLayout()
    layout.setContentsMargins(20, 20, 20, 20)
    
    box_backup = QGroupBox("مدیریت فایل دیتابیس و پشتیبان‌گیری")
    box_backup.setStyleSheet("font-weight: bold; color: #0d47a1;")
    b_layout = QHBoxLayout()
    
    btn_backup = QPushButton("💾 پشتیبان‌گیری از دیتابیس")
    btn_backup.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
    btn_backup.clicked.connect(self.create_db_backup)

    btn_restore = QPushButton("📂 بازگردانی فایل دیتابیس")
    btn_restore.setStyleSheet("background-color: #e65100; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
    btn_restore.clicked.connect(self.restore_db_backup)

    b_layout.addWidget(btn_backup)
    b_layout.addWidget(btn_restore)
    box_backup.setLayout(b_layout)
    layout.addWidget(box_backup)

    box_classes = QGroupBox("مدیریت اصناف مکتب")
    box_classes.setStyleSheet("font-weight: bold; color: #0d47a1;")
    c_layout = QHBoxLayout()
    self.txt_new_class = ZoomableLineEdit(); self.txt_new_class.setPlaceholderText("نام صنف جدید...")
    btn_add_cls = QPushButton("➕ افزودن صنف")
    btn_add_cls.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 6px 12px; border-radius: 6px;")
    btn_add_cls.clicked.connect(self.add_class_item)
    c_layout.addWidget(self.txt_new_class); c_layout.addWidget(btn_add_cls)
    box_classes.setLayout(c_layout)
    layout.addWidget(box_classes)

    layout.addStretch()
    tab.setLayout(layout)
    self.tabs.addTab(tab, "⚙️ تنظیمات سیستم")

def create_db_backup(self):
    file_path, _ = QFileDialog.getSaveFileName(self, "ذخیره فایل پشتیبان", "school_finance_backup.db", "Database Files (*.db)")
    if file_path:
        shutil.copy("school_finance.db", file_path)
        QMessageBox.information(self, "موفقیت", "نسخه پشتیبان دیتابیس با موفقیت ذخیره شد.")

def restore_db_backup(self):
    file_path, _ = QFileDialog.getOpenFileName(self, "انتخاب فایل دیتابیس", "", "Database Files (*.db)")
    if file_path:
        confirm = QMessageBox.question(self, "تایید بازگردانی", "با بازگردانی فایل، اطلاعات فعلی جایگزین می‌شود. آیا ادامه می‌دهید؟", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            shutil.copy(file_path, "school_finance.db")
            QMessageBox.information(self, "موفقیت", "دیتابیس جدید جایگزین شد. سیستم به‌روزرسانی می‌شود.")

def add_class_item(self):
    c_name = self.txt_new_class.text().strip()
    if not c_name: return
    conn = sqlite3.connect("school_finance.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO classes (class_name) VALUES (?)", (c_name,))
        conn.commit()
        QMessageBox.information(self, "موفقیت", "صنف جدید اضافه شد.")
        self.txt_new_class.clear()
        self.load_classes_into_combo(self.reg_class)
        self.load_classes_into_combo(self.combo_att_class)
        self.load_classes_into_combo(self.combo_eval_class)
    except:
        QMessageBox.warning(self, "خطا", "این صنف قبلاً ثبت شده است.")
    finally:
        conn.close()

# --------------------------------------------------------------------------
# TAB 11: HELP & DOCUMENTATION
# --------------------------------------------------------------------------
def init_help_tab(self):
    tab = QWidget()
    layout = QVBoxLayout()
    layout.setContentsMargins(20, 20, 20, 20)
    
    help_browser = QTextBrowser()
    help_browser.setStyleSheet("background-color: #ffffff; padding: 20px; font-family: Tahoma; font-size: 13px; line-height: 1.6;")
    
    html_content = """
    <h1 style='color: #0d47a1; text-align: center;'>📖 راهنمای سیستم مدیریت مکتب کاوشگران دانش بلخ</h1>
    <hr style='border: 1px solid #1976d2;'>
    <p style='font-size: 14px;'>این نرم‌افزار جهت ارتقای دقت، سرعت و شفافیت حسابداری و اداری مکتب طراحی شده است.</p>
    <h3>قابلیت‌های کلیدی:</h3>
    <ul>
        <li><b>محاسبه خودکار بدهی:</b> سیستم به طور هوشمند ماه‌های فعال دانش‌آموز را بر اساس تاریخ ثبت‌نام و کسر ماه‌های مرخصی (Break) محاسبه می‌کند.</li>
        <li><b>حاضری و ارزیابی روزانه:</b> امکان ثبت نمرات ارزیابی، اجندا، تکالیف و وضعیت حضور و غیاب شاگردان.</li>
        <li><b>حسابداری جامع:</b> کنترل ریز درآمدها، پرداختی‌های فیس، حقوق پرسنل و مصارف تفکیک‌شده.</li>
        <li><b>زوم هوشمند:</b> با نگه‌داشتن کلید Ctrl و چرخاندن چرخ‌دنده ماوس روی ورودی‌ها، اندازه قلم متون بزرگ یا کوچک می‌شود.</li>
    </ul>
    """
    help_browser.setHtml(html_content)
    layout.addWidget(help_browser)
    tab.setLayout(layout)
    self.tabs.addTab(tab, "📖 راهنما")

