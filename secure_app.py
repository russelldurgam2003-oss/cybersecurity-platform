import streamlit as str_app
import time
import base64
import pymysql  # مكتبة الاتصال بقاعدة بيانات MySQL
from core_system import AIAdaptiveSecuritySystem

# إعداد الصفحة واجهة عريضة
str_app.set_page_config(page_title="منصة الأمن التكيفي الذكي", layout="wide")

# --- ⚙️ دالة الاتصال بقاعدة البيانات السحابية الحقيقية (Aiven) ---
import os

def get_db_connection():
    """
    الاتصال بقاعدة البيانات السحابية الجديدة عبر البورت العالمي المفتوح 3306
    """
    return pymysql.connect(
        host="mysql-roz.alwaysdata.net",         # 🟢 الـ Host المأخوذ من لوحة التحكم
        port=3306,                               # 🟢 البورت القياسي المفتوح دائماً أونلاين
        user="roz_admin",                        # 🔴 اسم المستخدم (المنصة تضيف اسم حسابك تلقائياً كسابقة)
        password="russell2@@3",
        database="roz_cyber_db",                 # 🔴 اسم قاعدة البيانات بعد إنشائها
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )
    
    # 🏗️ بناء الجداول ذاتياً فور نجاح العبور
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    company_id VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    company_id VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
        connection.commit()
    except Exception as e:
        pass
        
    return connection
# تهيئة متغيرات الجلسة والنظام الأمني
if "cyber_system" not in str_app.session_state:
    str_app.session_state.cyber_system = AIAdaptiveSecuritySystem()
    str_app.session_state.logs = []

system = str_app.session_state.cyber_system

# تهيئة متغيرات تسجيل الدخول والحسابات
if "logged_in" not in str_app.session_state:
    str_app.session_state.logged_in = False
if "user_role" not in str_app.session_state:
    str_app.session_state.user_role = None
if "user_data" not in str_app.session_state:
    str_app.session_state.user_data = {}


# --- 🔐 نظام تسجيل الدخول وإنشاء الحسابات المتصل بالسيرفر ---
if not str_app.session_state.logged_in:
    str_app.title("🔐 نظام تسجيل الدخول الموحد (Aiven Cloud MySQL)")
    auth_action = str_app.tabs(["تسجيل الدخول", "إنشاء حساب جديد (Sign Up)"])
    
    # ------------------ تبويب تسجيل الدخول ------------------
    with auth_action[0]:
        account_type = str_app.radio("سجل دخولك كـ:", ["شركة رئيسية (Company)", "عميل تابع لشركة (Client)"], key="login_role")
        str_app.markdown("---")
        email = str_app.text_input("البريد الإلكتروني:", key="login_email")
        password = str_app.text_input("كلمة المرور:", type="password", key="login_pass")
        login_btn = str_app.button("دخول للمنصة 🚀")
        
        if login_btn and email and password:
            try:
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    if account_type == "شركة رئيسية (Company)":
                        sql = "SELECT * FROM companies WHERE email=%s AND password=%s"
                        cursor.execute(sql, (email, password))
                        result = cursor.fetchone()
                        if result:
                            str_app.session_state.logged_in = True
                            str_app.session_state.user_role = "company"
                            str_app.session_state.user_data = {"name": result["name"], "email": result["email"], "id": result["company_id"]}
                            str_app.success(f"✔️ تم تسجيل دخول شركة {result['name']} بنجاح!")
                            time.sleep(0.5)
                            str_app.rerun()
                        else:
                            str_app.error("❌ البريد الإلكتروني أو كلمة المرور غير صحيحة.")
                    else:
                        sql = "SELECT * FROM clients WHERE email=%s AND password=%s"
                        cursor.execute(sql, (email, password))
                        result = cursor.fetchone()
                        if result:
                            str_app.session_state.logged_in = True
                            str_app.session_state.user_role = "client"
                            str_app.session_state.user_data = {"name": result["name"], "email": result["email"], "company_id": result["company_id"]}
                            str_app.success(f"✔️ مرحباً بك يا {result['name']}!")
                            time.sleep(0.5)
                            str_app.rerun()
                        else:
                            str_app.error("❌ البريد الإلكتروني أو كلمة المرور غير صحيحة.")
            except pymysql.MySQLError as e:
                str_app.error(f"❌ خطأ في الاتصال بقاعدة البيانات السحابية: {e}")
            finally:
                if 'conn' in locals(): conn.close()

    # ------------------ تبويب إنشاء حساب جديد ------------------
    with auth_action[1]:
        reg_type = str_app.radio("نوع الحساب المراد إنشاؤه:", ["شركة جديدة", "عميل جديد"], key="reg_role")
        str_app.markdown("---")
        reg_name = str_app.text_input("الاسم الكامل / اسم الشركة:", key="reg_name")
        reg_email = str_app.text_input("البريد الإلكتروني:", key="reg_email")
        reg_password = str_app.text_input("كلمة المرور:", type="password", key="reg_pass")
        
        if reg_type == "شركة جديدة":
            reg_comp_id = str_app.text_input("ابتكر رقماً تعريفياً فريداً لشركتك (مثال: COMP123):", key="reg_comp_id")
            signup_btn = str_app.button("إنشاء حساب الشركة 🏢")
            if signup_btn and reg_name and reg_email and reg_password and reg_comp_id:
                try:
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        sql = "INSERT INTO companies (company_id, name, email, password) VALUES (%s, %s, %s, %s)"
                        cursor.execute(sql, (reg_comp_id, reg_name, reg_email, reg_password))
                    conn.commit()
                    str_app.success("🎉 تم تسجيل شركتك بنجاح في السيرفر السحابي أونلاين!")
                except pymysql.MySQLError as e:
                    str_app.error(f"❌ حدث خطأ في الحفظ: {e}")
                finally:
                    if 'conn' in locals(): conn.close()
        else:
            reg_client_comp_id = str_app.text_input("أدخل الرقم التعريفي للشركة التي تتبع لها:", key="reg_client_comp_id")
            signup_btn = str_app.button("إنشاء حساب العميل 👤")
            if signup_btn and reg_name and reg_email and reg_password and reg_client_comp_id:
                try:
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT * FROM companies WHERE company_id=%s", (reg_client_comp_id,))
                        if not cursor.fetchone():
                            str_app.error("❌ الرقم التعريفي للشركة غير موجود في السيرفر السحابي!")
                        else:
                            sql = "INSERT INTO clients (name, email, password, company_id) VALUES (%s, %s, %s, %s)"
                            cursor.execute(sql, (reg_name, reg_email, reg_password, reg_client_comp_id))
                            conn.commit()
                            str_app.success("🎉 تم تسجيل حساب العميل بنجاح أونلاين!")
                except pymysql.MySQLError as e:
                    str_app.error(f"❌ حدث خطأ في الحفظ: {e}")
                finally:
                    if 'conn' in locals(): conn.close()

# --- 🖥️ عرض واجهة المنصة والأمن السيبراني بعد تسجيل الدخول الناجح ---
else:
    with str_app.sidebar:
        str_app.markdown(f"### 👤 الحساب الحالي")
        str_app.write(f"**الاسم:** {str_app.session_state.user_data['name']}")
        str_app.write(f"**النوع:** {'🏢 شركة' if str_app.session_state.user_role == 'company' else '👤 عميل'}")
        if str_app.button("تسجيل الخروج ↪️"):
            str_app.session_state.logged_in = False
            str_app.session_state.rerun()

    str_app.markdown("---")
    col1, col2 = str_app.columns([1, 1.2])

    with col1:
        str_app.header("📥 إرسال البيانات ونقلها")
        input_type = str_app.radio("اختر نوع البيانات المراد حمايتها:", ["نص مكتوب فقط", "رفع ملف (مع إمكانية إضافة نص مرافق)"])

        final_data_to_send = ""
        preview_text_content = ""
        show_image_preview = False

        if input_type == "نص مكتوب فقط":
            user_input = str_app.text_area("اكتب البيانات الحساسة المراد تشفيرها وإرسالها:", "")
            if user_input.strip(): final_data_to_send = user_input
        else:
            uploaded_file = str_app.file_uploader("اختر ملفاً من جهازك (TXT, PNG, JPG, JPEG):", type=["txt", "png", "jpg", "jpeg"])
            file_caption = str_app.text_input("أضف نصاً مرافقاً أو وصفاً للملف (اختياري):", "")

            if uploaded_file is not None:
                file_data_string = ""
                if uploaded_file.type == "text/plain":
                    preview_text_content = uploaded_file.read().decode("utf-8")
                    if preview_text_content.strip(): file_data_string = f"[محتوى الملف النصي]: {preview_text_content}"
                else:
                    file_bytes = uploaded_file.read()
                    base64_image = base64.b64encode(file_bytes).decode("utf-8")
                    file_data_string = f"[بايتات الصورة المشفرة]: {base64_image}"
                    show_image_preview = uploaded_file

                if file_caption.strip(): final_data_to_send = f"النص المرافق: {file_caption} | {file_data_string}"
                else: final_data_to_send = file_data_string

        str_app.markdown("---")
        send_normal = str_app.button("🚀 إرسال كـ (مستخدم طبيعي)")
        send_attack = str_app.button("💥 محاكاة هجوم (إرسال مكثف وسريع)")

        if send_normal and final_data_to_send:
            result = system.process_request(final_data_to_send)
            str_app.session_state.logs.append(result)
        elif send_attack and final_data_to_send:
            str_app.warning("⚡ يتم الآن شن هجوم تكرار سريع...")
            for i in range(5):
                result = system.process_request(f"{final_data_to_send[:30]}_ATTACK_PACKET_{i}")
                str_app.session_state.logs.append(result)
                time.sleep(0.05)
            str_app.success("🎯 انتهت المحاكاة!")

    with col2:
        str_app.header("👁️ لوحة المراقبة الحية والذكاء الاصطناعي")
        if str_app.session_state.logs:
            last_log = str_app.session_state.logs[-1]
            if last_log["status"] == "ATTACK":
                str_app.error("🚨 حالة النظام الحالية: تحت الهجوم (ATTACK DETECTED)")
            else:
                str_app.success("🟢 حالة النظام الحالية: آمن وطبيعي (NORMAL)")

            st_col1, st_col2 = str_app.columns(2)
            st_col1.metric("⏱️ الفارق الزمني للطلب", f"{last_log['time_diff']} ثانية")
            st_col2.metric("📊 حجم البيانات المعالجة", f"{last_log['data_size']} بايت")

            str_app.subheader("🔒 النص المشفر المار عبر الشبكة (Ciphertext):")
            str_app.code(last_log["cipher_text"], language="text")

            decrypted_output = system.decrypt_data(last_log["cipher_text"], last_log["current_key"], last_log["current_iv"], last_log["current_tag"])
            str_app.success("✅ تم فك تشفير النص بنجاح عند المستلم:")
            str_app.code(decrypted_output, language="text")
        else:
            str_app.info("قم بإرسال بيانات لبدء المراقبة الحية.")
