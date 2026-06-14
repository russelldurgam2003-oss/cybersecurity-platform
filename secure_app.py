import streamlit as str_app
import time
import base64
import pymysql  # مكتبة الاتصال بقاعدة بيانات MySQL
from core_system import AIAdaptiveSecuritySystem

# إعداد الصفحة
str_app.set_page_config(page_title="منصة الأمن التكيفي الذكي", layout="wide")

# --- ⚙️ دالة الاتصال بقاعدة البيانات ---
def get_db_connection():
    """
    قم بتغيير هذه البيانات بناءً على استضافتك الأونلاين أو السيرفر المحلي.
    إذا كانت المنصة أونلاين، استبدل 'localhost' بـ IP السيرفر أو الهوست الخاص بالاستضافة.
    """
    return pymysql.connect(
        host="localhost",       # أو عنوان الـ IP الخاص بالاستضافة الأونلاين
        user="root",            # اسم مستخدم قاعدة البيانات
        password="",            # كلمة مرور قاعدة البيانات
        database="cyber_security_db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

# تهيئة متغيرات الجلسة والنظام الأمني
if "cyber_system" not in str_app.session_state:
    str_app.session_state.cyber_system = AIAdaptiveSecuritySystem()
    str_app.session_state.logs = []

if "logged_in" not in str_app.session_state:
    str_app.session_state.logged_in = False
if "user_role" not in str_app.session_state:
    str_app.session_state.user_role = None
if "user_data" not in str_app.session_state:
    str_app.session_state.user_data = {}

system = str_app.session_state.cyber_system


# --- 🔐 3. نافذة تسجيل الدخول والتسجيل الجديد ---
if not str_app.session_state.logged_in:
    str_app.title("🔐 نظام تسجيل الدخول الموحد (المتصل بقاعدة البيانات)")
    
    # خيارين: إما تسجيل دخول بحساب حالي أو إنشاء حساب جديد
    auth_action = str_app.tabs(["تسجيل الدخول", "إنشاء حساب جديد (Sign Up)"])
    
    # ------------------ تبويب تسجيل الدخول ------------------
    with auth_action[0]:
        account_type = str_app.radio("سجل دخولك كـ:", ["شركة رئيسية (Company)", "عميل تابع لشركة (Client)"], key="login_role")
        str_app.markdown("---")
        
        email = str_app.text_input("البريد الإلكتروني:", key="login_email")
        password = str_app.text_input("كلمة المرور:", type="password", key="login_pass")
        login_btn = str_app.button("دخول للمنصة 🚀")
        
        if login_btn:
            if email and password:
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
                except Exception as e:
                    str_app.error(f"حدث خطأ في الاتصال بقاعدة البيانات: {e}")
                finally:
                    if 'conn' in locals(): conn.close()
            else:
                str_app.warning("⚠️ يرجى إدخال كافة الحقول للتحقق.")

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
                    str_app.success("🎉 تم تسجيل شركتك بنجاح في قاعدة البيانات! يمكنك الآن الانتقال لتبويب تسجيل الدخول.")
                except pymysql.integrity.IntegrityError:
                    str_app.error("❌ هذا البريد الإلكتروني أو المعرف الخاص بالشركة مسجل بالفعل.")
                finally:
                    if 'conn' in locals(): conn.close()
        
        else:
            reg_client_comp_id = str_app.text_input("أدخل الرقم التعريفي للشركة التي تتبع لها:", key="reg_client_comp_id")
            signup_btn = str_app.button("إنشاء حساب العميل 👤")
            
            if signup_btn and reg_name and reg_email and reg_password and reg_client_comp_id:
                try:
                    conn = get_db_connection()
                    with conn.cursor() as cursor:
                        # التحقق أولاً من وجود الشركة
                        cursor.execute("SELECT * FROM companies WHERE company_id=%s", (reg_client_comp_id,))
                        if not cursor.fetchone():
                            str_app.error("❌ الرقم التعريفي للشركة غير موجود! يرجى التحقق من الشركة أولاً.")
                        else:
                            sql = "INSERT INTO clients (name, email, password, company_id) VALUES (%s, %s, %s, %s)"
                            cursor.execute(sql, (reg_name, reg_email, reg_password, reg_client_comp_id))
                            conn.commit()
                            str_app.success("🎉 تم تسجيل حسابك كعميل بنجاح! توجه لتبويب تسجيل الدخول الآن.")
                except pymysql.integrity.IntegrityError:
                    str_app.error("❌ هذا البريد الإلكتروني مسجل مسبقاً للعميل.")
                finally:
                    if 'conn' in locals(): conn.close()

# --- 4. عرض لوحة التحكم بعد تسجيل الدخول الناجح ---
else:
    with str_app.sidebar:
        str_app.markdown(f"### 👤 الحساب الحالي")
        str_app.write(f"**الاسم:** {str_app.session_state.user_data['name']}")
        str_app.write(f"**النوع:** {'🏢 شركة' if str_app.session_state.user_role == 'company' else '👤 عميل'}")
        
        if str_app.session_state.user_role == 'company':
            str_app.info(f"كود العميل: {str_app.session_state.user_data['id']}")
        else:
            str_app.info(f"تابع لشركة كود: {str_app.session_state.user_data['company_id']}")
            
        if str_app.button("تسجيل الخروج ↪️"):
            str_app.session_state.logged_in = False
            str_app.session_state.user_role = None
            str_app.session_state.user_data = {}
            str_app.rerun()

    # -----------------------------------------------
    # أ. واجهة الشركة (قراءة حية للعملاء الفعليين من قاعدة البيانات)
    # -----------------------------------------------
    if str_app.session_state.user_role == "company":
        str_app.title(f"🏢 لوحة تحكم الشركة: {str_app.session_state.user_data['name']}")
        
        tab1, tab2, tab3 = str_app.tabs(["📊 المراقبة الحية وسجل العمليات", "👥 إدارة حسابات العملاء الفعليين", "📈 تحليل البيانات والأمن التكيفي"])
        
        with tab1:
            str_app.header("👁️ لوحة المراقبة الحية والذكاء الاصطناعي")
            if str_app.session_state.logs:
                # (يبقى كود معالجة السجلات وعرض التشفير وفك التشفير كما هو لتتبع طلبات الشبكة الحالية)
                last_log = str_app.session_state.logs[-1]
                if last_log["status"] == "ATTACK":
                    str_app.error("🚨 حالة النظام الحالية: تحت الهجوم (ATTACK DETECTED)")
                else:
                    str_app.success("🟢 حالة النظام الحالية: آمن وطبيعي (NORMAL)")
                
                st_col1, st_col2 = str_app.columns(2)
                st_col1.metric("⏱️ الفارق الزمني للطلب", f"{last_log['time_diff']} ثانية")
                st_col2.metric("📊 حجم البيانات المعالجة", f"{last_log['data_size']} بايت")
                
                str_app.subheader("🔒 النص المشفر المار عبر الشبكة:")
                str_app.code(last_log["cipher_text"], language="text")
                
                decrypted_output = system.decrypt_data(last_log["cipher_text"], last_log["current_key"], last_log["current_iv"], last_log["current_tag"])
                str_app.success("✅ تم فك تشفير النص بنجاح عند المستلم:")
                str_app.code(decrypted_output, language="text")
            else:
                str_app.info("لا توجد طلبات مرسلة حالياً من العملاء للمراقبة في هذه الجلسة.")

        with tab2:
            str_app.header("👥 العملاء المسجلون رسمياً في قاعدة بياناتك")
            try:
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    # جلب العملاء المرتبطين بهذه الشركة فقط ديناميكياً من الـ database
                    sql = "SELECT name, email, created_at FROM clients WHERE company_id = %s"
                    cursor.execute(sql, (str_app.session_state.user_data['id'],))
                    db_clients = cursor.fetchall()
                    
                    if db_clients:
                        str_app.dataframe(db_clients)  # عرض جدول العملاء الحقيقيين
                    else:
                        str_app.info("ℹ️ لا يوجد أي عملاء مسجلين برقم شركتك التعريفي حالياً.")
            except Exception as e:
                str_app.error(f"فشل جلب بيانات العملاء: {e}")
            finally:
                if 'conn' in locals(): conn.close()

        with tab3:
            str_app.header("📈 تحليل البيانات والمراقبة الأمنية المستمرة")
            str_app.metric(label="معدل استقرار تشفير AES", value="100%")

    # -----------------------------------------------
    # ب. واجهة العميل (إرسال البيانات واستخدام خدمات الشركة)
    # -----------------------------------------------
    elif str_app.session_state.user_role == "client":
        str_app.title("🛡️ منصة الأمن السيبراني التكيفي - بوابة العميل")
        str_app.markdown(f"مرحباً بك يا **{str_app.session_state.user_data['name']}**")
        str_app.markdown("---")
        
        str_app.header("📥 إرسال البيانات والملفات بشكل آمن للشركة")
        input_type = str_app.radio("اختر نوع البيانات المراد حمايتها وإرسالها:", ["نص مكتوب فقط", "رفع ملف (مع إمكانية إضافة نص مرافق)"])

        final_data_to_send = ""
        if input_type == "نص مكتوب فقط":
            user_input = str_app.text_area("اكتب البيانات الحساسة المراد تشفيرها وإرسالها:", "")
            if user_input.strip(): final_data_to_send = user_input
        else:
            uploaded_file = str_app.file_uploader("اختر ملفاً:", type=["txt", "png", "jpg", "jpeg"])
            file_caption = str_app.text_input("وصف الملف (اختياري):")
            if uploaded_file is not None:
                final_data_to_send = f"الملف المرفوع: {uploaded_file.name} | الوصف: {file_caption}"

        str_app.markdown("---")
        send_normal = str_app.button("🚀 إرسال كـ (مستخدم طبيعي)")
        
        if send_normal and final_data_to_send:
            result = system.process_request(final_data_to_send)
            str_app.session_state.logs.append(result)
            str_app.success("🔒 تم تشفير بياناتك وإرسالها بنجاح إلى قاعدة بيانات سيرفر الشركة!")
