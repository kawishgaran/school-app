import streamlit as st
import sqlite3
import shutil
import os
import re
import jdatetime
import math
import pandas as pd

# ==================== تنظیمات صفحه و استایل مشابه ورد (Ribbon Menu RTL) ====================
st.set_page_config(
    page_title="مکتب خصوصی کاوشگران دانش بلخ",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        /* راست‌چین کردن کل بدنه و عناصر صفحه */
        html, body, [class*="css"] {
            direction: rtl;
            text-align: right;
            font-family: Tahoma, Arial, sans-serif;
        }
        
        /* استایل ظاهری برای شبیه‌سازی نوار ابزار ورد */
        .word-ribbon {
            background-color: #f3f3f3;
            padding: 10px;
            border-radius: 8px;
            border: 1px solid #dcdcdc;
            margin-bottom: 20px;
            direction: rtl;
        }
    </style>
""", unsafe_allow_html=True)

DB_FILE = "school_finance.db"

# ==================== ایجاد و مقداردهی اولیه دیتابیس ====================
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

# ==================== توابع محاسباتی و کمکی ====================
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
               registration_date, initial_previous_debt, initial_books_debt, initial_uniform_debt 
        FROM students WHERE student_id = ?
    ''', (student_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
        
    fee, is_free, uses_t, t_fee, reg_date, p_debt, b_debt, u_debt = row
    if is_free == 1:
        fee = 0.0
        
    active_m = calculate_active_months(student_id, reg_date)
    calc_tuition = fee * active_m
    calc_transport = (t_fee * active_m) if uses_t == 1 else 0.0
    
    gross_debt = p_debt + calc_tuition + calc_transport + b_debt + u_debt
    
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
        "gross_debt": gross_debt,
        "total_paid": total_paid,
        "net_debt": net_debt,
        "advance_pay": advance_pay
    }

# ==================== احراز هویت و مدیریت جلسات ====================
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
    # ==================== طراحی نوار ابزار افقی (مانند ورد آفیس) در بالای صفحه ====================
    st.markdown('<div class="word-ribbon">', unsafe_allow_html=True)
    
    c_info, c_logout = st.columns([6, 1])
    c_info.markdown(f"👤 کاربر فعال: **{st.session_state.user_name}** ({st.session_state.user_role})")
    if c_logout.button("🚪 خروج"):
        st.session_state.logged_in = False
        st.session_state.user_name = ""
        st.session_state.user_role = ""
        st.rerun()

    # دکمه چک‌باکس برای نمایش اطلاعات بیشتر (سایر منوها)
    show_more = st.checkbox("⚙️ اطلاعات بیشتر / سایر امکانات سیستم (نمایش منوهای پنهان)")

    # لیست منوها به شکلی که جستجو و پرونده و گزارشات پیشرفته در اول باشند
    if show_more:
        menu_options = [
            "🔍 جستجو و پرونده شاگردان", 
            "📈 گزارش‌گیری پیشرفته",
            "📊 داشبورد", 
            "➕ ثبت‌نام جدید", 
            "📝 حاضری شاگردان", 
            "⭐ ارزیابی شاگردان", 
            "👨‍🏫 پرسنل و استادان", 
            "💸 ثبت مصارف مکتب", 
            "💰 مدیریت صندوق", 
            "👥 مدیریت کاربران سیستم",
            "⚙️ تنظیمات سیستم",
            "📖 راهنما و کلیدهای میانبر"
        ]
    else:
        menu_options = [
            "🔍 جستجو و پرونده شاگردان", 
            "📈 گزارش‌گیری پیشرفته"
        ]

    menu = st.selectbox(
        "📌 منوی اصلی سیستم (نوار ابزار)",
        menu_options
    )
    st.markdown('</div>', unsafe_allow_html=True)

    conn = sqlite3.connect(DB_FILE)

    # ==================== ۱. جستجو و پرونده شاگردان (اولویت اول) ====================
    if menu == "🔍 جستجو و پرونده شاگردان":
        st.title("🔍 جستجو و پرونده مالی و اداری جامع دانش‌آموز")
        
        cursor = conn.cursor()
        cursor.execute("SELECT student_id, student_no, full_name, father_name FROM students WHERE status='فعال'")
        all_students = cursor.fetchall()
        
        if all_students:
            student_options = {}
            for s_id, s_no, s_name, s_father in all_students:
                display_label = f"{s_name} - نام پدر: {s_father} (آی‌دی: {s_no})"
                student_options[display_label] = s_id
                
            st.markdown("##### 📌 جستجو و انتخاب شاگرد از طریق پیشنهاد نام و نام پدر")
            selected_label = st.selectbox("شاگرد مورد نظر را جستجو یا انتخاب کنید:", options=list(student_options.keys()))
            
            if st.button("📂 نمایش پرونده شاگرد"):
                if selected_label:
                    st.session_state.selected_student_id = student_options[selected_label]
            
            target_id = st.session_state.get("selected_student_id", None)
            
            if target_id:
                cursor.execute('''
                    SELECT student_id, student_no, full_name, father_name, grandfather_name, class_name, standard_fee, is_free, 
                           uses_transport, transport_fee, father_phone, registration_date
                    FROM students WHERE student_id = ?
                ''', (target_id,))
                st_row = cursor.fetchone()
                
                if st_row:
                    s_id, no, name, father, gfather, cls, fee, is_free, uses_t, t_fee, fphone, reg_date = st_row
                    summary = get_student_financial_summary(s_id)
                    
                    if summary:
                        st.markdown("---")
                        st.subheader(f"📁 پرونده دانش‌آموز: {name} {'(معاف/رایگان)' if is_free == 1 else ''}")
                        
                        st.markdown(f"""
                        * **صنف:** {cls} | **نمبر آی‌دی:** {no} | **مجموع باقی‌داری کل:** {summary['net_debt']:,.2f} افغانی
                        * **نام پدر (پدرکلان):** {father} ({gfather}) | **تلفن پدر:** {fphone} | **تاریخ ثبت‌نام:** {reg_date}
                        * **فیس ماهانه:** {summary['monthly_fee']:,.2f} افغانی | **ماه‌های فعال:** {summary['active_months']} ماه
                        * **ریز بدهی‌ها:** [قبلی: {summary['previous_debt']:,.2f}] | [شهریه: {summary['calc_tuition']:,.2f}] | [ترانسپورت: {summary['calc_transport']:,.2f}] | [کتاب: {summary['books_debt']:,.2f}] | [لباس: {summary['uniform_debt']:,.2f}]
                        * **مجموع کل پرداختی‌ها:** {summary['total_paid']:,.2f} افغانی | **پیش‌پرداخت/بستانکاری:** {summary['advance_pay']:,.2f} افغانی
                        """)

                        tab_pay, tab_break, tab_att, tab_eval, tab_edit = st.tabs(["💳 دریافت فیس", "📌 عدم حضور (Break)", "📊 حضور و غیاب", "⭐ سوابق ارزیابی", "✏️ ویرایش شاگرد"])

                        with tab_pay:
                            with st.form(f"pay_form_{s_id}"):
                                fee_type = st.selectbox("نوع فیس / بدهی", ["شهریه ماه جاری", "باقی‌داری قبلی", "ترانسپورت", "کتاب", "لباس", "پیش‌پرداخت / بستانکاری"], key=f"ft_{s_id}")
                                p_amt = st.number_input("مبلغ پرداختی (افغانی)", min_value=0.0, key=f"pa_{s_id}")
                                p_date = st.text_input("تاریخ (اتومات/دستی)", value=jdatetime.date.today().strftime("%Y/%m/%d"), key=f"pd_{s_id}")
                                p_desc = st.text_input("توضیحات اختیاری", key=f"pdes_{s_id}")
                                if st.form_submit_button("ثبت پرداخت و دریافت وجه"):
                                    if p_amt > 0:
                                        cursor.execute("INSERT INTO student_payments (student_id, date, trans_type, fee_type, amount, description, user_name) VALUES (?, ?, 'دریافت وجه', ?, ?, ?, ?)",
                                                       (s_id, p_date, fee_type, p_amt, p_desc, st.session_state.user_name))
                                        cursor.execute("INSERT INTO cashbox (date, type, category, amount, description, user_name) VALUES (?, 'Inflow', ?, ?, ?, ?)",
                                                       (p_date, f"دریافت {fee_type}", p_amt, f"پرداخت شاگرد ID:{s_id}\n{p_desc}", st.session_state.user_name))
                                        conn.commit()
                                        st.success("تراکنش ثبت گردید.")
                                        st.rerun()

                            st.markdown("##### 💳 سوابق پرداخت‌های این شاگرد")
                            cursor.execute("SELECT payment_id, date, trans_type, fee_type, amount, description, user_name FROM student_payments WHERE student_id = ?", (s_id,))
                            p_rows = cursor.fetchall()
                            if p_rows:
                                df_p = pd.DataFrame(p_rows, columns=["شناسه", "تاریخ", "نوع تراکنش", "نوع فیس", "مبلغ", "توضیحات", "کاربر"])
                                st.dataframe(df_p, use_container_width=True)
                                
                                del_p_id = st.number_input("شناسه تراکنش جهت حذف", min_value=0, step=1, key=f"delp_{s_id}")
                                if st.button("❌ حذف پرداخت شاگرد", key=f"btndp_{s_id}"):
                                    cursor.execute("SELECT amount FROM student_payments WHERE payment_id = ?", (del_p_id,))
                                    r_p = cursor.fetchone()
                                    if r_p:
                                        cursor.execute("INSERT INTO cashbox (date, type, category, amount, description, user_name) VALUES (date('now'), 'Outflow', 'برگشت پرداخت شاگرد', ?, 'حذف پرداخت شاگرد', ?)",
                                                       (r_p[0], st.session_state.user_name))
                                        cursor.execute("DELETE FROM student_payments WHERE payment_id = ?", (del_p_id,))
                                        conn.commit()
                                        st.success("تراکنش حذف شد و حساب‌ها به‌روزرسانی شدند.")
                                        st.rerun()

                        with tab_break:
                            with st.form(f"break_form_{s_id}"):
                                b_start = st.text_input("از تاریخ/ماه (مثلاً 1405/02/01)", key=f"bs_{s_id}")
                                b_end = st.text_input("تا تاریخ/ماه (مثلاً 1405/03/01)", key=f"be_{s_id}")
                                b_reason = st.text_input("دلیل مرخصی", key=f"br_{s_id}")
                                if st.form_submit_button("➕ ثبت مرخصی / Break"):
                                    if b_start and b_end:
                                        cursor.execute("INSERT INTO student_breaks (student_id, start_month, end_month, reason) VALUES (?, ?, ?, ?)",
                                                       (s_id, b_start, b_end, b_reason))
                                        conn.commit()
                                        st.success("دوره عدم حضور ثبت شد.")
                                        st.rerun()

                            cursor.execute("SELECT break_id, start_month, end_month, reason FROM student_breaks WHERE student_id = ?", (s_id,))
                            b_rows = cursor.fetchall()
                            if b_rows:
                                df_b = pd.DataFrame(b_rows, columns=["شناسه", "از تاریخ", "تا تاریخ", "دلیل"])
                                st.dataframe(df_b, use_container_width=True)
                                
                                del_b_id = st.number_input("شناسه مرخصی جهت حذف", min_value=0, step=1, key=f"delb_{s_id}")
                                if st.button("❌ حذف Break", key=f"btndb_{s_id}"):
                                    cursor.execute("DELETE FROM student_breaks WHERE break_id = ?", (del_b_id,))
                                    conn.commit()
                                    st.success("مرخصی حذف گردید.")
                                    st.rerun()

                        with tab_att:
                            cursor.execute("SELECT status, COUNT(*) FROM attendance WHERE student_id = ? GROUP BY status", (s_id,))
                            att_stats = {r[0]: r[1] for r in cursor.fetchall()}
                            p_c = sum(v for k, v in att_stats.items() if "حاضر" in k and "غیر" not in k)
                            a_c = sum(v for k, v in att_stats.items() if "غیرحاضر" in k)
                            l_c = sum(v for k, v in att_stats.items() if "رخصتی" in k)
                            
                            st.write(f"✅ **حاضر:** {p_c} روز | ❌ **غیرحاضر:** {a_c} روز | 📌 **رخصتی:** {l_c} روز")
                            cursor.execute("SELECT attendance_id, date, status FROM attendance WHERE student_id = ? ORDER BY attendance_id DESC", (s_id,))
                            df_att = pd.DataFrame(cursor.fetchall(), columns=["شناسه", "تاریخ", "وضعیت"])
                            st.dataframe(df_att, use_container_width=True)

                        with tab_eval:
                            cursor.execute("SELECT evaluation_id, date, notebook_check, diary_check, dictation, learning_level, homework, other_cases, total_score FROM evaluations WHERE student_id = ? ORDER BY evaluation_id DESC", (s_id,))
                            df_ev = pd.DataFrame(cursor.fetchall(), columns=["شناسه", "تاریخ", "کتابچه", "دایری", "املا", "یادگیری", "خانگی", "سایر", "مجموع (از ۱۲)"])
                            st.dataframe(df_ev, use_container_width=True)

                        with tab_edit:
                            with st.form(f"edit_st_form_{s_id}"):
                                e_no = st.text_input("آی‌دی", value=str(no), key=f"eno_{s_id}")
                                e_name = st.text_input("نام کامل", value=str(name), key=f"ename_{s_id}")
                                e_father = st.text_input("نام پدر", value=str(father), key=f"efather_{s_id}")
                                e_gfather = st.text_input("نام پدرکلان", value=str(gfather), key=f"egfather_{s_id}")
                                e_fee = st.number_input("شهریه ماهانه", value=float(fee), key=f"efee_{s_id}")
                                e_free = st.checkbox("شاگرد رایگان", value=bool(is_free), key=f"efree_{s_id}")
                                e_fphone = st.text_input("تلفن پدر", value=str(fphone), key=f"efp_{s_id}")
                                e_pdebt = st.number_input("باقی‌داری قبلی", value=float(summary['previous_debt']), key=f"epd_{s_id}")
                                e_reg = st.text_input("تاریخ ثبت‌نام", value=str(reg_date), key=f"ereg_{s_id}")
                                
                                if st.form_submit_button("💾 ذخیره تغییرات مشخصات"):
                                    is_f_val = 1 if e_free else 0
                                    fee_val = 0.0 if is_f_val else e_fee
                                    cursor.execute('''
                                        UPDATE students SET student_no=?, full_name=?, father_name=?, grandfather_name=?, standard_fee=?, is_free=?, father_phone=?, initial_previous_debt=?, registration_date=?
                                        WHERE student_id=?
                                    ''', (e_no, e_name, e_father, e_gfather, fee_val, is_f_val, e_fphone, e_pdebt, e_reg, s_id))
                                    conn.commit()
                                    st.success("اطلاعات ویرایش شد.")
                                    st.rerun()

                            if st.button(f"❌ حذف کامل دانش‌آموز {name}", key=f"del_st_btn_{s_id}"):
                                cursor.execute("DELETE FROM students WHERE student_id = ?", (s_id,))
                                conn.commit()
                                st.success("دانش‌آموز حذف گردید.")
                                st.rerun()
        else:
            st.info("هیچ دانش‌آموزی در سیستم ثبت نشده است.")

    # ==================== ۲. گزارش‌گیری پیشرفته (اولویت دوم) ====================
    elif menu == "📈 گزارش‌گیری پیشرفته":
        st.title("📈 گزارش‌گیری پیشرفته و جامع مکتب")
        rep_type = st.selectbox("انتخاب نوع گزارش", [
            "گزارش لیست دانش‌آموزان (با تاریخ ثبت‌نام)", 
            "گزارش باقی‌داری شاگردان (از بیشترین به کمترین)",
            "گزارش لیست پرسنل و استادان",
            "گزارش مصارف مکتب",
            "گزارش پرداختی‌ها و درآمدها"
        ])
        
        cursor = conn.cursor()
        
        if "دانش‌آموزان (با تاریخ ثبت‌نام)" in rep_type:
            cursor.execute("SELECT student_id, student_no, full_name, father_name, class_name, registration_date, is_free FROM students")
            raw_r = cursor.fetchall()
            rows = []
            for r in raw_r:
                s_id, no, name, father, cls, reg_date, is_free = r
                summary = get_student_financial_summary(s_id)
                net_d = summary["net_debt"] if summary else 0.0
                rows.append([no, name + (" (رایگان)" if is_free == 1 else ""), father, cls, reg_date, f"{net_d:,.2f}"])
            df = pd.DataFrame(rows, columns=["نمبر آی‌دی", "نام کامل", "نام پدر", "صنف", "تاریخ ثبت‌نام", "مجموع باقی‌داری"])
            st.dataframe(df, use_container_width=True)

        elif "باقی‌داری شاگردان" in rep_type:
            cursor.execute("SELECT student_id, student_no, full_name, father_name, father_phone FROM students")
            raw_r = cursor.fetchall()
            rows = []
            for r in raw_r:
                s_id, no, name, father, fphone = r
                summary = get_student_financial_summary(s_id)
                net_d = summary["net_debt"] if summary else 0.0
                rows.append([no, name, father, fphone, net_d])
            
            rows.sort(key=lambda x: x[4], reverse=True)
            rows = [[r[0], r[1], r[2], r[3], f"{r[4]:,.2f}"] for r in rows]
            df = pd.DataFrame(rows, columns=["آی‌دی", "نام کامل", "نام پدر", "تلفن پدر", "مقدار کل باقی‌داری"])
            st.dataframe(df, use_container_width=True)

        elif "پرسنل و استادان" in rep_type:
            cursor.execute("SELECT staff_no, full_name, role_type, phone, salary, registration_date FROM staff")
            df = pd.DataFrame(cursor.fetchall(), columns=["شناسه پرسنل", "نام کامل", "وظیفه", "تلفن", "معاش", "تاریخ ثبت"])
            st.dataframe(df, use_container_width=True)

        elif "مصارف مکتب" in rep_type:
            cursor.execute("SELECT date, category, amount, description, user_name FROM cashbox WHERE type='Outflow' AND category != 'پرداخت پرسنل'")
            df = pd.DataFrame(cursor.fetchall(), columns=["تاریخ", "دسته‌بندی", "مبلغ", "تشریحات", "کاربر"])
            st.dataframe(df, use_container_width=True)

        elif "پرداختی‌ها و درآمدها" in rep_type:
            cursor.execute("SELECT date, category, amount, description, user_name FROM cashbox WHERE type='Inflow'")
            df = pd.DataFrame(cursor.fetchall(), columns=["تاریخ", "نوع درآمد / فیس", "مبلغ", "توضیحات", "کاربر"])
            st.dataframe(df, use_container_width=True)

    # ==================== سایر بخش‌ها (فقط در صورت تیک زدن اطلاعات بیشتر نمایش داده می‌شوند) ====================
    elif menu == "📊 داشبورد":
        st.title("📊 داشبورد مدیریتی مکتب خصوصی کاوشگران دانش بلخ")
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM students WHERE status='فعال'")
        s_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(amount) FROM cashbox WHERE type='Inflow'")
        inflow = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(amount) FROM cashbox WHERE type='Outflow'")
        outflow = cursor.fetchone()[0] or 0
        total_cash = inflow - outflow
        
        cursor.execute("SELECT student_id FROM students WHERE status='فعال'")
        all_ids = cursor.fetchall()
        total_debts = 0.0
        for s_tuple in all_ids:
            summary = get_student_financial_summary(s_tuple[0])
            if summary:
                total_debts += summary["net_debt"]

        col1, col2, col3 = st.columns(3)
        col1.metric("دانش‌آموزان فعال", f"{s_count} نفر")
        col2.metric("موجودی فعلی صندوق", f"{total_cash:,.2f} افغانی")
        col3.metric("مجموع باقی‌داری‌ها", f"{total_debts:,.2f} افغانی")

        st.markdown("---")
        st.subheader("💵 تنظیم تراز دستی صندوق")
        new_cash_input = st.number_input("مبلغ جدید تراز صندوق (افغانی)", value=float(total_cash))
        if st.button("ثبت و تنظیم تراز"):
            diff = new_cash_input - total_cash
            if diff != 0:
                t_type = "Inflow" if diff > 0 else "Outflow"
                cursor.execute("INSERT INTO cashbox (date, type, category, amount, description, user_name) VALUES (date('now'), ?, 'تنظیم تراز دستی', ?, 'اصلاح دستی تراز حساب صندوق توسط مدیر', ?)",
                               (t_type, abs(diff), st.session_state.user_name))
                conn.commit()
                st.success("تراز صندوق با موفقیت اصلاح شد.")
                st.rerun()

    elif menu == "➕ ثبت‌نام جدید":
        st.title("🎓 فرم ثبت نام دانش‌آموز جدید")
        cursor = conn.cursor()
        cursor.execute("SELECT class_name FROM classes")
        classes = [r[0] for r in cursor.fetchall()]

        with st.form("reg_form"):
            st.markdown("##### 👤 معلومات شخصی شاگرد")
            c1, c2 = st.columns(2)
            with c1:
                reg_no = st.text_input("نمبر آی‌دی *")
                reg_name = st.text_input("نام کامل شاگرد *")
                reg_father = st.text_input("نام پدر")
                reg_gfather = st.text_input("نام پدرکلان")
                reg_class = st.selectbox("صنف انتخابی", classes)
            with c2:
                reg_fee = st.number_input("شهریه ماهانه (افغانی)", min_value=0.0, value=1000.0)
                reg_chk_free = st.checkbox("شاگرد رایگان (معاف از شهریه)")
                reg_fphone = st.text_input("شماره تماس پدر")
                reg_mphone = st.text_input("شماره تماس مادر")
                reg_prev_debt = st.number_input("باقی‌داری قبلی", value=0.0)
                reg_date = st.text_input("تاریخ ثبت‌نام *", value=jdatetime.date.today().strftime("%Y/%m/%d"))

            st.markdown("##### 🚌 خدمات ترانسپورت")
            reg_chk_trans = st.checkbox("استفاده از سیستم ترانسپورت مکتب")
            c_t1, c_t2 = st.columns(2)
            reg_route = c_t1.text_input("مسیر ترانسپورت")
            reg_tfee = c_t2.number_input("کرایه ماهانه ترانسپورت", value=0.0)

            st.markdown("##### 📚 کتاب و لباس (دریشی)")
            c_b1, c_b2 = st.columns(2)
            reg_chk_books = c_b1.checkbox("تحویل کتاب‌های مکتب")
            reg_bfee = c_b1.number_input("قیمت کتاب", value=0.0)
            reg_bstatus = c_b1.selectbox("وضعیت پرداخت کتاب", ["پرداخت شده", "باقی‌دار"])

            reg_chk_uniform = c_b2.checkbox("تحویل لباس مکتب (دریشی)")
            reg_ufee = c_b2.number_input("قیمت لباس", value=0.0)
            reg_ustatus = c_b2.selectbox("وضعیت پرداخت لباس", ["پرداخت شده", "باقی‌دار"])

            submitted = st.form_submit_button("📝 ثبت نهایی دانش‌آموز در سیستم")
            if submitted:
                if not reg_no or not reg_name or not reg_date:
                    st.warning("لطفاً اطلاعات ضروری شامل آی‌دی، نام و تاریخ ثبت‌نام را پر کنید.")
                else:
                    cursor.execute("SELECT student_no FROM students WHERE student_no = ?", (reg_no,))
                    if cursor.fetchone():
                        st.error(f"شماره آی‌دی «{reg_no}» قبلاً ثبت شده است!")
                    else:
                        is_free = 1 if reg_chk_free else 0
                        final_fee = 0.0 if is_free else reg_fee
                        uses_t = 1 if reg_chk_trans else 0
                        takes_b = 1 if reg_chk_books else 0
                        takes_u = 1 if reg_chk_uniform else 0
                        b_debt = reg_bfee if (takes_b and reg_bstatus == "باقی‌دار") else 0.0
                        u_debt = reg_ufee if (takes_u and reg_ustatus == "باقی‌دار") else 0.0

                        try:
                            cursor.execute('''
                                INSERT INTO students (
                                    student_no, full_name, father_name, grandfather_name, class_name, standard_fee, is_free,
                                    father_phone, mother_phone, uses_transport, transport_route, transport_fee,
                                    takes_books, books_fee, books_payment_status, takes_uniform, uniform_fee, uniform_payment_status,
                                    initial_previous_debt, initial_books_debt, initial_uniform_debt, status, registration_date
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'فعال', ?)
                            ''', (reg_no, reg_name, reg_father, reg_gfather, reg_class, final_fee, is_free,
                                  reg_fphone, reg_mphone, uses_t, reg_route, reg_tfee,
                                  takes_b, reg_bfee, reg_bstatus, takes_u, reg_ufee, reg_ustatus,
                                  reg_prev_debt, b_debt, u_debt, reg_date))
                            conn.commit()
                            st.success("دانش‌آموز با موفقیت ثبت شد!")
                        except Exception as e:
                            st.error(f"خطا در ثبت اطلاعات: {e}")

    elif menu == "📝 حاضری شاگردان":
        st.title("📋 ثبت حضور و غیاب روزانه شاگردان")
        cursor = conn.cursor()
        cursor.execute("SELECT class_name FROM classes")
        classes = [r[0] for r in cursor.fetchall()]

        col1, col2 = st.columns(2)
        sel_class = col1.selectbox("انتخاب صنف", classes)
        att_date = col2.text_input("تاریخ حاضری", value=jdatetime.date.today().strftime("%Y/%m/%d"))

        cursor.execute("SELECT student_id, student_no, full_name, father_name FROM students WHERE class_name = ? AND status='فعال'", (sel_class,))
        students = cursor.fetchall()

        if students:
            cursor.execute("SELECT student_id, status FROM attendance WHERE date = ?", (att_date,))
            saved = {r[0]: r[1] for r in cursor.fetchall()}

            with st.form("att_form"):
                attendance_data = []
                for st_row in students:
                    s_id, no, name, father = st_row
                    init_idx = 0
                    if s_id in saved:
                        if "غیرحاضر" in saved[s_id]: init_idx = 1
                        elif "رخصتی" in saved[s_id]: init_idx = 2

                    status = st.selectbox(f"👤 {name} (پدر: {father} | آی‌دی: {no})", ["حاضر ✅", "غیرحاضر ❌", "رخصتی 📌"], index=init_idx, key=f"att_{s_id}")
                    attendance_data.append((s_id, status))

                if st.form_submit_button("💾 ثبت نهایی حاضری امروز"):
                    for s_id, status in attendance_data:
                        cursor.execute("SELECT attendance_id FROM attendance WHERE student_id = ? AND date = ?", (s_id, att_date))
                        ex = cursor.fetchone()
                        if ex:
                            cursor.execute("UPDATE attendance SET status = ? WHERE attendance_id = ?", (status, ex[0]))
                        else:
                            cursor.execute("INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)", (s_id, att_date, status))
                    conn.commit()
                    st.success("حاضری امروز با موفقیت ثبت شد.")
        else:
            st.info("هیچ شاگرد فعالی در این صنف یافت نشد.")

    elif menu == "⭐ ارزیابی شاگردان":
        st.title("⭐ سیستم ارزیابی اتوماتیک ماهانه (بدون احتساب جمعه‌ها)")
        eval_date = st.text_input("تاریخ ارزیابی امروز", value=jdatetime.date.today().strftime("%Y/%m/%d"))
        
        y, m, d = parse_shamsi_date(eval_date)
        is_friday = False
        if y and m and d:
            try:
                if jdatetime.date(y, m, d).weekday() == 6:
                    is_friday = True
            except:
                pass

        if is_friday:
            st.warning("📌 امروز جمعه است! طبق دستورالعمل، روزهای جمعه ارزیابی انجام نمی‌شود.")
        else:
            cursor = conn.cursor()
            cursor.execute("SELECT student_id, student_no, full_name, father_name, class_name FROM students WHERE status='فعال' ORDER BY student_id ASC")
            all_st = cursor.fetchall()

            if all_st:
                working_days = 26
                daily_quota = math.ceil(len(all_st) / float(working_days))

                cursor.execute("SELECT DISTINCT student_id FROM evaluations WHERE substr(date, 1, 7) = ?", (f"{y:04d}/{m:02d}",))
                already_eval = {r[0] for r in cursor.fetchall()}

                rem_st = [s for s in all_st if s[0] not in already_eval]
                target_batch = (rem_st if rem_st else all_st)[:daily_quota]

                st.info(f"📊 کل شاگردان: {len(all_st)} | سهمیه روزانه: {daily_quota} نفر | نوبت امروز: {len(target_batch)} نفر")

                with st.form("eval_form"):
                    eval_records = []
                    for st_row in target_batch:
                        s_id, no, name, father, c_name = st_row
                        st.markdown(f"**🎓 {name}** (پدر: {father} | صنف: {c_name} | آی‌دی: {no})")
                        col1, col2, col3, col4, col5, col6 = st.columns(6)
                        n_chk = col1.selectbox("چک کتابچه", [0, 1, 2], index=2, key=f"n_{s_id}")
                        d_chk = col2.selectbox("چک دایری", [0, 1, 2], index=2, key=f"d_{s_id}")
                        dict_s = col3.selectbox("املا", [0, 1, 2], index=2, key=f"dict_{s_id}")
                        learn = col4.selectbox("سطح یادگیری", [0, 1, 2], index=2, key=f"l_{s_id}")
                        hw = col5.selectbox("وظیفه خانگی", [0, 1, 2], index=2, key=f"hw_{s_id}")
                        oth = col6.selectbox("سایر موارد", [0, 1, 2], index=2, key=f"oth_{s_id}")
                        eval_records.append((s_id, n_chk, d_chk, dict_s, learn, hw, oth))

                    if st.form_submit_button("💾 ثبت نهایی ارزیابی‌های امروز"):
                        for rec in eval_records:
                            s_id, n, d_c, di, l, h, o = rec
                            total = n + d_c + di + l + h + o
                            cursor.execute('''
                                INSERT INTO evaluations (student_id, date, notebook_check, diary_check, dictation, learning_level, homework, other_cases, total_score)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (s_id, eval_date, n, d_c, di, l, h, o, total))
                        conn.commit()
                        st.success("ارزیابی‌های امروز با موفقیت در پرونده شاگردان ذخیره گردید.")
                        st.rerun()

    elif menu == "👨‍🏫 پرسنل و استادان":
        st.title("👨‍🏫 مدیریت و پرداخت حقوق پرسنل و استادان")
        
        with st.expander("➕ ثبت کارمند / استاد جدید"):
            with st.form("staff_add_form"):
                st_no = st.text_input("آی‌دی پرسنل *")
                st_name = st.text_input("نام کامل *")
                st_role = st.selectbox("وظیفه", ["استاد", "درایور", "گارد", "خاله مکتب", "مدیر مکتب", "سایر"])
                st_phone = st.text_input("تلفن")
                st_salary = st.number_input("معاش ماهانه (افغانی)", value=0.0)
                st_date = st.text_input("تاریخ ثبت *", value=jdatetime.date.today().strftime("%Y/%m/%d"))
                
                if st.form_submit_button("ثبت پرسنل"):
                    if st_no and st_name and st_date:
                        cursor = conn.cursor()
                        try:
                            cursor.execute("INSERT INTO staff (staff_no, full_name, role_type, phone, salary, registration_date) VALUES (?, ?, ?, ?, ?, ?)",
                                           (st_no, st_name, st_role, st_phone, st_salary, st_date))
                            conn.commit()
                            st.success("پرسنل ثبت شد.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"خطا: {e}")

        cursor = conn.cursor()
        search_st = st.text_input("🔍 جستجوی پرسنل بر اساس نام یا آی‌دی:")
        if search_st:
            cursor.execute("SELECT staff_id, staff_no, full_name, role_type, phone, salary, registration_date FROM staff WHERE full_name LIKE ? OR staff_no LIKE ?", (f"%{search_st}%", f"%{search_st}%"))
        else:
            cursor.execute("SELECT staff_id, staff_no, full_name, role_type, phone, salary, registration_date FROM staff")
        staff_rows = cursor.fetchall()

        for st_r in staff_rows:
            st_id, st_no, st_name, st_role, st_phone, st_salary, st_reg = st_r
            m_worked = calculate_active_months(st_id, st_reg)
            tot_sal_due = st_salary * m_worked
            
            cursor.execute("SELECT SUM(amount) FROM staff_payments WHERE staff_id = ?", (st_id,))
            paid_tot = cursor.fetchone()[0] or 0.0
            net_due = max(0, tot_sal_due - paid_tot)

            with st.expander(f"👤 {st_name} ({st_role}) | آی‌دی: {st_no} | باقی‌داری خالص حقوق: {net_due:,.2f} افغانی"):
                st.write(f"**تلفن:** {st_phone} | **تاریخ ثبت:** {st_reg} | **معاش ماهانه:** {st_salary:,.2f} | **کل معوقه ({m_worked} ماه):** {tot_sal_due:,.2f}")
                
                t_p1, t_p2 = st.tabs(["💵 پرداخت حقوق", "📋 سوابق پرداختی‌ها"])
                with t_p1:
                    with st.form(f"sp_form_{st_id}"):
                        p_amt = st.number_input("مبلغ پرداختی (افغانی)", min_value=0.0, key=f"samt_{st_id}")
                        p_date = st.text_input("تاریخ پرداخت", value=jdatetime.date.today().strftime("%Y/%m/%d"), key=f"sdate_{st_id}")
                        p_desc = st.text_input("توضیحات", key=f"sdesc_{st_id}")
                        if st.form_submit_button("ثبت پرداخت"):
                            if p_amt > 0:
                                cursor.execute("INSERT INTO staff_payments (staff_id, date, trans_type, amount, description, user_name) VALUES (?, ?, 'پرداخت حقوق', ?, ?, ?)",
                                               (st_id, p_date, p_amt, p_desc, st.session_state.user_name))
                                cursor.execute("INSERT INTO cashbox (date, type, category, amount, description, user_name) VALUES (?, 'Outflow', 'پرداخت پرسنل', ?, ?, ?)",
                                               (p_date, p_amt, f"حقوق پرسنل ID:{st_id}\n{p_desc}", st.session_state.user_name))
                                conn.commit()
                                st.success("پرداخت ثبت شد.")
                                st.rerun()

                with t_p2:
                    cursor.execute("SELECT payment_id, date, trans_type, amount, description, user_name FROM staff_payments WHERE staff_id = ?", (st_id,))
                    sp_rows = cursor.fetchall()
                    if sp_rows:
                        df_sp = pd.DataFrame(sp_rows, columns=["شناسه", "تاریخ", "نوع", "مبلغ", "توضیحات", "کاربر"])
                        st.dataframe(df_sp, use_container_width=True)
                        
                        del_sp_id = st.number_input("شناسه پرداخت جهت حذف", min_value=0, step=1, key=f"del_sp_{st_id}")
                        if st.button("❌ حذف پرداخت حقوق", key=f"btn_del_sp_{st_id}"):
                            cursor.execute("SELECT amount FROM staff_payments WHERE payment_id = ?", (del_sp_id,))
                            r_amt = cursor.fetchone()
                            if r_amt:
                                cursor.execute("INSERT INTO cashbox (date, type, category, amount, description, user_name) VALUES (date('now'), 'Inflow', 'برگشت حقوق پرسنل', ?, 'حذف پرداخت حقوق', ?)",
                                               (r_amt[0], st.session_state.user_name))
                                cursor.execute("DELETE FROM staff_payments WHERE payment_id = ?", (del_sp_id,))
                                conn.commit()
                                st.success("پرداخت حذف و مبلغ به صندوق بازگشت.")
                                st.rerun()

    elif menu == "💸 ثبت مصارف مکتب":
        st.title("💸 ثبت مصارف و هزینه‌های متفرقه مکتب")
        cursor = conn.cursor()
        cursor.execute("SELECT category_name FROM expense_categories")
        cats = [r[0] for r in cursor.fetchall()]

        with st.form("exp_form"):
            ex_date = st.text_input("تاریخ مصرف", value=jdatetime.date.today().strftime("%Y/%m/%d"))
            ex_cat = st.selectbox("دسته‌بندی مصرف", cats)
            ex_amount = st.number_input("مبلغ (افغانی)", min_value=0.0)
            ex_desc = st.text_input("تشریحات کامل مصرف")
            
            if st.form_submit_button("💸 ثبت مصرف و کسر از صندوق"):
                if ex_amount > 0 and ex_desc:
                    cursor.execute("INSERT INTO cashbox (date, type, category, amount, description, user_name) VALUES (?, 'Outflow', ?, ?, ?, ?)",
                                   (ex_date, ex_cat, ex_amount, ex_desc, st.session_state.user_name))
                    conn.commit()
                    st.success("مصرف ثبت و از صندوق کسر گردید.")
                else:
                    st.warning("مبلغ و توضیحات را وارد کنید.")

        st.markdown("### 📋 لیست مصارف ثبت‌شده")
        cursor.execute("SELECT transaction_id, date, category, amount, description, user_name FROM cashbox WHERE type='Outflow' AND category != 'پرداخت پرسنل'")
        exp_rows = cursor.fetchall()
        if exp_rows:
            df_exp = pd.DataFrame(exp_rows, columns=["شناسه تراکنش", "تاریخ", "دسته‌بندی", "مبلغ", "تشریحات", "کاربر"])
            st.dataframe(df_exp, use_container_width=True)
            
            del_exp_id = st.number_input("شناسه مصرف جهت حذف", min_value=0, step=1)
            if st.button("❌ حذف مصرف و بازگشت مبلغ به صندوق"):
                cursor.execute("SELECT amount FROM cashbox WHERE transaction_id = ?", (del_exp_id,))
                r_exp = cursor.fetchone()
                if r_exp:
                    cursor.execute("INSERT INTO cashbox (date, type, category, amount, description, user_name) VALUES (date('now'), 'Inflow', 'برگشت مصرف', ?, 'حذف و برگشت مبلغ مصرف', ?)",
                                   (r_exp[0], st.session_state.user_name))
                    cursor.execute("DELETE FROM cashbox WHERE transaction_id = ?", (del_exp_id,))
                    conn.commit()
                    st.success("مصرف حذف و مبلغ به صندوق بازگشت.")
                    st.rerun()

    elif menu == "💰 مدیریت صندوق":
        st.title("💰 گردش کامل صندوق و دخل مکتب")
        cursor = conn.cursor()
        cursor.execute("SELECT date, type, category, amount, description, user_name FROM cashbox")
        cash_rows = cursor.fetchall()
        if cash_rows:
            df_cash = pd.DataFrame(cash_rows, columns=["تاریخ", "نوع تراکنش", "دسته‌بندی", "مبلغ (افغانی)", "توضیحات", "کاربر"])
            st.dataframe(df_cash, use_container_width=True)

    elif menu == "👥 مدیریت کاربران سیستم":
        st.title("👥 مدیریت حساب‌های کاربری سیستم")
        if st.session_state.user_role != "Admin":
            st.error("⛔ شما دسترسی لازم برای مدیریت کاربران را ندارید.")
        else:
            with st.form("add_user_form"):
                st.markdown("##### ➕ تعریف کاربر جدید")
                nu_username = st.text_input("نام کاربری (Username) *")
                nu_password = st.text_input("رمز عبور (Password) *", type="password")
                nu_fullname = st.text_input("نام و نام خانوادگی *")
                nu_role = st.selectbox("نقش کاربر", ["Financial_Manager", "Admin"])
                
                if st.form_submit_button("ایجاد کاربر"):
                    if nu_username and nu_password and nu_fullname:
                        cursor = conn.cursor()
                        try:
                            cursor.execute("INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
                                           (nu_username, nu_password, nu_fullname, nu_role))
                            conn.commit()
                            st.success(f"کاربر {nu_username} با موفقیت تعریف گردید.")
                            st.rerun()
                        except:
                            st.error("این نام کاربری قبلاً وجود دارد.")

            st.markdown("##### 📋 لیست کاربران فعال")
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, username, full_name, role FROM users")
            users_df = pd.DataFrame(cursor.fetchall(), columns=["شناسه", "نام کاربری", "نام کامل", "نقش"])
            st.dataframe(users_df, use_container_width=True)

    elif menu == "⚙️ تنظیمات سیستم":
        st.title("⚙️ تنظیمات سیستم و مدیریت گزینه‌ها")
        cursor = conn.cursor()

        st.markdown("##### 🔑 تغییر رمز عبور حساب جاری")
        with st.form("pass_form"):
            new_pass = st.text_input("رمز عبور جدید", type="password")
            if st.form_submit_button("بروزرسانی رمز"):
                if new_pass:
                    cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_pass, st.session_state.user_name))
                    conn.commit()
                    st.success("رمز عبور تغییر یافت.")

        st.markdown("##### ➕ افزودن صنف جدید")
        with st.form("class_form"):
            new_cls = st.text_input("نام صنف جدید")
            if st.form_submit_button("افزودن صنف"):
                if new_cls:
                    try:
                        cursor.execute("INSERT INTO classes (class_name) VALUES (?)", (new_cls,))
                        conn.commit()
                        st.success("صنف جدید اضافه شد.")
                        st.rerun()
                    except:
                        st.error("این صنف قبلاً ثبت شده است.")

        st.markdown("##### ➕ افزودن دسته‌بندی مصرف جدید")
        with st.form("exp_cat_form"):
            new_cat = st.text_input("عنوان دسته‌بندی مصرف جدید")
            if st.form_submit_button("افزودن دسته‌بندی"):
                if new_cat:
                    try:
                        cursor.execute("INSERT INTO expense_categories (category_name) VALUES (?)", (new_cat,))
                        conn.commit()
                        st.success("دسته‌بندی جدید اضافه شد.")
                        st.rerun()
                    except:
                        st.error("این دسته‌بندی قبلاً ثبت شده است.")

    elif menu == "📖 راهنما و کلیدهای میانبر":
        st.title("📖 راهنمای جامع سیستم مدیریت مالی مکتب")
        st.markdown("""
        ### مکتب خصوصی کاوشگران دانش بلخ
        این سیستم به عنوان نسخه کامل وب جهت دسترسی آنلاین و همزمان چند کاربر طراحی شده است.

        #### 📋 راهنمای بخش‌ها:
        1. **جستجو و پرونده شاگردان:** جستجوی آسان نام شاگرد همراه با نام پدر، دکمه مستقیم نمایش پرونده، دریافت فیس، مرخصی (Break) و حضور و غیاب.
        2. **گزارش‌گیری پیشرفته:** تهیه گزارشات کامل و دسته‌بندی‌شده از شاگردان، باقی‌داری‌ها و پرسنل.
        3. **داشبورد و سایر بخش‌ها:** قابل دسترسی با فعال کردن تیک «اطلاعات بیشتر» در بالای صفحه.
        """)

    conn.close()