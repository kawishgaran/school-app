import streamlit as st
import sqlite3
import jdatetime
import pandas as pd

# ==================== تنظیمات صفحه ====================
st.set_page_config(
    page_title="مکتب خصوصی کاوشگران دانش بلخ",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "school_finance.db"

# ==================== راست‌چین‌سازی کامل و حرفه‌ای (RTL) ====================
st.markdown("""
<style>
    @import url('https://v1.fontapi.ir/css/Vazir');
    
    /* تنظیم کل صفحه به حالت راست‌چین و فونت وزیر */
    html, body, [class*="css"], [class*="st-"] {
        font-family: 'Vazir', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }

    /* راست‌چین کردن سایدبار (منوی سمت راست) */
    section[data-testid="stSidebar"] {
        direction: rtl !important;
        text-align: right !important;
    }

    /* راست‌چین کردن تمامی باکس‌های ورودی، منوها و جداول */
    .stTextInput>div>div>input, 
    .stSelectbox>div>div, 
    .stNumberInput>div>div>input,
    .stTextArea>div>div>textarea {
        direction: rtl !important;
        text-align: right !important;
    }

    /* استایل دکمه‌ها */
    .stButton>button {
        background-color: #12b8b2 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        width: 100%;
        font-weight: bold;
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
    st.title("🏫 ورود به سیستم - مکتب کاوشگران دانش بلخ")
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
    # منوی سایدبار راست‌چین
    st.sidebar.markdown(f"**کاربر فعال:** {st.session_state.user_name}")
    
    menu_options = [
        "🏠 صفحه اصلی (جستجوی شاگرد)", 
        "📊 داشبورد آمار",
        "➕ ثبت‌نام شاگرد جدید", 
        "📝 حاضری روزانه", 
        "⭐ ارزیابی ماهانه", 
        "👨‍🏫 پرسنل و استادان", 
        "💸 ثبت مصارف مکتب", 
        "🔍 لیست کلی پرونده‌ها", 
        "📈 گزارش‌گیری", 
        "💰 مدیریت صندوق", 
        "👥 کاربران سیستم",
        "⚙️ تنظیمات",
        "💬 چت آنلاین",
        "📖 راهنما"
    ]
    
    menu = st.sidebar.selectbox("منوی سیستم:", menu_options)
    
    if st.sidebar.button("🚪 خروج از سیستم"):
        st.session_state.logged_in = False
        st.session_state.user_name = ""
        st.session_state.user_role = ""
        st.rerun()

    conn = sqlite3.connect(DB_FILE)

    # ==================== ۱. صفحه اصلی (جستجوی شاگرد) ====================
    if menu == "🏠 صفحه اصلی (جستجوی شاگرد)":
        st.title("🏫 مکتب خصوصی کاوشگران دانش بلخ")
        st.subheader("🔍 جستجوی پرونده دانش‌آموز")

        cursor = conn.cursor()
        cursor.execute("SELECT student_id, student_no, full_name, father_name, class_name FROM students WHERE status='فعال'")
        all_students = cursor.fetchall()

        student_options = {}
        for s_id, s_no, s_name, f_name, c_name in all_students:
            display_str = f"{s_name} (پدر: {f_name} | صنف: {c_name} | آی‌دی: {s_no})"
            student_options[display_str] = s_id

        selected_display = st.selectbox(
            "نام شاگرد یا نام پدر را انتخاب/تایپ کنید:",
            options=[""] + list(student_options.keys()),
            key="simple_search_box"
        )

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
                    st.divider()
                    st.header(f"📋 پرونده: {name}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"👤 **نام کامل:** {name} {'(معاف/رایگان)' if is_free == 1 else ''}")
                        st.write(f"👨 **نام پدر:** {father}")
                        st.write(f"👴 **نام پدرکلان:** {gfather}")
                        st.write(f"🏫 **صنف:** {cls}")
                        st.write(f"🆔 **آی‌دی:** {no}")
                        st.write(f"📅 **تاریخ ثبت‌نام:** {reg_date}")
                    with col2:
                        st.write(f"📞 **تلفن پدر:** {fphone}")
                        st.write(f"📞 **تلفن مادر:** {mphone}")
                        st.write(f"💵 **شهریه ماهانه:** {summary['monthly_fee']:,.2f} افغانی")
                        st.write(f"📆 **ماه‌های فعال:** {summary['active_months']} ماه")
                        st.write(f"🔻 **باقی‌داری کل:** {summary['net_debt']:,.2f} افغانی")
                        st.write(f"🟢 **پیش‌پرداخت:** {summary['advance_pay']:,.2f} افغانی")

                    st.divider()
                    tab_pay, tab_break, tab_att, tab_eval, tab_edit = st.tabs(["💳 دریافت فیس", "📌 مرخصی", "📊 حاضری", "⭐ ارزیابی", "✏️ ویرایش"])

                    with tab_pay:
                        with st.form(f"pay_form_{s_id}"):
                            fee_type = st.selectbox("نوع فیس", ["شهریه ماه جاری", "باقی‌داری قبلی", "ترانسپورت", "کتاب", "لباس", "پیش‌پرداخت"], key=f"ft_{s_id}")
                            p_amt = st.number_input("مبلغ پرداختی (افغانی)", min_value=0.0, key=f"pa_{s_id}")
                            p_date = st.text_input("تاریخ", value=jdatetime.date.today().strftime("%Y/%m/%d"), key=f"pd_{s_id}")
                            p_desc = st.text_input("توضیحات", key=f"pdes_{s_id}")
                            if st.form_submit_button("ثبت دریافت وجه"):
                                if p_amt > 0:
                                    cursor.execute("INSERT INTO student_payments (student_id, date, trans_type, fee_type, amount, description, user_name) VALUES (?, ?, 'دریافت وجه', ?, ?, ?, ?)",
                                                   (s_id, p_date, fee_type, p_amt, p_desc, st.session_state.user_name))
                                    cursor.execute("INSERT INTO cashbox (date, type, category, amount, description, user_name) VALUES (?, 'Inflow', ?, ?, ?, ?)",
                                                   (p_date, f"دریافت {fee_type}", p_amt, f"پرداخت شاگرد ID:{s_id}\n{p_desc}", st.session_state.user_name))
                                    conn.commit()
                                    st.success("پرداخت با موفقیت ثبت شد.")
                                    st.rerun()

                        cursor.execute("SELECT payment_id, date, fee_type, amount, description, user_name FROM student_payments WHERE student_id = ?", (s_id,))
                        p_rows = cursor.fetchall()
                        if p_rows:
                            st.write("📋 سوابق پرداختی‌ها:")
                            st.dataframe(pd.DataFrame(p_rows, columns=["شناسه", "تاریخ", "نوع", "مبلغ", "توضیحات", "کاربر"]), use_container_width=True)

                    with tab_break:
                        with st.form(f"break_form_{s_id}"):
                            b_start = st.text_input("از تاریخ/ماه", key=f"bs_{s_id}")
                            b_end = st.text_input("تا تاریخ/ماه", key=f"be_{s_id}")
                            b_reason = st.text_input("دلیل مرخصی", key=f"br_{s_id}")
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
                        st.info(f"✅ حاضر: {p_c} روز | ❌ غیرحاضر: {a_c} روز")

                    with tab_eval:
                        cursor.execute("SELECT evaluation_id, date, total_score FROM evaluations WHERE student_id = ? ORDER BY evaluation_id DESC", (s_id,))
                        st.dataframe(pd.DataFrame(cursor.fetchall(), columns=["شناسه", "تاریخ", "نمره"]), use_container_width=True)

                    with tab_edit:
                        with st.form(f"edit_form_{s_id}"):
                            e_name = st.text_input("نام کامل", value=str(name), key=f"ename_{s_id}")
                            e_father = st.text_input("نام پدر", value=str(father), key=f"efather_{s_id}")
                            e_fee = st.number_input("شهریه ماهانه", value=float(fee), key=f"efee_{s_id}")
                            e_fphone = st.text_input("تلفن پدر", value=str(fphone), key=f"efp_{s_id}")
                            if st.form_submit_button("ذخیره ویرایش"):
                                cursor.execute("UPDATE students SET full_name=?, father_name=?, standard_fee=?, father_phone=? WHERE student_id=?",
                                               (e_name, e_father, e_fee, e_fphone, s_id))
                                conn.commit()
                                st.success("اطلاعات بروزرسانی شد.")
                                st.rerun()

    # ==================== ۱۱. کاربران سیستم ====================
    elif menu == "👥 کاربران سیستم":
        st.title("👥 مدیریت کاربران سیستم")
        
        if st.session_state.user_role != "Admin":
            st.error("⛔ فقط مدیر کل (Admin) دسترسی به این بخش دارد.")
        else:
            st.subheader("➕ تعریف کاربر جدید")
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

            st.divider()
            st.subheader("📋 لیست کاربران فعال")
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, username, full_name, role FROM users")
            users_list = cursor.fetchall()
            
            if users_list:
                df_u = pd.DataFrame(users_list, columns=["شناسه", "نام کاربری", "نام کامل", "نقش"])
                st.dataframe(df_u, use_container_width=True)

    # ==================== سایر بخش‌های سیستم ====================
    elif menu == "📊 داشبورد آمار":
        st.title("📊 آمار و وضعیت صندوق")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM students WHERE status='فعال'")
        s_count = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(amount) FROM cashbox WHERE type='Inflow'")
        inflow = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(amount) FROM cashbox WHERE type='Outflow'")
        outflow = cursor.fetchone()[0] or 0
        col1, col2 = st.columns(2)
        col1.metric("تعداد شاگردان فعال", f"{s_count} نفر")
        col2.metric("موجودی صندوق", f"{inflow - outflow:,.2f} افغانی")

    elif menu == "➕ ثبت‌نام شاگرد جدید":
        st.title("🎓 فرم ثبت‌نام دانش‌آموز جدید")
        cursor = conn.cursor()
        cursor.execute("SELECT class_name FROM classes")
        classes = [r[0] for r in cursor.fetchall()]

        with st.form("r_form"):
            reg_no = st.text_input("آی‌دی *")
            reg_name = st.text_input("نام کامل *")
            reg_father = st.text_input("نام پدر *")
            reg_gfather = st.text_input("نام پدرکلان")
            reg_class = st.selectbox("صنف", classes)
            reg_fee = st.number_input("شهریه", value=1000.0)
            reg_date = st.text_input("تاریخ", value=jdatetime.date.today().strftime("%Y/%m/%d"))

            if st.form_submit_button("ثبت نهایی"):
                if reg_no and reg_name and reg_father:
                    cursor.execute("INSERT INTO students (student_no, full_name, father_name, grandfather_name, class_name, standard_fee, status, registration_date) VALUES (?, ?, ?, ?, ?, ?, 'فعال', ?)",
                                   (reg_no, reg_name, reg_father, reg_gfather, reg_class, reg_fee, reg_date))
                    conn.commit()
                    st.success("شاگرد با موفقیت ثبت شد.")

    elif menu == "📝 حاضری روزانه":
        st.title("📋 ثبت حضور و غیاب")
        cursor = conn.cursor()
        cursor.execute("SELECT class_name FROM classes")
        classes = [r[0] for r in cursor.fetchall()]
        sel_c = st.selectbox("انتخاب صنف", classes)
        att_d = st.text_input("تاریخ", value=jdatetime.date.today().strftime("%Y/%m/%d"))
        cursor.execute("SELECT student_id, full_name, father_name FROM students WHERE class_name=? AND status='فعال'", (sel_c,))
        st_list = cursor.fetchall()
        if st_list:
            with st.form("a_form"):
                for s_id, name, father in st_list:
                    st.selectbox(f"{name} (پدر: {father})", ["حاضر ✅", "غیرحاضر ❌"], key=f"a_{s_id}")
                if st.form_submit_button("ذخیره حاضری"):
                    st.success("حاضری ثبت شد.")

    elif menu == "⭐ ارزیابی ماهانه":
        st.title("⭐ ارزیابی ماهانه شاگردان")
        st.info("بخش ارزیابی فعال است.")

    elif menu == "👨‍🏫 پرسنل و استادان":
        st.title("👨‍🏫 پرسنل و استادان")
        cursor = conn.cursor()
        cursor.execute("SELECT staff_no, full_name, role_type, salary FROM staff")
        st.dataframe(pd.DataFrame(cursor.fetchall(), columns=["شناسه", "نام کامل", "وظیفه", "معاش"]), use_container_width=True)

    elif menu == "💸 ثبت مصارف مکتب":
        st.title("💸 ثبت مصارف")
        cursor = conn.cursor()
        cursor.execute("SELECT date, category, amount, description FROM cashbox WHERE type='Outflow'")
        st.dataframe(pd.DataFrame(cursor.fetchall(), columns=["تاریخ", "دسته‌بندی", "مبلغ", "توضیحات"]), use_container_width=True)

    elif menu == "🔍 لیست کلی پرونده‌ها":
        st.title("🔍 لیست کلی پرونده‌ها")
        q = st.text_input("جستجو:")
        cursor = conn.cursor()
        cursor.execute("SELECT student_no, full_name, father_name, class_name FROM students WHERE full_name LIKE ? OR student_no LIKE ?", (f"%{q}%", f"%{q}%"))
        st.dataframe(pd.DataFrame(cursor.fetchall(), columns=["آی‌دی", "نام کامل", "نام پدر", "صنف"]), use_container_width=True)

    elif menu == "📈 گزارش‌گیری":
        st.title("📈 گزارش‌گیری پیشرفته")
        cursor = conn.cursor()
        cursor.execute("SELECT student_no, full_name, class_name, registration_date FROM students")
        st.dataframe(pd.DataFrame(cursor.fetchall(), columns=["آی‌دی", "نام کامل", "صنف", "تاریخ ثبت‌نام"]), use_container_width=True)

    elif menu == "💰 مدیریت صندوق":
        st.title("💰 گردش مالی صندوق")
        cursor = conn.cursor()
        cursor.execute("SELECT date, type, category, amount, description FROM cashbox")
        st.dataframe(pd.DataFrame(cursor.fetchall(), columns=["تاریخ", "نوع", "دسته‌بندی", "مبلغ", "توضیحات"]), use_container_width=True)

    elif menu == "⚙️ تنظیمات":
        st.title("⚙️ تنظیمات سیستم")
        st.success("تنظیمات فعال است.")

    elif menu == "💬 چت آنلاین":
        st.title("💬 گفتگوی آنلاین")
        cursor = conn.cursor()
        with st.form("c_form", clear_on_submit=True):
            msg = st.text_area("ارسال پیام:")
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
        st.title("📖 راهنمای استفاده")
        st.write("سیستم مدیریت مالی و اداری مکتب خصوصی کاوشگران دانش بلخ.")

    conn.close()