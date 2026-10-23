import streamlit as st
import sqlite3
import jdatetime
import os

# تنظیمات صفحه وب
st.set_page_config(
    page_title="مکتب خصوصی کاوشگران دانش بلخ",
    page_icon="🏫",
    layout="wide"
)

# اتصال به دیتابیس موجود
DB_FILE = "school_finance.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

st.title("🏫 مکتب خصوصی کاوشگران دانش بلخ")
st.subheader("سیستم جامع مدیریت مالی و اداری (نسخه وب)")

# منوی ناوبری در سایدبار
menu = st.sidebar.selectbox(
    "انتخاب بخش", 
    ["داشبورد", "ثبت‌نام شاگردان", "جستجو و لیست شاگردان", "مدیریت صندوق و مصارف", "پرسنل و استادان"]
)

# بخش داشبورد
if menu == "داشبورد":
    st.markdown("### 📊 داشبورد مدیریتی")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # تعداد شاگردان فعال
        cursor.execute("SELECT COUNT(*) FROM students WHERE status='فعال'")
        s_count = cursor.fetchone()[0]
        
        # موجودی صندوق
        cursor.execute("SELECT SUM(amount) FROM cashbox WHERE type='Inflow'")
        inflow = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(amount) FROM cashbox WHERE type='Outflow'")
        outflow = cursor.fetchone()[0] or 0
        total_cash = inflow - outflow
        
        conn.close()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="دانش‌آموزان فعال", value=f"{s_count} نفر")
        with col2:
            st.metric(label="موجودی فعلی صندوق", value=f"{total_cash:,.2f} افغانی")
            
    except Exception as e:
        st.error(f"خطا در خواندن دیتابیس: لطفاً مطمئن شوید فایل `school_finance.db` آپلود شده است.\nجزئیات خطا: {e}")

# بخش ثبت‌نام شاگردان
elif menu == "ثبت‌نام شاگردان":
    st.markdown("### 🎓 فرم ثبت نام شاگرد جدید")
    
    with st.form("registration_form"):
        col1, col2 = st.columns(2)
        with col1:
            reg_no = st.text_input("نمبر آی‌دی")
            reg_name = st.text_input("نام کامل شاگرد")
            reg_father = st.text_input("نام پدر")
            reg_gfather = st.text_input("نام پدرکلان")
        with col2:
            reg_class = st.text_input("صنف (مثلاً صنف اول)")
            reg_fee = st.number_input("شهریه ماهانه (افغانی)", min_value=0.0, value=1000.0)
            reg_fphone = st.text_input("شماره تماس پدر")
            reg_date = st.text_input("تاریخ ثبت‌نام", value=jdatetime.date.today().strftime("%Y/%m/%d"))
            
        submitted = st.form_submit_button("ثبت نهایی دانش‌آموز")
        
        if submitted:
            if not reg_no or not reg_name:
                st.warning("لطفاً نمبر آی‌دی و نام کامل را وارد کنید.")
            else:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO students (student_no, full_name, father_name, grandfather_name, class_name, standard_fee, father_phone, registration_date, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'فعال')
                    ''', (reg_no, reg_name, reg_father, reg_gfather, reg_class, reg_fee, reg_fphone, reg_date))
                    conn.commit()
                    conn.close()
                    st.success("دانش‌آموز با موفقیت ثبت شد!")
                except Exception as e:
                    st.error(f"خطا در ثبت اطلاعات: {e}")

# بخش جستجو و لیست شاگردان
elif menu == "جستجو و لیست شاگردان":
    st.markdown("### 🔍 لیست و جستجوی شاگردان")
    search_query = st.text_input("جستجو بر اساس نام یا آی‌دی:")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if search_query:
            cursor.execute("SELECT student_no, full_name, father_name, class_name, standard_fee, registration_date FROM students WHERE full_name LIKE ? OR student_no LIKE ?", (f"%{search_query}%", f"%{search_query}%"))
        else:
            cursor.execute("SELECT student_no, full_name, father_name, class_name, standard_fee, registration_date FROM students")
        
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            import pandas as pd
            df = pd.DataFrame(rows, columns=["نمبر آی‌دی", "نام کامل", "نام پدر", "صنف", "شهریه", "تاریخ ثبت‌نام"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("هیچ شاگردی یافت نشد.")
    except Exception as e:
        st.error(f"خطا در بارگذاری اطلاعات: {e}")

# بخش مدیریت صندوق و مصارف
elif menu == "مدیریت صندوق و مصارف":
    st.markdown("### 💰 گردش صندوق و مصارف مکتب")
    try:
        conn = get_connection()
        import pandas as pd
        df_cash = pd.read_sql("SELECT date, type, category, amount, description, user_name FROM cashbox", conn)
        conn.close()
        st.dataframe(df_cash, use_container_width=True)
    except Exception as e:
        st.error(f"خطا در خواندن اطلاعات صندوق: {e}")

# بخش پرسنل و استادان
elif menu == "پرسنل و استادان":
    st.markdown("### 👨‍🏫 لیست پرسنل و استادان")
    try:
        conn = get_connection()
        import pandas as pd
        df_staff = pd.read_sql("SELECT staff_no, full_name, role_type, phone, salary, registration_date FROM staff", conn)
        conn.close()
        st.dataframe(df_staff, use_container_width=True)
    except Exception as e:
        st.error(f"خطا در خواندن اطلاعات پرسنل: {e}")