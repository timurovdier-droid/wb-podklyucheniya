from html import escape

from bot.config import settings

PHOTO_STEPS = [
    ("passport.jpg", "1/11 — Passport (old tarafi) rasmini jo'nating:"),
    ("license_front.jpg", "2/11 — Haydovchilik guvohnomasi (old tarafi) rasmini jo'nating:"),
    ("license_back.jpg", "3/11 — Haydovchilik guvohnomasi (orqa tarafi) rasmini jo'nating:"),
    ("tech_front.jpg", "4/11 — Texnik passport (old tarafi) rasmini jo'nating:"),
    ("tech_back.jpg", "5/11 — Texnik passport (orqa tarafi) rasmini jo'nating:"),
    ("selfie.jpg", "6/11 — Selfie rasmini jo'nating:"),
    ("taxi_license.jpg", "7/11 — Litsenziya rasmini jo'nating:"),
]

CAR_PROMPT = (
    "8-11/11 — Mashina rasmlari\n\n"
    "Mashinangizning 4 ta tomonidan rasmga olib jo'nating:\n"
    "1. Old • 2. Orqa • 3. Chap • 4. O'ng\n\n"
    "Quyida namuna. Xuddi shunday 4 ta rasm yuboring."
)

CAR_EXAMPLES = [
    ("car_front.jpg", "Namuna — old tomondan"),
    ("car_rear.jpg", "Namuna — orqa tomondan"),
    ("car_left.jpg", "Namuna — chap tomondan"),
    ("car_right.jpg", "Namuna — o'ng tomondan"),
]

BTN_APPLY = "Ulanish uchun Ariza"
BTN_BRAND = "Brend Ariza"
BTN_CONTACT = "Bog'lanish uchun"
BTN_OFFICE = "Ofis manzili"
BTN_PHONE = "Raqamni jo'natish"
BTN_CONTINUE = "Davom etish"
BTN_BACK = "⬅️ Orqaga"

MENU_BUTTONS = {BTN_APPLY, BTN_BRAND, BTN_CONTACT, BTN_OFFICE}


def contact_footer() -> str:
    lines: list[str] = []
    if settings.support_phone:
        lines.append(f"📞 {escape(settings.support_phone)}")
    if settings.operator_username:
        username = settings.operator_username.lstrip("@")
        lines.append(
            f'✈️ Telegram: <a href="https://t.me/{escape(username)}">@{escape(username)}</a>'
        )
    if not lines:
        return ""
    return "\n\nSavol bo'lsa:\n" + "\n".join(lines)


def with_contacts(text: str) -> str:
    footer = contact_footer()
    return f"{text}{footer}" if footer else text


def welcome() -> str:
    return (
        f"<b>{escape(settings.park_name)}</b>\n"
        "Haydovchilar uchun ariza markazi\n\n"
        "Ulanish yoki avtomobilni brendlash bo'yicha "
        "murojaatingizni shu yerda qoldiring.\n\n"
        "<b>1-qadam · Shaharni tanlang</b>\n"
        "Arizangiz tanlangan shahardagi operatorga yuboriladi."
    )


def city_chosen(city: str) -> str:
    return f"✅ Tanlandi: {escape(city)}"


def menu_intro(city: str) -> str:
    return (
        f"📍 <b>{escape(city)}</b>\n\n"
        "Arizangiz tanlangan shahardagi operatorlarga yuboriladi.\n\n"
        "🟣 <b>Ulanish uchun ariza</b> — haydovchi sifatida ro'yxatdan o'tish.\n"
        "🎨 <b>Brend ariza</b> — avtomobilni brendlash uchun murojaat.\n"
        "📞 Aloqa ma'lumotlari va 📍 ofis manzili ham quyidagi menyuda.\n\n"
        "Kerakli bo'limni tanlang:"
    )


def apply_phone(city: str) -> str:
    return (
        f"📄 <b>{escape(city)} — haydovchilik arizasi</b>\n\n"
        "Ism va familiyangiz pravangizdan olinadi.\n\n"
        "Telefon raqamni yuborish:\n"
        "• pastdagi <b>Raqamni jo'natish</b> tugmasi, yoki\n"
        "• raqamni <b>qo'lda yozing</b> (masalan: +998901112233 yoki 901112233)"
    )


def apply_phone_again() -> str:
    return (
        "Telefon noto'g'ri. Tugma orqali yuboring yoki "
        "raqamni yozing (masalan: +998901112233)."
    )


def apply_warning() -> str:
    return (
        "⚠️ <b>Diqqat!</b>\n\n"
        "Endi sizdan hujjatlaringizning <b>originalini rasmga olib</b> jo'natishingiz so'raladi.\n\n"
        "❌ Soliqdan olingan skrinshot <b>QABUL QILINMAYDI!</b>\n\n"
        "Hujjatlardagi ma'lumotlar arizani ko'rib chiqish uchun operatorlarga yuboriladi. "
        "Davom etish orqali ushbu yuborishga rozilik bildirasiz."
    )


def need_photo() -> str:
    return "Iltimos, hujjatning rasmini yuboring. Fayl yoki matn qabul qilinmaydi."


def cars_progress(count: int) -> str:
    return f"{count}/4 qabul qilindi. Yana {4 - count} ta rasm yuboring: old, orqa, chap, o'ng."


def cars_need_four() -> str:
    return "Iltimos, aynan 4 ta rasm yuboring: 1. Old • 2. Orqa • 3. Chap • 4. O'ng."


def cars_ok() -> str:
    return "✅ 4 ta rasm qabul qilindi!"


def ask_plate() -> str:
    return "Endi mashinangizning <b>davlat raqamini</b> yozing (masalan: 01A123BC):"


def plate_again() -> str:
    return "Davlat raqamini lotin harflari va raqamlar bilan yozing. Masalan: 01A123BC."


def sending() -> str:
    return "⏳ Arizangiz operatorga yuborilmoqda."


def accepted_apply(code: str, city: str) -> str:
    phone = f"\n\nAloqa: {escape(settings.support_phone)}" if settings.support_phone else ""
    return (
        "✅ <b>Arizangiz qabul qilindi</b>\n\n"
        f"Ariza kodi: <code>{escape(code)}</code>\n"
        f"Hudud: {escape(city)}\n\n"
        "Hujjatlaringiz operatorga yuborildi. Natija yoki qo'shimcha ma'lumot kerak bo'lsa, "
        f"shu bot orqali xabar beramiz.{phone}"
    )


def accepted_brand(code: str, city: str) -> str:
    return (
        f"Ariza kodi: <code>{escape(code)}</code>\n"
        "✅ <b>Arizangiz qabul qilindi</b>\n\n"
        f"{escape(city)} — Brend arizangiz qabul qilindi. Tez orada operatorlarimiz bog'lanadi."
    )


def send_failed() -> str:
    return (
        "Ariza saqlandi, lekin operatorga yuborishda xatolik yuz berdi. "
        "Birozdan so'ng /start orqali qayta yuboring."
    )


def brand_rules(city: str) -> str:
    return (
        f"📍 <b>{escape(city)} — Brend arizasi</b>\n\n"
        "⚠️ <b>DIQQAT! BRENDLASH SHARTLARI:</b>\n\n"
        "❌ SPARK — brendlanmaydi\n"
        "❌ NEXIA 3 — brendlanmaydi\n"
        "❌ Yili 2015 va undan past mashinalar — brendlanmaydi\n"
        "✅ Boshqa mashinalar (yili 2016 va undan yuqori) — brendlanadi\n\n"
        "<i>SPARK va NEXIA 3 yili nechi bo'lishidan qat'i nazar BREND qilinmaydi. "
        "2016 dan past mashinalar ham brend qilinmaydi.</i>\n\n"
        "Davom etish uchun pastdagi knopkani bosing."
    )


def brand_rejected_rules() -> str:
    return (
        "❌ Bu mashina brendlash talablariga mos kelmaydi.\n\n"
        "SPARK va NEXIA 3 brendlanmaydi. 2015 va undan past mashinalar ham brendlanmaydi.\n"
        "Boshqa model yoki 2016 va undan yuqori yilni yozing. Chiqish uchun /start."
    )


def brand_ask_name(city: str) -> str:
    return f"📍 <b>{escape(city)} — Brend arizasi</b>\n\nIltimos, <b>ism va familiyangizni</b> yozing:"


def brand_name_again() -> str:
    return "❗ Iltimos, to'liq ism familiyangizni yozing:"


def brand_ask_phone(city: str) -> str:
    return f"📍 <b>{escape(city)} — Brend</b>\n\n📞 Telefon raqamingizni jo'nating:"


def brand_phone_again() -> str:
    return "Telefon raqamini to'liq yozing. Masalan: +998901234567."


def brand_ask_model(city: str) -> str:
    return f"📍 <b>{escape(city)} — Brend</b>\n\n🚗 Mashinangizning rusumi (modelini) yozing:"


def brand_ask_year(city: str) -> str:
    return f"📍 <b>{escape(city)} — Brend</b>\n\n📅 Mashinangizning yilini yozing:"


def brand_year_again() -> str:
    return "Yilni 4 ta raqam bilan yozing. Masalan: 2023."


def brand_ask_color(city: str) -> str:
    return f"📍 <b>{escape(city)} — Brend</b>\n\n🎨 Mashinangizning rangini yozing:"


def brand_color_again() -> str:
    return "Rangni so'z bilan yozing. Masalan: oq."


def brand_ask_plate(city: str) -> str:
    return f"📍 <b>{escape(city)} — Brend</b>\n\n🔢 Mashinangizning davlat raqamini yozing:"


def office_text(city: str) -> str:
    return (
        f"📍 <b>{escape(city)} — ofis manzili</b>\n\n"
        f"Manzil — {escape(settings.office_address)}\n\n"
        f"Mo'ljal: {escape(settings.office_landmark)}\n\n"
        "👇 Manzilni ko'rish uchun «Xaritada ochish» tugmasini bosing."
        f"{contact_footer()}"
    )


def contacts_text(city: str) -> str:
    lines = [f"<b>{escape(city)} — bog'lanish</b>"]
    if settings.support_phone:
        lines.append(f"\n📞 Aloqa: {escape(settings.support_phone)}")
    if settings.operator_username:
        username = settings.operator_username
        if not username.startswith("@"):
            username = f"@{username}"
        lines.append(f"\n✈️ Telegram: {escape(username)}")
    if settings.channel_url:
        lines.append(f"\n📣 Telegram kanal: {escape(settings.channel_url)}")
    if settings.instagram:
        lines.append(f"\n📸 Instagram: {escape(settings.instagram)}")
    if len(lines) == 1:
        lines.append("\nAloqa ma'lumotlari hali kiritilmagan.")
    return "".join(lines)


def coming_soon() -> str:
    return "Bu bo'lim tez orada ishga tushadi. Kerakli bo'limni menyudan tanlang."


def choose_city() -> str:
    return "Avval shaharni tanlang."


def incomplete_docs_notice(code: str) -> str:
    phone = settings.support_phone
    contact = (
        f"\n\nSavollar bo'lsa: {escape(phone)}"
        if phone
        else ""
    )
    return (
        f"📷 Ariza <code>{escape(code)}</code>\n\n"
        "Barcha talab qilinadigan hujjatlar yoki rasmlar to'liq emas yoki sifati yomon.\n\n"
        "Iltimos, nimalarni o'tkazib yuborganingizni ko'rib chiqing va "
        "arizani <b>qaytadan</b> to'ldiring:\n"
        "menyu → «Ulanish uchun Ariza»."
        f"{contact}"
    )


def status_notice(kind: str, status: str, code: str) -> str:
    phone = settings.support_phone
    if kind == "brend" and status == "rejected":
        contact = f"\n\nSavollar bo'lsa, {escape(phone)} raqamiga murojaat qiling." if phone else ""
        return (
            f"Ariza <code>{escape(code)}</code>\n\n"
            "Arizangiz ko'rib chiqildi. Afsuski, avtomobilingiz yoki yuborgan "
            "ma'lumotlaringiz brendlash talablariga mos kelmagani uchun arizangiz tasdiqlanmadi."
            f"{contact}"
        )
    titles = {
        ("ulanish", "contacted"): "Operatorimiz siz bilan bog'lanadi.",
        ("ulanish", "connected"): (
            "✅ <b>Arizangiz ishlovga olindi</b>\n\n"
            "Operatorlar arizangizni qabul qilishdi va ishga olishdi. "
            "Hozir arizangiz ko'rib chiqilmoqda. Tez orada siz bilan bog'lanishadi."
        ),
        ("ulanish", "rejected"): "Arizangiz ko'rib chiqildi. Afsuski, arizangiz tasdiqlanmadi.",
        ("brend", "contacted"): "Operatorimiz brend arizangiz bo'yicha siz bilan bog'lanadi.",
        ("brend", "connected"): (
            "✅ <b>Arizangiz ishlovga olindi</b>\n\n"
            "Brend arizangiz qabul qilindi va ishga olindi. "
            "Tez orada operatorlar siz bilan bog'lanishadi."
        ),
    }
    body = titles.get((kind, status), "Ariza holati yangilandi.")
    extra = ""
    if status == "rejected" and phone:
        extra = f"\n\nSavollar bo'lsa, {escape(phone)} raqamiga murojaat qiling."
    text = f"Ariza <code>{escape(code)}</code>\n\n{body}{extra}"
    if status == "connected":
        return with_contacts(text)
    return text


STATUS_LABELS = {
    "new": "Новая",
    "contacted": "На связи",
    "connected": "Подключён",
    "incomplete": "Chala rasm",
    "rejected": "Отклонён",
}

OCR_MISSING = "⚠️ Aniqlanmadi — tekshiring"


def _ocr_field(ocr: dict | None, key: str) -> str:
    if not ocr:
        return OCR_MISSING
    value = str(ocr.get(key) or "").strip()
    return value if value else OCR_MISSING


def _phone_display(phone: str | None) -> str:
    raw = (phone or "").strip()
    digits = "".join(ch for ch in raw if ch.isdigit())
    return digits or raw or OCR_MISSING


def admin_card_ulanish(app: dict) -> str:
    ocr = app.get("extracted") if isinstance(app.get("extracted"), dict) else {}
    username = f"@{escape(app['username'])}" if app.get("username") else "—"
    plate = (app.get("plate") or "").strip()
    auto = plate or str(ocr.get("avtomobil_raqam") or "").strip()
    auto_line = escape(auto) if auto else escape(_ocr_field(ocr, "avtomobil_raqam"))
    lines = [
        f"<b>{escape(settings.park_name)} · HAYDOVCHI ARIZASI</b>",
        f"Ariza: <code>{escape(app['code'])}</code> · {escape(app.get('city') or '')}",
        f"Arizachi: {username}",
    ]
    if app.get("status") == "contacted":
        lines.append("🟡 <b>Jarayonda</b> — boshqa operator bog'lanmoqda")
    lines.extend(
        [
        "",
        f"Familiya: {escape(_ocr_field(ocr, 'familiya'))}",
        f"Ism: {escape(_ocr_field(ocr, 'ism'))}",
        f"Tug'ilgan sana: {escape(_ocr_field(ocr, 'tugilgan_sana'))}",
        f"Telefon raqami: {escape(_phone_display(app.get('phone')))}",
        f"PINFL: {escape(_ocr_field(ocr, 'pinfl'))}",
        f"Tug'ilgan joy: {escape(_ocr_field(ocr, 'tugilgan_joy'))}",
        f"Prava raqami: {escape(_ocr_field(ocr, 'prava_raqam'))}",
        f"Amal qilish muddati: {escape(_ocr_field(ocr, 'prava_amal_muddati'))}",
        f"Avtomobil raqami: {auto_line}",
        f"Texpasport seriya raqami: {escape(_ocr_field(ocr, 'texpasport_seriya_raqam'))}",
        "",
        "<i>OCR natijasini hujjat bilan solishtiring.</i>",
        "",
        "Operator boshqaruvi. Quyidagi amallardan birini tanlang.",
        ]
    )
    note = str(ocr.get("eslatma") or "").strip()
    if note:
        lines.insert(-2, f"Eslatma: {escape(note)}")
    return "\n".join(lines)


def admin_card(app: dict) -> str:
    if app.get("kind") == "ulanish" and settings.gemini_api_key:
        return admin_card_ulanish(app)
    username = f"@{escape(app['username'])}" if app.get("username") else "—"
    driver = f'<a href="tg://user?id={app["user_id"]}">profil</a>'
    status = STATUS_LABELS.get(app["status"], app["status"])
    lines = [
        f"<b>{'Ulanish' if app['kind'] == 'ulanish' else 'Brend'}</b> <code>{escape(app['code'])}</code>",
        f"Holat: {escape(status)}",
        "",
        f"Shahar: {escape(app['city'])}",
        f"Telefon: {escape(app['phone'])}",
    ]
    if app["kind"] == "brend":
        lines.extend(
            [
                f"FIO: {escape(app['full_name'])}",
                f"Model: {escape(app.get('car_model') or '')}",
                f"Yil: {escape(app.get('car_year') or '')}",
                f"Rang: {escape(app.get('car_color') or '')}",
            ]
        )
    else:
        lines.append(f"Ism: {escape(app.get('full_name') or '—')}")
    lines.extend(
        [
            f"Username: {username}",
            f"Davlat raqami: {escape(app.get('plate') or '')}",
            f"Haydovchi: {driver}",
        ]
    )
    return "\n".join(lines)
