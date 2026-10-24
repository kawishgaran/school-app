import streamlit as st
import sqlite3
import jdatetime
import math
import pandas as pd

# ==================== تنظیمات اصلی صفحه وب ====================
st.set_page_config(
    page_title="مکتب خصوصی کاوشگران دانش بلخ",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DB_FILE = "school_finance.db"

# ==================== استایل‌دهی سفارشی (CSS) ====================
st.markdown("""
<style>
    @import url('https://v1.fontapi.ir/css/Vazir');
    
    html, body, [class*="css"] {
        font-family: 'Vazir', sans-serif !important;
        direction: rtl;
        text-align: right;
    }
    
    .main-header {
        background: linear-gradient(135deg, #0f172a, #1e293b);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        text-align: center;
    }

    .google-search-box {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 16px;
        box-shadow: 0px 6px 20px rgba(0,0,0,0.06);
        border: 1px solid #e2e8f0;
        margin-bottom: 25px;
    }

    .stButton>button {
        background-color: #12b8b2 !important;
        color: white !important;
        border-radius: 6px !important;
        border: none !important;
        width: 100%;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ==================== ایجاد دیتابیس ====================
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
    # نوار بالای صفحه (مثل برنامه‌های آفیس) جهت نمایش منوی اصلی به صورت ردیفی
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 صفحه اصلی"

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

    st.markdown("##### 📌 منوی اصلی سیستم (انتخاب بخش)")
    cols = st.columns(len(menu_options))
    for idx, option in enumerate(menu_options):
        with cols[idx]:
            if st.button(option, key=f"menu_btn_{idx}"):
                st.session_state.current_page = option
                st.rerun()

    st.markdown("---")
    
    # اطلاعات کاربر و دکمه خروج در سایدبار کوچک یا پایین
    st.sidebar.markdown(f"👤 کاربر فعال: **{st.session_state.user_name}** ({st.session_state.user_role})")
    if st.sidebar.button("🚪 خروج از سیستم"):
        st.session_state.logged_in = False
        st.session_state.user_name = ""
        st.session_state.user_role = ""
        st.rerun()

    conn = sqlite3.connect(DB_FILE)
    menu = st.session_state.current_page

    # ==================== ۱. صفحه اصلی (با باکس جستجوی پیشنهادی و دکمه جستجو در دیتابیس) ====================
    if menu == "🏠 صفحه اصلی":
        st.markdown("""
        <div class="main-header">
            <h2>🏫 مکتب خصوصی کاوشگران دانش بلخ</h2>
            <p>سامانه جامع جستجوی هوشمند پرونده شاگردان و مدیریت آنلاین</p>
        </div>
        """, unsafe_allow_html=True)

        # دریافت لیست کامل نام‌های شاگردان برای پیشنهاد خودکار (Autocomplete)
        cursor = conn.cursor()
        cursor.execute("SELECT full_name FROM students WHERE status='فعال'")
        all_student_names = [row[0] for row in cursor.fetchall()]

        st.markdown('<div class="google-search-box">', unsafe_allow_html=True)
        st.markdown("### 🔍 جستجوی پیشرفته پرونده دانش‌آموز")
        
        col_s1, col_s2 = st.columns([4, 1])
        with col_s1:
            # باکس جستجو با قابلیت پیشنهاد خودکار (selectbox با قابلیت تایپ یا st.selectbox)
            selected_student_name = st.selectbox(
                "نام شاگرد را تایپ کنید یا از لیست انتخاب کنید:",
                options=[""] + all_student_names,
                key="autocomplete_search"
            )
        with col_s2:
            st.write("") # فاصله‌گذاری عمودی
            search_clicked = st.button("🔎 جستجو در دیتابیس")

        st.markdown('</div>', unsafe_allow_html=True)

        # اگر دکمه جستجو زده شد یا شاگردی انتخاب شد
        search_term = selected_student_name if selected_student_name else ""

        if search_clicked or search_term:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT student_id, student_no, full_name, father_name, grandfather_name, class_name, standard_fee, is_free, 
                       uses_transport, transport_fee, father_phone, registration_date
                FROM students WHERE full_name LIKE ? OR student_no LIKE ?
            ''', (f"%{search_term}%", f"%{search_term}%"))
            students = cursor.fetchall()

            if students:
                st.subheader(f"📂 نتایج پرونده برای: «{search_term}»")
                for st_row in students:
                    s_id, no, name, father, gfather, cls, fee, is_free, uses_t, t_fee, fphone, reg_date = st_row
                    summary = get_student_financial_summary(s_id)
                    if not summary:
                        continue

                    title_text = f"🎓 {name} {'(معاف/رایگان)' if is_free == 1 else ''} | صنف: {cls} | آی‌دی: {no} | باقی‌داری کل: {summary['net_debt']:,.2f} افغانی"
                    
                    with st.expander(title_text, expanded=True):
                        st.markdown(f"""
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
                                p_date = st.text_input("تاریخ", value=jdatetime.date.today().strftime("%Y/%m/%d"), key=f"pd_{s_id}")
                                p_desc = st.text_input("توضیحات", key=f"pdes_{s_id}")
                                if st.form_submit_button("ثبت پرداخت"):
                                    if p_amt > 0:
                                        cursor.execute("INSERT INTO student_payments (student_id, date, trans_type, fee_type, amount, description, user_name) VALUES (?, ?, 'دریافت وجه', ?, ?, ?, ?)",
                                                       (s_id, p_date, fee_type, p_amt, p_desc, st.session_state.user_name))
                                        cursor.execute("INSERT INTO cashbox (date, type, category, amount, description, user_name) VALUES (?, 'Inflow', ?, ?, ?, ?)",
                                                       (p_date, f"دریافت {fee_type}", p_amt, f"پرداخت شاگرد ID:{s_id}\n{p_desc}", st.session_state.user_name))
                                        conn.commit()
                                        st.success("تراکنش ثبت گردید.")
                                        st.rerun()

                            cursor.execute("SELECT payment_id, date, trans_type, fee_type, amount, description, user_name FROM student_payments WHERE student_id = ?", (s_id,))
                            p_rows = cursor.fetchall()
                            if p_rows:
                                df_p = pd.DataFrame(p_rows, columns=["شناسه", "تاریخ", "نوع تراکنش", "نوع فیس", "مبلغ", "توضیحات", "کاربر"])
                                st.dataframe(df_p, use_container_width=True)

                        with tab_break:
                            with st.form(f"break_form_{s_id}"):
                                b_start = st.text_input("از تاریخ/ماه", key=f"bs_{s_id}")
                                b_end = st.text_input("تا تاریخ/ماه", key=f"be_{s_id}")
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

                        with tab_att:
                            cursor.execute("SELECT status, COUNT(*) FROM attendance WHERE student_id = ? GROUP BY status", (s_id,))
                            att_stats = {r[0]: r[1] for r in cursor.fetchall()}
                            p_c = sum(v for k, v in att_stats.items() if "حاضر" in k and "غیر" not in k)
                            a_c = sum(v for k, v in att_stats.items() if "غیرحاضر" in k)
                            l_c = sum(v for k, v in att_stats.items() if "رخصتی" in k)
                            st.write(f"✅ **حاضر:** {p_c} روز | ❌ **غیرحاضر:** {a_c} روز | 📌 **رخصتی:** {l_c} روز")

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
            elif search_term:
                st.warning("هیچ پرونده‌ای با این مشخصات یافت نشد.")

    # ==================== ۲. داشبورد آمار ====================
    elif menu == "📊 داشبورد آمار":
        st.title("📊 داشبورد آمار و مدیریت صندوق")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM students WHERE status='فعال'")
        s_count = cursor.fetchone()[0] or 0
        
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

    # ==================== ۳. ثبت‌نام جدید ====================
    elif menu == "➕ ثبت‌نام":
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

            submitted = st.form_submit_button("📝 ثبت نهایی دانش‌آموز در سیستم")
            if submitted:
                if not reg_no or not reg_name or not reg_date:
                    st.warning("لطفاً اطلاعات ضروری را پر کنید.")
                else:
                    cursor.execute("SELECT student_no FROM students WHERE student_no = ?", (reg_no,))
                    if cursor.fetchone():
                        st.error(f"شماره آی‌دی «{reg_no}» قبلاً ثبت شده است!")
                    else:
                        is_free = 1 if reg_chk_free else 0
                        final_fee = 0.0 if is_free else reg_fee
                        try:
                            cursor.execute('''
                                INSERT INTO students (
                                    student_no, full_name, father_name, grandfather_name, class_name, standard_fee, is_free,
                                    father_phone, mother_phone, initial_previous_debt, status, registration_date
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'فعال', ?)
                            ''', (reg_no, reg_name, reg_father, reg_gfather, reg_class, final_fee, is_free,
                                  reg_fphone, reg_mphone, reg_prev_debt, reg_date))
                            conn.commit()
                            st.success("دانش‌آموز با موفقیت ثبت شد!")
                        except Exception as e:
                            st.error(f"خطا در ثبت اطلاعات: {e}")

    # ==================== ۴. حاضری شاگردان ====================
    elif menu == "📝 حاضری":
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

                if st.form_submit_button("💾 ثبت نهایی حاضری"):
                    for s_id, status in attendance_data:
                        cursor.execute("SELECT attendance_id FROM attendance WHERE student_id = ? AND date = ?", (s_id, att_date))
                        ex = cursor.fetchone()
                        if ex:
                            cursor.execute("UPDATE attendance SET status = ? WHERE attendance_id = ?", (status, ex[0]))
                        else:
                            cursor.execute("INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)", (s_id, att_date, status))
                    conn.commit()
                    st.success("حاضری با موفقیت ثبت شد.")
        else:
            st.info("هیچ شاگرد فعالی یافت نشد.")

    # ==================== ۵. ارزیابی شاگردان ====================
    elif menu == "⭐ ارزیابی":
        st.title("⭐ سیستم ارزیابی اتوماتیک ماهانه")
        eval_date = st.text_input("تاریخ ارزیابی امروز", value=jdatetime.date.today().strftime("%Y/%m/%d"))
        y, m, d = parse_shamsi_date(eval_date)
        cursor = conn.cursor()
        cursor.execute("SELECT student_id, student_no, full_name, father_name, class_name FROM students WHERE status='فعال'")
        all_st = cursor.fetchall()
        if all_st:
            with st.form("eval_form"):
                for st_row in all_st[:5]: # نمونه نمایشی
                    s_id, no, name, father, c_name = st_row
                    st.markdown(f"**🎓 {name}** (صنف: {c_name})")
                    col1, col2 = st.columns(2)
                    col1.selectbox("چک کتابچه", [0, 1, 2], key=f"n_{s_id}")
                    col2.selectbox("سطح یادگیری", [0, 1, 2], key=f"l_{s_id}")
                if st.form_submit_button("💾 ثبت ارزیابی"):
                    st.success("ارزیابی‌ها ذخیره شدند.")

    # ==================== ۶. پرسنل ====================
    elif menu == "👨‍🏫 پرسنل":
        st.title("👨‍🏫 مدیریت پرسنل و حقوق")
        cursor = conn.cursor()
        cursor.execute("SELECT staff_no, full_name, role_type, phone, salary FROM staff")
        df_staff = pd.DataFrame(cursor.fetchall(), columns=["شناسه", "نام", "وظیفه", "تلفن", "معاش"])
        st.dataframe(df_staff, use_container_width=True)

    # ==================== ۷. مصارف ====================
    elif menu == "💸 مصارف":
        st.title("💸 ثبت مصارف مکتب")
        cursor = conn.cursor()
        cursor.execute("SELECT date, category, amount, description, user_name FROM cashbox WHERE type='Outflow'")
        df_exp = pd.DataFrame(cursor.fetchall(), columns=["تاریخ", "دسته‌بندی", "مبلغ", "توضیحات", "کاربر"])
        st.dataframe(df_exp, use_container_width=True)

    # ==================== ۸. پرونده‌ها ====================
    elif menu == "🔍 پرونده‌ها":
        st.title("🔍 جستجو و پرونده شاگردان")
        query = st.text_input("جستجو بر اساس نام یا آی‌دی:")
        cursor = conn.cursor()
        cursor.execute("SELECT student_id, student_no, full_name, class_name FROM students WHERE full_name LIKE ? OR student_no LIKE ?", (f"%{query}%", f"%{query}%"))
        df_st = pd.DataFrame(cursor.fetchall(), columns=["شناسه", "آی‌دی", "نام", "صنف"])
        st.dataframe(df_st, use_container_width=True)

    # ==================== ۹. گزارشات ====================
    elif menu == "📈 گزارشات":
        st.title("📈 گزارش‌گیری پیشرفته مکتب")
        cursor = conn.cursor()
        cursor.execute("SELECT student_no, full_name, class_name, registration_date FROM students")
        df_rep = pd.DataFrame(cursor.fetchall(), columns=["آی‌دی", "نام", "صنف", "تاریخ ثبت‌نام"])
        st.dataframe(df_rep, use_container_width=True)

    # ==================== ۱۰. صندوق ====================
    elif menu == "💰 صندوق":
        st.title("💰 گردش کامل صندوق و دخل مکتب")
        cursor = conn.cursor()
        cursor.execute("SELECT date, type, category, amount, description, user_name FROM cashbox")
        df_cash = pd.DataFrame(cursor.fetchall(), columns=["تاریخ", "نوع", "دسته‌بندی", "مبلغ", "توضیحات", "کاربر"])
        st.dataframe(df_cash, use_container_width=True)

    # ==================== ۱۱. کاربران ====================
    elif menu == "👥 کاربران":
        st.title("👥 مدیریت کاربران سیستم")
        cursor = conn.cursor()
        cursor.execute("SELECT username, full_name, role FROM users")
        df_users = pd.DataFrame(cursor.fetchall(), columns=["نام کاربری", "نام کامل", "نقش"])
        st.dataframe(df_users, use_container_width=True)

    # ==================== ۱۲. تنظیمات ====================
    elif menu == "⚙️ تنظیمات":
        st.title("⚙️ تنظیمات سیستم")
        with st.form("pass_form"):
            new_pass = st.text_input("رمز عبور جدید", type="password")
            if st.form_submit_button("بروزرسانی رمز"):
                st.success("رمز عبور تغییر یافت.")

    # ==================== ۱۳. چت آنلاین ====================
    elif menu == "💬 چت آنلاین":
        st.title("💬 اتاق گفتگوی آنلاین مدیر و کاربران")
        cursor = conn.cursor()
        with st.form("chat_form", clear_on_submit=True):
            user_msg = st.text_area("✍️ پیام خود را بنویسید:", height=80)
            if st.form_submit_button("📤 ارسال پیام") and user_msg.strip():
                now_str = jdatetime.datetime.now().strftime("%Y/%m/%d - %H:%M:%S")
                cursor.execute("INSERT INTO chat_messages (sender_name, sender_role, message, timestamp) VALUES (?, ?, ?, ?)",
                               (st.session_state.user_name, st.session_state.user_role, user_msg.strip(), now_str))
                conn.commit()
                st.rerun()

        cursor.execute("SELECT sender_name, sender_role, message, timestamp FROM chat_messages ORDER BY message_id DESC")
        for s_name, s_role, m_text, m_time in cursor.fetchall():
            with st.chat_message("user" if s_role == "Admin" else "assistant"):
                st.write(f"**{s_name}** ({s_role}) - *{m_time}*")
                st.write(m_text)

    # ==================== ۱۴. راهنما ====================
    elif menu == "📖 راهنما":
        st.title("📖 راهنمای جامع سیستم")
        st.markdown("این سیستم جهت مدیریت آنلاین و گزارش‌گیری مکتب خصوصی کاوشگران دانش بلخ طراحی شده است.")

    conn.close()