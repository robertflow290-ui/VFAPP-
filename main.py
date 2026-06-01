import flet as ft
import requests
import json
import threading

# --- الإعدادات وقائمة الباقات ---
TELEGRAM_BOT_TOKEN = "6456889199:AAHH17nKbXpfvXsjRu1_NENDZ8_7faBxBU8"
TELEGRAM_CHAT_ID = "6474888099"
ADMIN_WALLET_NUMBER = "01000000000" # ⚠️ غير الرقم ده برقم محفظتك اللي العميل هيحولك عليه كاش

# رابط قاعدة بيانات Firebase الخاصة بك
FIREBASE_URL = "https://cash-90eee-default-rtdb.firebaseio.com/"

ALL_PRODUCTS = [
    ("فكة 2.5 جنيه", "Fakka_2.5_Unite"), ("فكة 4.25 جنيه", "Fakka_4.25_Unite"),
    ("فكة 5 جنيه", "Fakka_5_Unite"), ("فكة 6 جنيه", "Fakka_6_NewUnite"),
    ("فكة 7 جنيه", "Fakka_7_Unite"), ("فكة 9 جنيه", "Fakka_9_Unite"),
    ("فكة 10 جنيه", "Fakka_10_Unite"), ("فكة 10 جنيه (new)", "Fakka_10_NewUnite"),
    ("فكة 10.5 جنيه", "Fakka_10.5_Unite"), ("فكة 11.5 جنيه", "Fakka_11.5_Unite"),
    ("فكة 12 جنيه", "Fakka_12_Unite"), ("فكة 12.5 جنيه", "Fakka_12.5_Unite"),
    ("فكة 13 جنيه", "Fakka_13_Unite"), ("فكة 13.5 جنيه", "Fakka_13.5_Unite"),
    ("فكة 15 جنيه", "Fakka_15_Unite"), ("فكة 15 جنيه (new)", "Fakka_15_NewUnite"),
    ("فكة 15.5 جنيه", "Fakka_15.5_Unite"), ("فكة 16.5 جنيه", "Fakka_16.5_Unite"),
    ("فكة 17.5 جنيه", "Fakka_17.5_Unite"), ("فكة 19.5 جنيه", "Fakka_19.5_NewUnite"),
    ("فكة 20 جنيه", "Fakka_20_Unite"), ("فكة 26 جنيه", "Fakka_26_Unite"),
    ("مارد 10 دقايق", "Mared_10_Minuts"), ("مارد 10 فليكس", "Mared_10_Flexs"),
    ("مارد 10 سوشيال", "Mared_10_Social")
]

def main(page: ft.Page):
    page.title = "تطبيق شحن فودافون"
    page.rtl = True
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 400
    page.window_height = 700

    user_state = {
        "msisdn": "",
        "seamless_token": "",
        "access_token": "",
        "points": 0
    }

    # --- واجهة المستخدم ---
    info_text = ft.Text("جاري التعرف على الرقم بالداتا...", weight=ft.FontWeight.BOLD)
    points_text = ft.Text("النقاط: --", color=ft.colors.GREEN, weight=ft.FontWeight.BOLD)
    top_bar = ft.Row([info_text, points_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    
    loading_ring = ft.ProgressRing(visible=True)
    
    product_dropdown = ft.Dropdown(
        label="اختر الكارت",
        options=[ft.dropdown.Option(text=name, key=prod_id) for name, prod_id in ALL_PRODUCTS],
        width=300, visible=False
    )
    receiver_input = ft.TextField(label="الرقم المراد الشحن له", width=300, visible=False, keyboard_type=ft.KeyboardType.PHONE)
    pin_input = ft.TextField(label="الرقم السري للمحفظة", password=True, can_reveal_password=True, width=300, visible=False, keyboard_type=ft.KeyboardType.NUMBER)
    
    result_text = ft.Text("", text_align=ft.TextAlign.CENTER)

    # --- التعامل مع Firebase ---
    def get_or_create_user_points(msisdn):
        try:
            url = f"{FIREBASE_URL}users/{msisdn}.json"
            res = requests.get(url)
            data = res.json()
            if data is not None and "points" in data:
                return data["points"]
            else:
                requests.put(url, json={"points": 0})
                return 0
        except:
            return 0

    def update_firebase_points(msisdn, new_points):
        try:
            url = f"{FIREBASE_URL}users/{msisdn}.json"
            requests.patch(url, json={"points": new_points})
            return True
        except:
            return False

    def sync_ui_points():
        points_text.value = f"النقاط: {user_state['points']}"
        page.update()

    # --- الدوال الفرعية للأزرار ---
    def send_telegram_deposit(sender_phone, points_count):
        text = f"🚨 *طلب إيداع جديد*\n\n📱 *رقم العميل:* `0{user_state['msisdn']}`\n💸 *رقم المرسل:* `{sender_phone}`\n🔢 *النقاط المطلوبة:* {points_count}\n\nتفعيل النقاط تلقائياً ارسل للبوت:\n/add\_points\_0{user_state['msisdn']}\_{points_count}"
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload)
            return True
        except:
            return False

    def on_deposit_click(e):
        sender_input = ft.TextField(label="رقم الكاش المحول منه")
        points_input = ft.TextField(label="عدد النقاط المطلوبة", keyboard_type=ft.KeyboardType.NUMBER)
        
        def confirm_deposit(e):
            if not sender_input.value or not points_input.value: return
            success = send_telegram_deposit(sender_input.value, points_input.value)
            deposit_dialog.open = False
            page.snack_bar = ft.SnackBar(ft.Text("تم إرسال طلبك بنجاح وجاري المراجعة!" if success else "خطأ في الاتصال"))
            page.snack_bar.open = True
            page.update()

        deposit_dialog = ft.AlertDialog(
            title=ft.Text("طلب شحن نقاط"),
            content=ft.Column([
                ft.Text(f"يرجى تحويل قيمة النقاط إلى فودافون كاش:\n{ADMIN_WALLET_NUMBER}"),
                points_input, sender_input
            ], height=180),
            actions=[
                ft.TextButton("تأكيد الإرسال", on_click=confirm_deposit),
                ft.TextButton("إلغاء", on_click=lambda e: setattr(deposit_dialog, 'open', False) or page.update())
            ]
        )
        page.dialog = deposit_dialog
        deposit_dialog.open = True
        page.update()

    deposit_btn = ft.ElevatedButton("طلب إيداع نقاط", icon=ft.icons.ACCOUNT_BALANCE_WALLET, on_click=on_deposit_click, visible=False)

    def login_seamless():
        try:
            url_seamless = "http://mobile.vodafone.com.eg/checkSeamless/realms/vf-realm/protocol/openid-connect/auth?client_id=ana-vodafone-app-seamless"
            headers_seamless = {
                'User-Agent': "okhttp/4.11.0", 'clientId': "AnaVodafoneAndroid", 'Accept-Language': "ar"
            }
            res = requests.get(url_seamless, headers=headers_seamless, timeout=10)
            data = res.json()
            
            if data.get('seamlessToken'):
                user_state["seamless_token"] = data.get('seamlessToken')
                user_state["msisdn"] = str(data.get('msisdn'))
                
                user_state["points"] = get_or_create_user_points(user_state["msisdn"])
                
                info_text.value = f"أهلاً، 0{user_state['msisdn']}"
                loading_ring.visible = False
                product_dropdown.visible = True
                receiver_input.visible = True
                pin_input.visible = True
                charge_btn.visible = True
                deposit_btn.visible = True
                sync_ui_points()
                
                url_token = "https://mobile.vodafone.com.eg/auth/realms/vf-realm/protocol/openid-connect/token"
                payload_token = {'grant_type': "password", 'client_secret': "b86e30a8-ae29-467a-a71f-65c73f2ff5e3", 'client_id': "cash-app"}
                headers_token = {'User-Agent': "okhttp/4.11.0", 'silentLogin': "true", 'seamlessToken': user_state["seamless_token"], 'clientId': "AnaVodafoneAndroid", 'Accept-Language': "ar"}
                token_res = requests.post(url_token, data=payload_token, headers=headers_token)
                user_state["access_token"] = token_res.json().get('access_token')
            else:
                raise Exception()
        except:
            loading_ring.visible = False
            info_text.value = "يرجى تشغيل داتا فودافون وإعادة فتح التطبيق."
            page.update()

    def do_charge(e):
        user_state["points"] = get_or_create_user_points(user_state["msisdn"])
        sync_ui_points()

        if user_state["points"] < 1:
            result_text.value = "❌ نقاطك غير كافية، يرجى طلب إيداع أولاً."
            result_text.color = ft.colors.RED
            page.update()
            return
            
        if not product_dropdown.value or len(receiver_input.value) != 11 or not pin_input.value:
            result_text.value = "❌ تأكد من تعبئة البيانات بالكامل بشكل صحيح."
            result_text.color = ft.colors.RED
            page.update()
            return

        result_text.value = "⏳ جاري تنفيذ عملية الشحن..."
        result_text.color = ft.colors.BLUE
        page.update()

        def api_call():
            try:
                url_order = "https://mobile.vodafone.com.eg/services/dxl/pom/productOrder"
                payload = {
                    "channel": {"name": "MobileApp"},
                    "orderItem": [{"action": "insert", "id": product_dropdown.value, 
                                   "product": {"characteristic": [{"name": "PaymentMethod", "value": "VFCash"}, {"name": "USE_EMONEY", "value": "False"}], 
                                               "id": product_dropdown.value, "relatedParty": [{"id": user_state["msisdn"], "name": "MSISDN", "role": "Subscriber"}, {"id": receiver_input.value, "name": "Receiver", "role": "Receiver"}]}, 
                                   "@type": product_dropdown.value, "eCode": 0}],
                    "relatedParty": [{"id": pin_input.value, "name": "pin", "role": "Requestor"}],
                    "@type": "CashFakkaAndMared"
                }
                headers = {
                    'User-Agent': "okhttp/4.11.0", 'Content-Type': "application/json", 'api-host': "ProductOrderingManagement",
                    'useCase': "CashFakkaAndMared", 'api-version': "v2", 'msisdn': f"0{user_state['msisdn']}",
                    'Authorization': f"Bearer {user_state['access_token']}", 'Accept-Language': "ar", 'clientId': "AnaVodafoneAndroid"
                }
                
                res = requests.post(url_order, json=payload, headers=headers)
                data = res.json()
                
                if data.get('state') == 'Completed' or data.get('complete'):
                    new_pts = user_state["points"] - 1
                    update_firebase_points(user_state["msisdn"], new_pts)
                    user_state["points"] = new_pts
                    sync_ui_points()
                    result_text.value = "✅ تم شحن الكارت بنجاح وخصم 1 نقطة!"
                    result_text.color = ft.colors.GREEN
                else:
                    result_text.value = "❌ فشل: رصيد الكاش غير كافٍ أو الرقم السري خطأ."
                    result_text.color = ft.colors.RED
            except:
                result_text.value = "❌ حدث خطأ غير متوقع أثناء الشحن."
                result_text.color = ft.colors.RED
            page.update()

        threading.Thread(target=api_call).start()

    charge_btn = ft.ElevatedButton("شحن الكارت الان", icon=ft.icons.BOLT, on_click=do_charge, visible=False, width=300)

    page.add(
        ft.Container(
            content=ft.Column([
                top_bar, ft.Divider(), deposit_btn,
                ft.Column([loading_ring], alignment=ft.MainAxisAlignment.CENTER),
                product_dropdown, receiver_input, pin_input, charge_btn, result_text
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20
        )
    )

    threading.Thread(target=login_seamless).start()

ft.app(target=main)

