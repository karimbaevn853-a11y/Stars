import os
import telebot
from telebot import types

BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
ADMIN_ID_RAW = (os.getenv("ADMIN_ID") or "0").strip()
CHANNEL_URL = (os.getenv("CHANNEL_URL") or "https://t.me/NFT_SAVDOSI_CHATI").strip()
CHANNEL_USERNAME = (os.getenv("CHANNEL_USERNAME") or "@NFT_SAVDOSI_CHATI").strip()
REQUIRED_INVITES = int((os.getenv("REQUIRED_INVITES") or "30").strip())
REWARD_STARS = int((os.getenv("REWARD_STARS") or "500").strip())

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi! Render Environment Variables ni tekshiring.")

ADMIN_ID = int(ADMIN_ID_RAW)

bot = telebot.TeleBot(BOT_TOKEN)

users = {}
waiting_for_username = set()


def is_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return True


def get_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "invites": 0,
            "username_submitted": None,
            "status": "none",
        }
    return users[user_id]


@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.from_user.id
    u = get_user(user_id)

    parts = message.text.split()
    if len(parts) > 1 and parts[1].isdigit():
        inviter_id = int(parts[1])
        if inviter_id != user_id and u["status"] == "none":
            inviter = get_user(inviter_id)
            inviter["invites"] += 1
            try:
                bot.send_message(
                    inviter_id,
                    f"🎉 Sizning havolangiz orqali yangi odam kirdi!\n"
                    f"Jami chaqirilganlar: {inviter['invites']}/{REQUIRED_INVITES} ta"
                )
            except Exception:
                pass

    bot_username = bot.get_me().username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📢 Kanalga kirish", url=CHANNEL_URL),
        types.InlineKeyboardButton("✍️ 30 ta odam to'ldirdim (User yozish)", callback_data="send_user"),
        types.InlineKeyboardButton("📊 Mening hisobim", callback_data="my_stats"),
    )

    text = (
        "Salom! Bepul Stars botga xush kelibsiz! ⭐\n\n"
        f"👉 <a href='{CHANNEL_URL}'>NFT_SAVDOSI_CHATI</a> kanaliga <b>{REQUIRED_INVITES} ta odam</b> chaqirsangiz, "
        f"sizga <b>{REWARD_STARS} Stars</b> beriladi!\n\n"
        f"🔗 Sizning shaxsiy taklif havolangiz:\n<code>{ref_link}</code>\n\n"
        f"📌 Shart: {REQUIRED_INVITES} ta odamni to'ldirsangiz beriladi, to'ldirmasangiz berilmaydi. "
        "Odamlar sonini to'ldirganlar o'z <b>@username</b> ingizni yozib qoldiring — admin siz bilan bog'lanadi!"
    )

    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup, disable_web_page_preview=True)


@bot.callback_query_handler(func=lambda call: call.data == "my_stats")
def stats_callback(call):
    u = get_user(call.from_user.id)
    status_map = {
        "none": "Hali ariza topshirilmagan",
        "pending": "⏳ Admin tekshirmoqda",
        "approved": "✅ Tasdiqlangan (500 Stars berilgan)",
        "rejected": "❌ Rad etilgan (30 ta to'lmagan)",
    }
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        f"📊 Sizning natijangiz:\n"
        f"• Chaqirilganlar: <b>{u['invites']} / {REQUIRED_INVITES}</b>\n"
        f"• Holat: <b>{status_map[u['status']]}</b>",
        parse_mode="HTML",
    )


@bot.callback_query_handler(func=lambda call: call.data == "send_user")
def ask_username_callback(call):
    user_id = call.from_user.id
    u = get_user(user_id)
    bot.answer_callback_query(call.id)

    if not is_member(user_id):
        bot.send_message(
            call.message.chat.id,
            f"⚠️ Avval {CHANNEL_URL} kanaliga a'zo bo'ling!"
        )
        return

    if u["invites"] < REQUIRED_INVITES:
        qolgan = REQUIRED_INVITES - u["invites"]
        bot.send_message(
            call.message.chat.id,
            f"❌ Siz hali {REQUIRED_INVITES} ta odamni to'ldirmadingiz!\n"
            f"Hozirda: <b>{u['invites']}</b> ta. Yana <b>{qolgan}</b> ta odam chaqiring — "
            f"to'ldirmasangiz Stars berilmaydi.",
            parse_mode="HTML",
        )
        return

    waiting_for_username.add(user_id)
    bot.send_message(
        call.message.chat.id,
        "✍️ Tabriklaymiz! O'z <b>@username</b> ingizni yozib qoldiring (masalan: <code>@username</code>).\n"
        "Admin tekshirib, siz bilan bog'lanadi!",
        parse_mode="HTML",
    )


@bot.message_handler(func=lambda m: m.from_user.id in waiting_for_username)
def receive_username(message):
    user_id = message.from_user.id
    text = message.text.strip()

    if not text.startswith("@") or len(text) < 4:
        bot.send_message(message.chat.id, "⚠️ Iltimos, to'g'ri @username kiriting (masalan: @sizning_user).")
        return

    waiting_for_username.discard(user_id)
    u = get_user(user_id)
    u["username_submitted"] = text
    u["status"] = "pending"

    bot.send_message(
        message.chat.id,
        f"✅ <b>{text}</b> qabul qilindi!\n"
        "Admin tekshiradi va siz bilan xabarlashadi.",
        parse_mode="HTML",
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Berish (500 Stars)", callback_data=f"approve_{user_id}"),
        types.InlineKeyboardButton("❌ Bermaslik", callback_data=f"reject_{user_id}"),
    )
    bot.send_message(
        ADMIN_ID,
        f"📩 <b>Yangi ariza!</b>\n"
        f"• ID: <code>{user_id}</code>\n"
        f"• Yozgan user: <b>{text}</b>\n"
        f"• Chaqirilganlar: <b>{u['invites']} / {REQUIRED_INVITES}</b>\n"
        f"• Kanal: {CHANNEL_URL}",
        parse_mode="HTML",
        reply_markup=markup,
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith(("approve_", "reject_")))
def admin_decision(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Bu tugma faqat admin uchun!", show_alert=True)
        return

    action, target_str = call.data.split("_", 1)
    target_id = int(target_str)
    u = get_user(target_id)

    if action == "approve":
        u["status"] = "approved"
        bot.edit_message_text(
            call.message.text + "\n\n🟢 <b>TASDIQLANDI (500 Stars berildi)</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
        )
        try:
            bot.send_message(
                target_id,
                f"🎉 Tabriklaymiz! {REQUIRED_INVITES} ta odam sharti tasdiqlandi.\n"
                f"Sizga <b>{REWARD_STARS} Stars</b> berildi! Admin ({u['username_submitted']}) bilan bog'lanadi.",
                parse_mode="HTML",
            )
        except Exception:
            pass
    else:
        u["status"] = "rejected"
        bot.edit_message_text(
            call.message.text + "\n\n🔴 <b>RAD ETILDI (Shart bajarilmagan)</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
        )
        try:
            bot.send_message(
                target_id,
                f"❌ Kechirasiz, {REQUIRED_INVITES} ta odam to'ldirilmagani uchun Stars berilmadi.\n"
                f"Shartni to'liq bajaring.",
                parse_mode="HTML",
            )
        except Exception:
            pass

    bot.answer_callback_query(call.id, "Bajarildi!")


print("Bot ishga tushdi...")
bot.infinity_polling(skip_pending=True)
