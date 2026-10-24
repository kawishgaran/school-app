import streamlit as st
import sqlite3
import jdatetime
import pandas as pd
import math
import shutil

# ==================== تنظیمات صفحه ====================
st.set_page_config(
    page_title="مکتب خصوصی کاوشگران دانش بلخ",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "school_finance.db"

# ==================== استایل‌دهی و راست‌چین‌سازی کامل (RTL) ====================
st.markdown("""
<style>
    @import url('https://v1.fontapi.ir/css/Vazir');
    
    html, body, [class*="css"], [class*="st-"] {
        font-family: 'Vazir', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }

    section[data-testid="stSidebar"] {
        direction: rtl !important;
        text-align: right !important;
    }

    .stTextInput>div>div>input, 
    .stSelectbox>div>div, 
    .stNumberInput>div>div>input,
    .stTextArea>div>div>textarea {
        direction: rtl !important;
        text-align: right !important;
    }

    .stButton>button {
        background-color: #0d47a1 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        width: 100%;
        font-weight: bold;
        padding: 8px;
    }
    .stButton>button:hover {
        background-color: #1565c0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== مقداردهی اولیه دیتابیس ====================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    
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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY(student_id) REFERENCES students(student_id)
        )
    ''')

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

    try:
        cursor.execute("ALTER TABLE students ADD COLUMN is_free INTEGER DEFAULT 0")
    except:
        pass
    
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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            class_id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT UNIQUE NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expense_categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE NOT NULL
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, password, full_name, role) VALUES ('admin', 'admin123', 'مدیر کل سیستم', 'Admin')")
        cursor.execute("INSERT INTO users (username, password, full_name, role) VALUES ('finance', 'finance123', 'مدیر مالی', 'Financial_Manager')")

    cursor.execute("SELECT COUNT(*) FROM classes")
    if cursor.fetchone()[0] == 0:
        default_classes = ["صنف اول", "صنف دوم", "صنف سوم", "صنف چهارم", "صنف پنجم", "صنف ششم", "صنف هفتم", "صنف هشتم", "صنف نهم", "صنف دهم", "صنف یازدهم", "صنف دوازدهم", "آمادگی"]
        for c in default_classes:
            cursor.execute("INSERT OR IGNORE INTO classes (class_name) VALUES (?)", (c,))

    cursor.execute("SELECT COUNT(*) FROM expense_categories")
    if cursor.fetchone()[0] == 0:
        default_cats = ["خرید وسایل و تجهیزات", "ترمیم وسایط و موترها", "مصارف برق و آب", "لوازم‌التحریر", "سایر مصارف"]
        for cat in default_cats:
            cursor.execute("INSERT OR IGNORE INTO expense_categories (category_name) VALUES (?)", (cat,))

    conn.commit()
    conn.close()

init_db()

# ==================== توابع محاسباتی ====================
def parse_shamsi_date(date_str):
    try:
        clean_str = str(date_str).replace('-', '/').strip()
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

    conn = sqlite3.connect(DB_FILE)
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

def get_student_financial_summary(student_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT standard_fee, is_free, uses_transport, transport_fee, 
               registration_date, initial_previous_debt, initial_books_debt, initial_uniform_debt, initial_transport_debt 
        FROM students WHERE student_id = ?
    ''', (student_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
        
    fee, is_free, uses_t, t_fee, reg_date, p_debt, b_debt, u_debt, tr_debt = row
    if is_free == 1:
        fee = 0.0
        
    active_m = calculate_active_months(student_id, reg_date)
    calc_tuition = fee * active_m
    calc_transport = (t_fee * active_m) if uses_t == 1 else 0.0
    
    gross_debt = p_debt + calc_tuition + calc_transport + b_debt + u_debt + tr_debt
    
    cursor.execute("SELECT SUM(amount) FROM student_payments WHERE student_id = ?", (student_id,))
    total_paid = cursor.fetchone()[0] or 0.0
    conn.close()
    
    if total_paid > gross_debt:
        net_debt = 0.0
        advance_pay = total_paid - gross_debt
    else:
        net_debt = gross_debt - total_paid
        advance_pay = 0.0
        
    return {
        "active_months": active_m,
        "monthly_fee": fee,
        "calc_tuition": calc_tuition,
        "calc_transport": calc_transport,
        "previous_debt": p_debt,
        "books_debt": b_debt,
        "uniform_debt": u_debt,
        "transport_debt": tr_debt,
        "gross_debt": gross_debt,
        "total_paid": total_paid,
        "net_debt": net_debt,
        "advance_pay": advance_pay
    }

# ==================== احراز هویت ====================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_name = ""
    st.session_state.user_role = ""

if not st.session_state.logged_in:
    st.title("🏫 ورود به سیستم - مکتب خصوصی کاوشگران دانش بلخ")
    with st.form("login_form"):
        u = st.text_input("👤 نام کاربری")
        p = st.text_input("🔒 رمز عبور", type="password")
        submit = st.form_submit_button("ورود به سیستم")
        if submit:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT full_name, role FROM users WHERE username = ? AND password = ?", (u, p))
            user = cursor.fetchone()
            conn.close()
            if user:
                st.session_state.logged_in = True
                st.session_state.user_name = user[0]
                st.session_state.user_role = user[1]
                st.rerun()
            else:
                st.error("نام کاربری یا رمز عبور اشتباه است!")
else:
    st.sidebar.markdown(f"👤 **کاربر فعال:** {st.session_state.user_name} ({st.session_state.user_role})")
    
    menu_options = [
        "📊 داشبورد مدیریتی",
        "➕ ثبت‌نام جدید شاگرد", 
        "📝 حاضری روزانه", 
        "⭐ ارزیابی شاگردان", 
        "👨‍🏫 پرسنل و استادان", 
        "💸 ثبت مصارف مکتب", 
        "🔍 جستجو و پرونده شاگردان", 
        "📈 گزارش‌گیری پیشرفته", 
        "💰 مدیریت صندوق", 
        "👥 کاربران سیستم",
        "⚙️ تنظیمات سیستم",
        "📖 راهنما"
    ]
    
    menu = st.sidebar.selectbox("📌 منوی اصلی سیستم:", menu_options)
    
    if st.sidebar.button("🚪 خروج از سیستم"):
        st.session_state.logged_in = False
        st.session_state.user_name = ""
        st.session_state.user_role = ""
        st.rerun()

    conn = sqlite3.connect(DB_FILE)

    # ==================== ۱. داشبورد مدیریتی ====================
    if menu == "📊 داشبورد مدیریتی":
        st.title("📊 داشبورد مدیریتی مکتب خصوصی کاوشگران دانش بلخ")
        
        col_b1, col_b2 = st.columns([1, 3])
        with col_b1:
            if st.button("💾 پشتیبان‌گیری دیتابیس"):
                try:
                    backup_name = f"school_finance_backup_{jdatetime.date.today().strftime('%Y%m%d_%H%M%S')}.db"
                    shutil.copy(DB_FILE, backup_name)
                    st.success(f"فایل پشتیبان ذخیره شد: {backup_name}")
                except Exception as e:
                    st.error(f"خطا در ایجاد پشتیبان: {e}")

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM students WHERE status='فعال'")
        s_count = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(amount) FROM cashbox WHERE type='Inflow'")
        inflow = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(amount) FROM cashbox WHERE type='Outflow'")
        outflow = cursor.fetchone()[0] or 0
        total_cash = inflow - outflow
        
        cursor.execute("SELECT student_id, standard_fee, is_free, uses_transport, transport_fee, registration_date, initial_previous_debt, initial_books_debt, initial_uniform_debt, initial_transport_debt FROM students")
        all_st = cursor.fetchall()
        total_debts = 0
        for st_row in all_st:
            s_id, fee, is_free, uses_t, t_fee, reg_date, p_debt, b_debt, u_debt, tr_debt = st_row
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

        col1, col2, col3 = st.columns(3)
        col1.metric("دانش‌آموزان فعال", f"{s_count} نفر")
        col2.metric("موجودی فعلی صندوق", f"{total_cash:,.2f} افغانی")
        col3.metric("مجموع باقی‌داری‌ها", f"{total_debts:,.2f} افغانی")

        st.markdown("---")
        st.subheader("⚙️ تنظیم تراز دستی صندوق")
        col_m1, col_m2 = st.columns([2, 1])
        with col_m1:
            manual_new_cash = st.number_input("مبلغ جدید برای صندوق (افغانی):", min_value=0.0, value=float(total_cash))
        with col_m2:
            st.write("")
            if st.button("🔄 اعمال تنظیم تراز"):
                diff = manual_new_cash - total_cash
                if diff != 0:
                    t_type = "Inflow" if diff > 0 else "Outflow"
                    cursor.execute("INSERT INTO cashbox (date, type, category, amount, description, user_name) VALUES (date('now'), ?, 'تنظیم تراز دستی', ?, 'اصلاح دستی تراز حساب صندوق توسط مدیر', ?)",
                                   (t_type, abs(diff), st.session_state.user_name))
                    conn.commit()
                    st.success("تراز صندوق تنظیم شد.")
                    st.rerun()

    # ==================== ۲. ثبت‌نام جدید شاگرد ====================
    elif menu == "➕ ثبت‌نام جدید شاگرد":
        st.title("🎓 فرم ثبت‌نام دانش‌آموز جدید")
        
        cursor = conn.cursor()
        cursor.execute("SELECT class_name FROM classes")
        classes = [row[0] for row in cursor.fetchall()]

        with st.form("reg_form"):
            st.subheader("👤 معلومات شخصی شاگرد")
            col1, col2 = st.columns(2)
            with col1:
                reg_no = st.text_input("نمبر آی‌دی *")
                reg_name = st.text_input("نام کامل شاگرد *")
                reg_father = st.text_input("نام پدر *")
                reg_gfather = st.text_input("نام پدرکلان")
            with col2:
                reg_class = st.selectbox("صنف انتخابی", classes)
                reg_fee = st.number_input("شهریه ماهانه (افغانی)", min_value=0.0, value=1000.0)
                reg_chk_free = st.checkbox("شاگرد رایگان (معاف از شهریه)")
                reg_date = st.text_input("تاریخ ثبت‌نام", value=jdatetime.date.today().strftime("%Y/%m/%d"))

            col3, col4 = st.columns(2)
            with col3:
                reg_fphone = st.text_input("شماره تماس پدر")
                reg_prev_debt = st.number_input("باقی‌داری قبلی", min_value=0.0, value=0.0)
            with col4:
                reg_mphone = st.text_input("شماره تماس مادر")

            st.markdown("---")
            st.subheader("🚌 خدمات ترانسپورت و مسیر")
            reg_chk_trans = st.checkbox("استفاده از سیستم ترانسپورت مکتب")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                reg_route = st.text_input("مسیر ترانسپورت")
            with col_t2:
                reg_tfee = st.number_input("کرایه ماهانه ترانسپورت", min_value=0.0, value=0.0)

            st.markdown("---")
            st.subheader("📚 کتاب و لباس (دریشی)")
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                reg_chk_books = st.checkbox("تحویل کتاب‌های مکتب")
                reg_bfee = st.number_input("قیمت کتاب", min_value=0.0, value=0.0)
                reg_bstatus = st.selectbox("وضعیت پرداخت کتاب", ["پرداخت شده", "باقی‌دار"])
            with col_b2:
                reg_chk_uniform = st.checkbox("تحویل لباس مکتب (دریشی)")
                reg_ufee = st.number_input("قیمت لباس", min_value=0.0, value=0.0)
                reg_ustatus = st.selectbox("وضعیت پرداخت لباس", ["پرداخت شده", "باقی‌دار"])

            submit_reg = st.form_submit_button("📝 ثبت نهایی دانش‌آموز در سیستم")
            if submit_reg:
                if reg_no and reg_name and reg_father and reg_date:
                    try:
                        cursor.execute("SELECT student_no FROM students WHERE student_no = ?", (reg_no,))
                        if cursor.fetchone():
                            st.error(f"شماره آی‌دی «{reg_no}» قبلاً ثبت شده است!")
                        else:
                            final_fee = 0.0 if reg_chk_free else reg_fee
                            is_f = 1 if reg_chk_free else 0
                            uses_t = 1 if reg_chk_trans else 0
                            takes_b = 1 if reg_chk_books else 0
                            takes_u = 1 if reg_chk_uniform else 0
                            
                            b_debt = reg_bfee if (takes_b and reg_bstatus == "باقی‌دار") else 0.0
                            u_debt = reg_ufee if (takes_u and reg_ustatus == "باقی‌دار") else 0.0

                            cursor.execute('''
                                INSERT INTO students (
                                    student_no, full_name, father_name, grandfather_name, class_name, standard_fee, is_free,
                                    father_phone, mother_phone, uses_transport, transport_route, transport_fee,
                                    takes_books, books_fee, books_payment_status, takes_uniform, uniform_fee, uniform_payment_status,
                                    initial_previous_debt, initial_books_debt, initial_uniform_debt, status, registration_date
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'فعال', ?)
                            ''', (reg_no, reg_name, reg_father, reg_gfather, reg_class, final_fee, is_f,
                                  reg_fphone, reg_mphone, uses_t, reg_route if uses_t else "", reg_tfee if uses_t else 0.0,
                                  takes_b, reg_bfee if takes_b else 0.0, reg_bstatus, takes_u, reg_ufee if takes_u else 0.0, reg_ustatus,
                                  reg_prev_debt, b_debt, u_debt, reg_date))
                            conn.commit()
                            st.success("دانش‌آموز با موفقیت ثبت شد!")
                    except Exception as e:
                        st.error(f"خطا در ثبت اطلاعات: {e}")
                else:
                    st.warning("لطفاً فیلدهای ضروری را تکمیل کنید.")

    # ==================== ۳. حاضری روزانه ====================
    elif menu == "📝 حاضری روزانه":
        st.title("📋 سیستم ثبت حضور و غیاب (حاضری) روزانه شاگردان")
        
        cursor = conn.cursor()
        cursor.execute("SELECT class_name FROM classes")
        classes = [row[0] for row in cursor.fetchall()]
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            sel_class = st.selectbox("انتخاب صنف:", classes)
        with col_f2:
            att_date = st.text_input("تاریخ حاضری:", value=jdatetime.date.today().strftime("%Y/%m/%d"))

        cursor.execute("SELECT student_id, student_no, full_name, father_name FROM students WHERE class_name = ? AND status='فعال'", (sel_class,))
        students = cursor.fetchall()

        cursor.execute("SELECT student_id, status FROM attendance WHERE date = ?", (att_date,))
        saved_records = {row[0]: row[1] for row in cursor.fetchall()}

        if students:
            with st.form("attendance_form"):
                att_data = []
                for s_id, no, name, father in students:
                    default_idx = 0
                    if s_id in saved_records:
                        prev = saved_records[s_id]
                        if "غیرحاضر" in prev: default_idx = 1
                        elif "رخصتی" in prev: default_idx = 2

                    status = st.selectbox(f"{name} (پدر: {father} - آی‌دی: {no})", ["حاضر ✅", "غیرحاضر ❌", "رخصتی 📌"], index=default_idx, key=f"att_{s_id}")
                    att_data.append((s_id, status))

                submit_att = st.form_submit_button("💾 ثبت نهایی حاضری امروز")
                if submit_att:
                    for s_id, status in att_data:
                        cursor.execute("SELECT attendance_id FROM attendance WHERE student_id = ? AND date = ?", (s_id, att_date))
                        ex = cursor.fetchone()
                        if ex:
                            cursor.execute("UPDATE attendance SET status = ? WHERE attendance_id = ?", (status, ex[0]))
                        else:
                            cursor.execute("INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)", (s_id, att_date, status))
                    conn.commit()
                    st.success("حاضری شاگردان با موفقیت ثبت شد.")
        else:
            st.info("هیچ شاگرد فعالی در این صنف یافت نشد.")

    # ==================== ۴. ارزیابی شاگردان ====================
    elif menu == "⭐ ارزیابی شاگردان":
        st.title("⭐ سیستم ارزیابی اتوماتیک ماهانه کل شاگردان (بدون روزهای جمعه)")
        
        eval_date = st.text_input("تاریخ ارزیابی امروز:", value=jdatetime.date.today().strftime("%Y/%m/%d"))
        
        y, m, d = parse_shamsi_date(eval_date)
        is_friday = False
        if y and m and d:
            try:
                dt = jdatetime.date(y, m, d)
                if dt.weekday() == 6:
                    is_friday = True
            except:
                pass

        if is_friday:
            st.warning("📌 امروز جمعه است! طبق دستورالعمل، روزهای جمعه ارزیابی انجام نمی‌شود.")
        else:
            cursor = conn.cursor()
            cursor.execute("SELECT student_id, student_no, full_name, father_name, class_name FROM students WHERE status='فعال' ORDER BY student_id ASC")
            all_students = cursor.fetchall()
            
            if all_students:
                total_s = len(all_students)
                working_days = 26
                daily_quota = math.ceil(total_s / float(working_days))

                cursor.execute("SELECT DISTINCT student_id FROM evaluations WHERE substr(date, 1, 7) = ?", (f"{y:04d}/{m:02d}",))
                already_eval = {row[0] for row in cursor.fetchall()}
                rem_st = [st for st in all_students if st[0] not in already_eval]
                target_list = rem_st if rem_st else all_students
                today_batch = target_list[:daily_quota]

                st.info(f"کل شاگردان: {total_s} | سهمیه روزانه: {daily_quota} نفر | نوبت ارزیابی امروز: {len(today_batch)} شاگرد")

                with st.form("eval_form"):
                    eval_scores = []
                    for st_row in today_batch:
                        s_id, no, name, father, cls_name = st_row
                        st.markdown(f"**{name}** (پدر: {father} - صنف: {cls_name})")
                        c1, c2, c3, c4, c5, c6 = st.columns(6)
                        with c1: n_ch = st.selectbox("کتابچه", ["0", "1", "2"], index=2, key=f"nc_{s_id}")
                        with c2: d_ch = st.selectbox("دایری", ["0", "1", "2"], index=2, key=f"dc_{s_id}")
                        with c3: dict_ = st.selectbox("املا", ["0", "1", "2"], index=2, key=f"dt_{s_id}")
                        with c4: learn = st.selectbox("یادگیری", ["0", "1", "2"], index=2, key=f"lr_{s_id}")
                        with c5: home = st.selectbox("خانگی", ["0", "1", "2"], index=2, key=f"hm_{s_id}")
                        with c6: oth = st.selectbox("سایر", ["0", "1", "2"], index=2, key=f"ot_{s_id}")
                        eval_scores.append((s_id, int(n_ch), int(d_ch), int(dict_), int(learn), int(home), int(oth)))
                        st.markdown("---")

                    submit_ev = st.form_submit_button("💾 ثبت نهایی ارزیابی‌های امروز")
                    if submit_ev:
                        for item in eval_scores:
                            s_id, nc, dc, dt, lr, hm, ot = item
                            total_sc = nc + dc + dt + lr + hm + ot
                            cursor.execute('''
                                INSERT INTO evaluations (student_id, date, notebook_check, diary_check, dictation, learning_level, homework, other_cases, total_score)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (s_id, eval_date, nc, dc, dt, lr, hm, ot, total_sc))
                        conn.commit()
                        st.success("ارزیابی شاگردان ثبت شد.")
            else:
                st.info("هیچ شاگرد فعالی یافت نشد.")

    # ==================== ۵. پرسنل و استادان ====================
    elif menu == "👨‍🏫 پرسنل و استادان":
        st.title("👨‍🏫 مدیریت پرسنل و استادان مکتب")
        
        with st.form("staff_form"):
            st.subheader("➕ ثبت پرسنل جدید")
            c1, c2 = st.columns(2)
            with c1:
                st_no = st.text_input("آی‌دی پرسنل *")
                st_name = st.text_input("نام کامل *")
                st_role = st.selectbox("وظیفه / سمت", ["استاد", "درایور", "گارد", "خاله مکتب", "مدیر مکتب", "سایر"])
            with c2:
                st_phone = st.text_input("تلفن")
                st_salary = st.number_input("معاش ماهانه (افغانی)", min_value=0.0, value=5000.0)
                st_date = st.text_input("تاریخ ثبت", value=jdatetime.date.today().strftime("%Y/%m/%d"))

            if st.form_submit_button("ثبت پرسنل"):
                if st_no and st_name and st_date:
                    try:
                        cursor.execute("INSERT INTO staff (staff_no, full_name, role_type, phone, salary, registration_date) VALUES (?, ?, ?, ?, ?, ?)",
                                       (st_no, st_name, st_role, st_phone, st_salary, st_date))
                        conn.commit()
                        st.success("پرسنل ثبت شد.")
                    except Exception as e:
                        st.error(f"خطا: {e}")
                else:
                    st.warning("موارد ضروری را پر کنید.")

        st.markdown("---")
        st.subheader("📋 لیست پرسنل مکتب")
        cursor.execute("SELECT staff_id, staff_no, full_name, role_type, phone, salary, registration_date FROM staff")
        staff_rows = cursor.fetchall()
        if staff_rows:
            df_st = pd.DataFrame(staff_rows, columns=["شناسه", "آی‌دی", "نام کامل", "وظیفه", "تلفن", "معاش", "تاریخ ثبت"])
            st.dataframe(df_st, use_container_width=True)

    # ==================== ۶. ثبت مصارف مکتب ====================
    elif menu == "💸 ثبت مصارف مکتب":
        st.title("💸 ثبت مصارف و هزینه‌های مکتب")
        
        cursor.execute("SELECT category_name FROM expense_categories")
        cats = [row[0] for row in cursor.fetchall()]

        with st.form("expense_form"):
            c1, c2 = st.columns(2)
            with c1:
                ex_date = st.text_input("تاریخ مصرف", value=jdatetime.date.today().strftime("%Y/%m/%d"))
                ex_cat = st.selectbox("دسته‌بندی مصرف", cats)
            with c2:
                ex_amount = st.number_input("مبلغ مصرف (افغانی)", min_value=0.0, value=0.0)
                ex_desc = st.text_input("تشریحات کامل مصرف")

            if st.form_submit_button("ثبت مصرف و کسر از صندوق"):
                if ex_amount > 0 and ex_desc:
                    cursor.execute("INSERT INTO cashbox (date, type, category, amount, description, user_name) VALUES (?, 'Outflow', ?, ?, ?, ?)",
                                   (ex_date, ex_cat, ex_amount, ex_desc, st.session_state.user_name))
                    conn.commit()
                    st.success("مصرف ثبت و از صندوق کسر گردید.")
                else:
                    st.warning("مبلغ و تشریحات را وارد کنید.")

        st.markdown("---")
        st.subheader("📋 سوابق مصارف ثبت‌شده")
        cursor.execute("SELECT date, category, amount, description, user_name FROM cashbox WHERE type='Outflow' AND category != 'پرداخت پرسنل'")
        ex_rows = cursor.fetchall()
        if ex_rows:
            st.dataframe(pd.DataFrame(ex_rows, columns=["تاریخ", "دسته‌بندی", "مبلغ", "تشریحات", "کاربر"]), use_container_width=True)

    # ==================== ۷. جستجو و پرونده شاگردان (اصلاح‌شده) ====================
    elif menu == "🔍 جستجو و پرونده شاگردان":
        st.title("🔍 جستجو و مشاهده پرونده کامل شاگردان")
        
        search_q = st.text_input("جستجو بر اساس نام شاگرد یا شماره آی‌دی:", value="")
        cursor.execute("SELECT student_id, student_no, full_name, father_name, class_name FROM students WHERE full_name LIKE ? OR student_no LIKE ?", (f"%{search_q}%", f"%{search_q}%"))
        found_students = cursor.fetchall()

        st_options = {f"{r[2]} (پدر: {r[3]} - صنف: {r[4]} - آی‌دی: {r[1]})": r[0] for r in found_students}
        sel_display = st.selectbox("انتخاب شاگرد از لیست:", options=[""] + list(st_options.keys()))
        
        target_s_id = st_options.get(sel_display) if sel_display else None

        if target_s_id:
            cursor.execute('''
                SELECT student_id, student_no, full_name, father_name, grandfather_name, class_name, standard_fee, is_free, 
                       uses_transport, transport_fee, father_phone, mother_phone, registration_date, initial_previous_debt, initial_books_debt, initial_uniform_debt 
                FROM students WHERE student_id = ?
            ''', (target_s_id,))
            s_row = cursor.fetchone()
            if s_row:
                s_id, no, name, father, gfather, cls, fee, is_free, uses_t, t_fee, fphone, mphone, reg_date, p_debt, b_debt, u_debt = s_row
                summary = get_student_financial_summary(s_id)
                
                if summary:
                    st.markdown(f"### 📂 پرونده مالی و اداری: {name} {'(معاف/رایگان)' if is_free == 1 else ''}")
                    c_inf1, c_inf2, c_inf3 = st.columns(3)
                    with c_inf1:
                        st.write(f"🆔 **آی‌دی:** {no}")
                        st.write(f"👨 **نام پدر:** {father} ({gfather})")
                        st.write(f"🏫 **صنف:** {cls}")
                    with c_inf2:
                        st.write(f"📞 **تلفن پدر:** {fphone}")
                        st.write(f"📞 **تلفن مادر:** {mphone}")
                        st.write(f"📅 **تاریخ ثبت‌نام:** {reg_date}")
                    with c_inf3:
                        st.write(f"💵 **فیس ماهانه:** {summary['monthly_fee']:,.2f} افغانی")
                        st.write(f"📆 **ماه‌های فعال:** {summary['active_months']} ماه")
                        st.write(f"🔻 **باقی‌داری کل:** <span style='color:red;'>**{summary['net_debt']:,.2f} افغانی**</span>", unsafe_allow_html=True)

                    st.markdown(f"**ریز بدهی‌ها:** [قبلی: {summary['previous_debt']:,.2f}] | [شهریه: {summary['calc_tuition']:,.2f}] | [ترانسپورت: {summary['calc_transport']:,.2f}] | [کتاب: {summary['books_debt']:,.2f}] | [لباس: {summary['uniform_debt']:,.2f}] | [بستانکاری: {summary['advance_pay']:,.2f}]")

                    tab_p, tab_b, tab_a, tab_e = st.tabs(["💳 دریافت فیس و وجه", "📌 ثبت مرخصی / Break", "📊 سوابق حاضری", "⭐ سوابق ارزیابی"])
                    
                    with tab_p:
                        with st.form(f"pay_f_{s_id}"):
                            ftype = st.selectbox("نوع فیس:", ["شهریه ماه جاری", "باقی‌داری قبلی", "ترانسپورت", "کتاب", "لباس", "پیش‌پرداخت / بستانکاری"])
                            pamt = st.number_input("مبلغ پرداختی (افغانی):", min_value=0.0)
                            pdate = st.text_input("تاریخ پرداخت:", value=jdatetime.date.today().strftime("%Y/%m/%d"))
                            pdesc = st.text_input("توضیحات:")
                            if st.form_submit_button("ثبت پرداخت"):
                                if pamt > 0:
                                    cursor.execute("INSERT INTO student_payments (student_id, date, trans_type, fee_type, amount, description, user_name) VALUES (?, ?, 'دریافت وجه', ?, ?, ?, ?)",
                                                   (s_id, pdate, ftype, pamt, pdesc, st.session_state.user_name))
                                    cursor.execute("INSERT INTO cashbox (date, type, category, amount, description, user_name) VALUES (?, 'Inflow', ?, ?, ?, ?)",
                                                   (pdate, f"دریافت {ftype}", pamt, f"پرداخت شاگرد ID:{s_id}\n{pdesc}", st.session_state.user_name))
                                    conn.commit()
                                    st.success("پرداخت ثبت شد.")
                                    st.rerun()

                        cursor.execute("SELECT date, fee_type, amount, description, user_name FROM student_payments WHERE student_id = ?", (s_id,))
                        pay_hist = cursor.fetchall()
                        if pay_hist:
                            st.dataframe(pd.DataFrame(pay_hist, columns=["تاریخ", "نوع فیس", "مبلغ", "توضیحات", "کاربر"]), use_container_width=True)

                    with tab_b:
                        with st.form(f"break_f_{s_id}"):
                            bstart = st.text_input("از تاریخ/ماه (1405/02/01)")
                            bend = st.text_input("تا تاریخ/ماه (1405/03/01)")
                            breason = st.text_input("دلیل عدم حضور:")
                            if st.form_submit_button("ثبت دوره Break"):
                                if bstart and bend:
                                    cursor.execute("INSERT INTO student_breaks (student_id, start_month, end_month, reason) VALUES (?, ?, ?, ?)",
                                                   (s_id, bstart, bend, breason))
                                    conn.commit()
                                    st.success("مرخصی ثبت شد.")
                                    st.rerun()

                        cursor.execute("SELECT break_id, start_month, end_month, reason FROM student_breaks WHERE student_id = ?", (s_id,))
                        break_hist = cursor.fetchall()
                        if break_hist:
                            st.dataframe(pd.DataFrame(break_hist, columns=["شناسه", "از تاریخ", "تا تاریخ", "دلیل"]), use_container_width=True)

                    with tab_a:
                        cursor.execute("SELECT date, status FROM attendance WHERE student_id = ?", (s_id,))
                        att_rows = cursor.fetchall()
                        if att_rows:
                            st.dataframe(pd.DataFrame(att_rows, columns=["تاریخ", "وضعیت حضور"]), use_container_width=True)

                    with tab_e:
                        cursor.execute("SELECT date, notebook_check, diary_check, dictation, learning_level, homework, other_cases, total_score FROM evaluations WHERE student_id = ?", (s_id,))
                        eval_rows = cursor.fetchall()
                        if eval_rows:
                            st.dataframe(pd.DataFrame(eval_rows, columns=["تاریخ", "کتابچه", "دایری", "املا", "یادگیری", "خانگی", "سایر", "مجموع"]), use_container_width=True)

    # ==================== ۸. گزارش‌گیری پیشرفته ====================
    elif menu == "📈 گزارش‌گیری پیشرفته":
        st.title("📈 گزارش‌گیری جامع و پیشرفته مکتب")
        
        rep_choice = st.selectbox("انتخاب نوع گزارش:", [
            "گزارش لیست دانش‌آموزان", 
            "گزارش باقی‌داری شاگردان",
            "گزارش لیست پرسنل و استادان",
            "گزارش مصارف مکتب",
            "گزارش درآمدها و پرداختی‌ها"
        ])

        if "دانش‌آموزان" in rep_choice:
            cursor.execute("SELECT student_no, full_name, father_name, class_name, registration_date, standard_fee FROM students")
            rows = cursor.fetchall()
            st.dataframe(pd.DataFrame(rows, columns=["آی‌دی", "نام کامل", "نام پدر", "صنف", "تاریخ ثبت‌نام", "شهریه"]), use_container_width=True)
        elif "باقی‌داری شاگردان" in rep_choice:
            cursor.execute("SELECT student_id, student_no, full_name, father_name, class_name FROM students")
            st_list = cursor.fetchall()
            rep_data = []
            for r in st_list:
                s_id, no, name, father, cls = r
                sum_f = get_student_financial_summary(s_id)
                if sum_f:
                    rep_data.append((no, name, father, cls, f"{sum_f['net_debt']:,.2f}"))
            st.dataframe(pd.DataFrame(rep_data, columns=["آی‌دی", "نام کامل", "نام پدر", "صنف", "باقی‌داری کل"]), use_container_width=True)
        elif "پرسنل و استادان" in rep_choice:
            cursor.execute("SELECT staff_no, full_name, role_type, phone, salary FROM staff")
            rows = cursor.fetchall()
            st.dataframe(pd.DataFrame(rows, columns=["آی‌دی", "نام کامل", "وظیفه", "تلفن", "معاش"]), use_container_width=True)
        elif "مصارف مکتب" in rep_choice:
            cursor.execute("SELECT date, category, amount, description, user_name FROM cashbox WHERE type='Outflow'")
            rows = cursor.fetchall()
            st.dataframe(pd.DataFrame(rows, columns=["تاریخ", "دسته‌بندی", "مبلغ", "تشریحات", "کاربر"]), use_container_width=True)
        elif "درآمدها" in rep_choice:
            cursor.execute("SELECT date, category, amount, description, user_name FROM cashbox WHERE type='Inflow'")
            rows = cursor.fetchall()
            st.dataframe(pd.DataFrame(rows, columns=["تاریخ", "نوع درآمد", "مبلغ", "تشریحات", "کاربر"]), use_container_width=True)

    # ==================== ۹. مدیریت صندوق ====================
    elif menu == "💰 مدیریت صندوق":
        st.title("💰 گردش کامل صندوق و دخل مکتب")
        cursor.execute("SELECT date, type, category, amount, description, user_name FROM cashbox")
        rows = cursor.fetchall()
        if rows:
            st.dataframe(pd.DataFrame(rows, columns=["تاریخ", "نوع", "دسته‌بندی", "مبلغ", "تشریحات", "کاربر"]), use_container_width=True)

    # ==================== ۱۰. کاربران سیستم ====================
    elif menu == "👥 کاربران سیستم":
        st.title("👥 مدیریت کاربران و دسترسی‌ها")
        if st.session_state.user_role != "Admin":
            st.error("⛔ فقط مدیر کل (Admin) به این بخش دسترسی دارد.")
        else:
            with st.form("new_user"):
                st.subheader("➕ تعریف کاربر جدید")
                n_name = st.text_input("نام کامل")
                n_user = st.text_input("نام کاربری")
                n_pass = st.text_input("رمز عبور", type="password")
                n_role = st.selectbox("نقش", ["Admin", "Financial_Manager"])
                if st.form_submit_button("ایجاد کاربر"):
                    try:
                        cursor.execute("INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)", (n_user, n_pass, n_name, n_role))
                        conn.commit()
                        st.success("کاربر جدید ساخته شد.")
                    except:
                        st.error("نام کاربری تکراری است.")
            
            cursor.execute("SELECT username, full_name, role FROM users")
            st.dataframe(pd.DataFrame(cursor.fetchall(), columns=["نام کاربری", "نام کامل", "نقش"]), use_container_width=True)

    # ==================== ۱۱. تنظیمات سیستم ====================
    elif menu == "⚙️ تنظیمات سیستم":
        st.title("⚙️ تنظیمات سیستم و افزودن گزینه‌ها")
        
        with st.form("class_form"):
            st.subheader("افزودن صنف جدید")
            new_cls = st.text_input("نام صنف جدید:")
            if st.form_submit_button("افزودن صنف"):
                if new_cls:
                    try:
                        cursor.execute("INSERT INTO classes (class_name) VALUES (?)", (new_cls,))
                        conn.commit()
                        st.success("صنف جدید افزوده شد.")
                    except:
                        st.error("این صنف قبلاً ثبت شده است.")

        with st.form("exp_cat_form"):
            st.subheader("افزودن دسته‌بندی مصارف جدید")
            new_cat = st.text_input("عنوان دسته مصرف:")
            if st.form_submit_button("افزودن دسته"):
                if new_cat:
                    try:
                        cursor.execute("INSERT INTO expense_categories (category_name) VALUES (?)", (new_cat,))
                        conn.commit()
                        st.success("دسته‌بندی مصارف افزوده شد.")
                    except:
                        st.error("این دسته‌بندی وجود دارد.")

    # ==================== ۱۲. راهنما ====================
    elif menu == "📖 راهنما":
        st.title("📖 راهنما و آموزش جامع سیستم")
        st.markdown("""
        ### سیستم مدیریت مالی و اداری مکتب خصوصی کاوشگران دانش بلخ
        - تمامی محاسبات شهریه، ترانسپورت و باقی‌داری‌ها بر اساس تاریخ خورشیدی و روز ۲۹ هر ماه انجام می‌شود.
        - ارزیابی اتوماتیک روزانه برای سهمیه شاگردان بدون در نظر گرفتن روزهای جمعه فعال است.
        - امکان ثبت مرخصی یا عدم حضور (`Break`) برای کسر عادلانه فیس وجود دارد.
        """)

    conn.close()