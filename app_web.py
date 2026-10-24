import streamlit as st
import sqlite3
import jdatetime
import math
import pandas as pd

# ==================== تنظیمات صفحه ====================
st.set_page_config(
    page_title="مکتب خصوصی کاوشگران دانش بلخ",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="auto"
)

DB_FILE = "school_finance.db"

# ==================== استایل‌دهی حرفه‌ای و سازگار با موبایل ====================
st.markdown("""
<style>
    @import url('https://v1.fontapi.ir/css/Vazir');
    
    html, body, [class*="css"] {
        font-family: 'Vazir', sans-serif !important;
        direction: rtl;
        text-align: right;
    }
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }

    .main-header {
        background: linear-gradient(135deg, #0f172a, #1e293b);
        color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    .main-header h2 {
        color: #ffffff !important;
        font-size: 20px !important;
        margin-bottom: 5px;
    }

    .main-header p {
        font-size: 13px !important;
        color: #cbd5e1;
    }

    .search-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
        margin-bottom: 15px;
    }

    .info-card {
        background-color: #f8fafc;
        border-right: 4px solid #12b8b2;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 15px;
        font-size: 14px;
        line-height: 1.6;
    }

    .stButton>button {
        background-color: #12b8b2 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        width: 100%;
        font-weight: bold;
        padding: 10px;
    }

    @media (max-width: 768px) {
        .main-header h2 { font-size: 16px !important; }
        .info-card { font-size: 12px !important; }
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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_name TEXT NOT NULL,
            sender_role TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL
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
    st.sidebar.markdown(f"👤 کاربر: **{st.session_state.user_name}** ({st.session_state.user_role})")
    
    menu_options = [
        "🏠 صفحه اصلی", 
        "📊 داشبورد آمار",
        "➕ ثبت‌نام", 
        "📝 حاضری", 
        "⭐ ارزیابی", 
        "👨‍🏫 پرسنل", 
        "💸 مصارف", 
        "🔍 پرونده‌ها", 
        "📈 گزارشات", 
        "💰 صندوق", 
        "👥 کاربران",
        "⚙️ تنظیمات",
        "💬 چت آنلاین",
        "📖 راهنما"
    ]
    
    menu = st.sidebar.radio("📌 منوی سیستم", menu_options)
    
    if st.sidebar.button("🚪 خروج از سیستم"):
        st.session_state.logged_in = False
        st.session_state.user_name = ""
        st.session_state.user_role = ""
        st.rerun()

    conn = sqlite3.connect(DB_FILE)

    # ==================== ۱. صفحه اصلی ====================
    if menu == "🏠 صفحه اصلی":
        st.markdown("""
        <div class="main-header">
            <h2>🏫 مکتب خصوصی کاوشگران دانش بلخ</h2>
            <p>سامانه جستجوی هوشمند پرونده دانش‌آموزان</p>
        </div>
        """, unsafe_allow_html=True)

        cursor = conn.cursor()
        cursor.execute("SELECT student_id, student_no, full_name, father_name, class_name FROM students WHERE status='فعال'")
        all_students = cursor.fetchall()

        student_options = {}
        for s_id, s_no, s_name, f_name, c_name in all_students:
            display_str = f"{s_name} (پدر: {f_name} | صنف: {c_name} | آی‌دی: {s_no})"
            student_options[display_str] = s_id

        st.markdown('<div class="search-card">', unsafe_allow_html=True)
        st.markdown("### 🔍 جستجوی شاگرد")
        
        # یک باکس واحد برای جستجو و انتخاب
        selected_display = st.selectbox(
            "نام شاگرد یا نام پدر را جستجو کنید:",
            options=[""] + list(student_options.keys()),
            key="main_search_box"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        target_id = student_options.get(selected_display) if selected_display else None

        if target_id:
            cursor.execute('''
                SELECT student_id, student_no, full_name, father_name, grandfather_name, class_name, standard_fee, is_free, 
                       uses_transport, transport_route, transport_fee, takes_books, books_fee, takes_uniform, uniform_fee, 
                       father_phone, mother_phone, registration_date
                FROM students WHERE student_id = ?
            ''', (target_id,))
            st_row = cursor.fetchone()

            if st_row:
                (s_id, no, name, father, gfather, cls, fee, is_free, uses_t, t_route, t_fee, 
                 takes_b, b_fee, takes_u, u_fee, fphone, mphone, reg_date) = st_row
                
                summary = get_student_financial_summary(s_id)
                
                if summary:
                    free_badge = " (رایگان / معاف)" if is_free == 1 else ""
                    st.markdown(f"""
                    <div class="info-card">
                        <b>🎓 نام شاگرد:</b> {name}{free_badge} | <b>🆔 آی‌دی:</b> {no}<br>
                        <b>👨 پدر:</b> {father} | <b>👴 پدرکلان:</b> {gfather} | <b>🏫 صنف:</b> {cls}<br>
                        <b>📞 تلفن پدر:</b> {fphone} | <b>📞 تلفن مادر:</b> {mphone} | <b>📅 تاریخ ثبت‌نام:</b> {reg_date}<br>
                        <b>💵 فیس ماهانه:</b> {summary['monthly_fee']:,.2f} افغانی | <b>📆 ماه‌های فعال:</b> {summary['active_months']} ماه<br>
                        <b>🚌 ترانسپورت:</b> {'دارد (' + t_route + ' - ' + str(t_fee) + ' افغانی)' if uses_t else 'ندارد'}<br>
                        <b>📚 کتاب:</b> {'دارد (' + str(b_fee) + ' افغانی)' if takes_b else 'ندارد'} | <b>👕 لباس:</b> {'دارد (' + str(u_fee) + ' افغانی)' if takes_u else 'ندارد'}<br>
                        <b>📊 ریز بدهی‌ها:</b> [قبلی: {summary['previous_debt']:,.2f}] | [شهریه: {summary['calc_tuition']:,.2f}] | [ترانسپورت: {summary['calc_transport']:,.2f}] | [کتاب: {summary['books_debt']:,.2f}] | [لباس: {summary['uniform_debt']:,.2f}]<br>
                        <b>🔻 باقی‌داری کل:</b> <span style="color:red; font-weight:bold;">{summary['net_debt']:,.2f} افغانی</span> | <b>🟢 بستانکاری/پیش‌پرداخت:</b> {summary['advance_pay']:,.2f} افغانی
                    </div>
                    """, unsafe_allow_html=True)

                    tab_pay, tab_break, tab_att, tab_eval, tab_edit = st.tabs(["💳 دریافت فیس", "📌 مرخصی", "📊 حاضری", "⭐ ارزیابی", "✏️ ویرایش"])

                    with tab_pay:
                        with st.form(f"pay_form_{s_id}"):
                            fee_type = st.selectbox("نوع فیس", ["شهریه ماه جاری", "باقی‌داری قبلی", "ترانسپورت", "کتاب", "لباس", "پیش‌پرداخت"], key=f"ft_{s_id}")
                            p_amt = st.number_input("مبلغ پرداختی (افغانی)", min_value=0.0, key=f"pa_{s_id}")
                            p_date = st.text_input("تاریخ", value=jdatetime.date.today().strftime("%Y/%m/%d"), key=f"pd_{s_id}")
                            p_desc = st.text_input("توضیحات", key=f"pdes_{s_id}")
                            if st.form_submit_button("ثبت پرداخت"):
                                if p_amt > 0:
                                    cursor.execute("INSERT INTO student_payments (student_id, date, trans_type, fee_type, amount, description, user_name) VALUES (?, ?, 'دریافت وجه', ?, ?, ?, ?)",
                                                   (s_id, p_date, fee_type, p_amt, p_desc, st.session_state.user_name))
                                    cursor.execute("INSERT INTO cashbox (date, type, category, amount, description, user_name) VALUES (?, 'Inflow', ?, ?, ?, ?)",
                                                   (p_date, f"دریافت {fee_type}", p_amt, f"پرداخت شاگرد ID:{s_id}\n{p_desc}", st.session_state.user_name))
                                    conn.commit()
                                    st.success("پرداخت ثبت گردید.")
                                    st.rerun()

                        cursor.execute("SELECT payment_id, date, fee_type, amount, description, user_name FROM student_payments WHERE student_id = ?", (s_id,))
                        p_rows = cursor.fetchall()
                        if p_rows:
                            st.dataframe(pd.DataFrame(p_rows, columns=["شناسه", "تاریخ", "نوع", "مبلغ", "توضیحات", "کاربر"]), use_container_width=True)

                    with tab_break:
                        with st.form(f"break_form_{s_id}"):
                            b_start = st.text_input("از تاریخ", key=f"bs_{s_id}")
                            b_end = st.text_input("تا تاریخ", key=f"be_{s_id}")
                            b_reason = st.text_input("دلیل", key=f"br_{s_id}")
                            if st.form_submit_button("ثبت مرخصی"):
                                if b_start and b_end:
                                    cursor.execute("INSERT INTO student_breaks (student_id, start_month, end_month, reason) VALUES (?, ?, ?, ?)",
                                                   (s_id, b_start, b_end, b_reason))
                                    conn.commit()
                                    st.success("مرخصی ثبت شد.")
                                    st.rerun()

                        cursor.execute("SELECT break_id, start_month, end_month, reason FROM student_breaks WHERE student_id = ?", (s_id,))
                        b_rows = cursor.fetchall()
                        if b_rows:
                            st.dataframe(pd.DataFrame(b_rows, columns=["شناسه", "از تاریخ", "تا تاریخ", "دلیل"]), use_container_width=True)

                    with tab_att:
                        cursor.execute("SELECT status, COUNT(*) FROM attendance WHERE student_id = ? GROUP BY status", (s_id,))
                        att_stats = {r[0]: r[1] for r in cursor.fetchall()}
                        p_c = sum(v for k, v in att_stats.items() if "حاضر" in k and "غیر" not in k)
                        a_c = sum(v for k, v in att_stats.items() if "غیرحاضر" in k)
                        l_c = sum(v for k, v in att_stats.items() if "رخصتی" in k)
                        st.write(f"✅ **حاضر:** {p_c} روز | ❌ **غیرحاضر:** {a_c} روز | 📌 **رخصتی:** {l_c} روز")

                    with tab_eval:
                        cursor.execute("SELECT evaluation_id, date, total_score FROM evaluations WHERE student_id = ? ORDER BY evaluation_id DESC", (s_id,))
                        st.dataframe(pd.DataFrame(cursor.fetchall(), columns=["شناسه", "تاریخ", "نمره"]), use_container_width=True)

                    with tab_edit:
                        with st.form(f"edit_form_{s_id}"):
                            e_name = st.text_input("نام کامل", value=str(name), key=f"ename_{s_id}")
                            e_father = st.text_input("نام پدر", value=str(father), key=f"efather_{s_id}")
                            e_fee = st.number_input("شهریه ماهانه", value=float(fee), key=f"efee_{s_id}")
                            e_free = st.checkbox("شاگرد رایگان", value=bool(is_free), key=f"efree_{s_id}")
                            e_fphone = st.text_input("تلفن پدر", value=str(fphone), key=f"efp_{s_id}")
                            if st.form_submit_button("ذخیره تغییرات"):
                                is_f_val = 1 if e_free else 0
                                fee_val = 0.0 if is_f_val else e_fee
                                cursor.execute("UPDATE students SET full_name=?, father_name=?, standard_fee=?, is_free=?, father_phone=? WHERE student_id=?",
                                               (e_name, e_father, fee_val, is_f_val, e_fphone, s_id))
                                conn.commit()
                                st.success("بروزرسانی شد.")
                                st.rerun()

    # ==================== ۱۱. کاربران ====================
    elif menu == "👥 کاربران":
        st.title("👥 مدیریت کاربران سیستم")
        
        if st.session_state.user_role != "Admin":
            st.error("⛔ فقط مدیر کل (Admin) دسترسی به این بخش دارد.")
        else:
            st.markdown("### ➕ تعریف کاربر جدید")
            with st.form("new_user_form"):
                nu_name = st.text_input("نام و نام خانوادگی *")
                nu_user = st.text_input("نام کاربری (Username) *")
                nu_pass = st.text_input("رمز عبور (Password) *", type="password")
                nu_role = st.selectbox("نقش کاربر", ["Admin", "Financial_Manager"])
                
                if st.form_submit_button("👤 ساخت کاربر جدید"):
                    if nu_name and nu_user and nu_pass:
                        cursor = conn.cursor()
                        try:
                            cursor.execute("INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
                                           (nu_user, nu_pass, nu_name, nu_role))
                            conn.commit()
                            st.success(f"کاربر «{nu_user}» با موفقیت ساخته شد.")
                            st.rerun()
                        except:
                            st.error("این نام کاربری قبلاً ثبت شده است.")
                    else:
                        st.warning("لطفاً تمامی موارد را پر کنید.")

            st.markdown("---")
            st.markdown("### 📋 لیست کاربران فعال")
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, username, full_name, role FROM users")
            users_list = cursor.fetchall()
            
            if users_list:
                df_u = pd.DataFrame(users_list, columns=["شناسه", "نام کاربری", "نام کامل", "نقش"])
                st.dataframe(df_u, use_container_width=True)
                
                del_u_id = st.number_input("شناسه کاربر جهت حذف:", min_value=1, step=1)
                if st.button("❌ حذف کاربر"):
                    cursor.execute("DELETE FROM users WHERE user_id = ?", (del_u_id,))
                    conn.commit()
                    st.success("کاربر حذف شد.")
                    st.rerun()

    # ==================== سایر بخش‌ها ====================
    elif menu == "📊 داشبورد آمار":
        st.title("📊 آمار و صندوق")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM students WHERE status='فعال'")
        s_count = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(amount) FROM cashbox WHERE type='Inflow'")
        inflow = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(amount) FROM cashbox WHERE type='Outflow'")
        outflow = cursor.fetchone()[0] or 0
        st.metric("تعداد شاگردان فعال", f"{s_count} نفر")
        st.metric("موجودی صندوق", f"{inflow - outflow:,.2f} افغانی")

    elif menu == "➕ ثبت‌نام":
        st.title("🎓 ثبت‌نام جدید")
        cursor = conn.cursor()
        cursor.execute("SELECT class_name FROM classes")
        classes = [r[0] for r in cursor.fetchall()]

        with st.form("r_form"):
            reg_no = st.text_input("آی‌دی *")
            reg_name = st.text_input("نام کامل *")
            reg_father = st.text_input("نام پدر *")
            reg_class = st.selectbox("صنف", classes)
            reg_fee = st.number_input("شهریه", value=1000.0)
            reg_date = st.text_input("تاریخ", value=jdatetime.date.today().strftime("%Y/%m/%d"))

            if st.form_submit_button("ثبت"):
                if reg_no and reg_name and reg_father:
                    cursor.execute("INSERT INTO students (student_no, full_name, father_name, grandfather_name, class_name, standard_fee, status, registration_date) VALUES (?, ?, ?, '', ?, ?, 'فعال', ?)",
                                   (reg_no, reg_name, reg_father, reg_class, reg_fee, reg_date))
                    conn.commit()
                    st.success("ثبت شد.")

    elif menu == "📝 حاضری":
        st.title("📋 حاضری")
        cursor = conn.cursor()
        cursor.execute("SELECT class_name FROM classes")
        classes = [r[0] for r in cursor.fetchall()]
        sel_c = st.selectbox("صنف", classes)
        att_d = st.text_input("تاریخ", value=jdatetime.date.today().strftime("%Y/%m/%d"))
        cursor.execute("SELECT student_id, full_name, father_name FROM students WHERE class_name=? AND status='فعال'", (sel_c,))
        st_list = cursor.fetchall()
        if st_list:
            with st.form("a_form"):
                for s_id, name, father in st_list:
                    st.selectbox(f"{name} ({father})", ["حاضر ✅", "غیرحاضر ❌"], key=f"a_{s_id}")
                if st.form_submit_button("ذخیره حاضری"):
                    st.success("ذخیره شد.")

    elif menu == "⭐ ارزیابی":
        st.title("⭐ ارزیابی")
        st.info("بخش ارزیابی فعال است.")

    elif menu == "👨‍🏫 پرسنل":
        st.title("👨‍🏫 پرسنل")
        cursor = conn.cursor()
        cursor.execute("SELECT staff_no, full_name, role_type, salary FROM staff")
        st.dataframe(pd.DataFrame(cursor.fetchall(), columns=["شناسه", "نام", "وظیفه", "معاش"]), use_container_width=True)

    elif menu == "💸 مصارف":
        st.title("💸 مصارف")
        cursor = conn.cursor()
        cursor.execute("SELECT date, category, amount, description FROM cashbox WHERE type='Outflow'")
        st.dataframe(pd.DataFrame(cursor.fetchall(), columns=["تاریخ", "دسته", "مبلغ", "توضیحات"]), use_container_width=True)

    elif menu == "🔍 پرونده‌ها":
        st.title("🔍 جستجو")
        q = st.text_input("نام یا آی‌دی:")
        cursor = conn.cursor()
        cursor.execute("SELECT student_no, full_name, father_name, class_name FROM students WHERE full_name LIKE ? OR student_no LIKE ?", (f"%{q}%", f"%{q}%"))
        st.dataframe(pd.DataFrame(cursor.fetchall(), columns=["آی‌دی", "نام", "پدر", "صنف"]), use_container_width=True)

    elif menu == "📈 گزارشات":
        st.title("📈 گزارشات")
        cursor = conn.cursor()
        cursor.execute("SELECT student_no, full_name, class_name, registration_date FROM students")
        st.dataframe(pd.DataFrame(cursor.fetchall(), columns=["آی‌دی", "نام", "صنف", "تاریخ"]), use_container_width=True)

    elif menu == "💰 صندوق":
        st.title("💰 صندوق")
        cursor = conn.cursor()
        cursor.execute("SELECT date, type, category, amount, description FROM cashbox")
        st.dataframe(pd.DataFrame(cursor.fetchall(), columns=["تاریخ", "نوع", "دسته", "مبلغ", "توضیحات"]), use_container_width=True)

    elif menu == "⚙️ تنظیمات":
        st.title("⚙️ تنظیمات")
        st.success("فعال است.")

    elif menu == "💬 چت آنلاین":
        st.title("💬 چت")
        cursor = conn.cursor()
        with st.form("c_form", clear_on_submit=True):
            msg = st.text_area("پیام:")
            if st.form_submit_button("ارسال") and msg.strip():
                t_str = jdatetime.datetime.now().strftime("%Y/%m/%d - %H:%M:%S")
                cursor.execute("INSERT INTO chat_messages (sender_name, sender_role, message, timestamp) VALUES (?, ?, ?, ?)",
                               (st.session_state.user_name, st.session_state.user_role, msg.strip(), t_str))
                conn.commit()
                st.rerun()

        cursor.execute("SELECT sender_name, sender_role, message, timestamp FROM chat_messages ORDER BY message_id DESC")
        for s_name, s_role, m_text, m_time in cursor.fetchall():
            with st.chat_message("user" if s_role == "Admin" else "assistant"):
                st.write(f"**{s_name}** ({s_role}) - *{m_time}*")
                st.write(m_text)

    elif menu == "📖 راهنما":
        st.title("📖 راهنما")
        st.markdown("سیستم مدیریت مکتب خصوصی کاوشگران دانش بلخ")

    conn.close()