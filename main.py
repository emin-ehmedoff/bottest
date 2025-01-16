from pyrogram import Client, filters
from pyrogram.types import Message

# Bot üçün konfiqurasiya
bot_token = "7631661650:AAFyLxGS_2tTirwd8A1Jxn3QEi_FERqnREg"
bot = Client("my_bot", bot_token=bot_token)

# İstifadəçi məlumatları üçün lüğət
user_sessions = {}

def validate_api_data(api_id, api_hash):
    if not api_id.isdigit():
        return False, "API ID rəqəmlərdən ibarət olmalıdır."
    if len(api_hash) != 32:
        return False, "API hash düzgün uzunluqda deyil."
    return True, None

@bot.on_message(filters.command(["start"]))
def start(client, message: Message):
    message.reply("Salam! Mənə API ID göndərin:")

@bot.on_message(filters.text & ~filters.command(["start"]))
def handle_message(client, message: Message):
    user_id = message.from_user.id

    if user_id not in user_sessions:
        # İlk dəfə məlumat göndərir
        user_sessions[user_id] = {"step": "api_id", "api_id": message.text}
        is_valid, error = validate_api_data(message.text, "")
        if not is_valid:
            message.reply(error)
            return
        message.reply("API ID saxlanıldı! İndi API hash kodunu göndərin:")
    elif user_sessions[user_id]["step"] == "api_id":
        # API hash-ni saxla
        user_sessions[user_id]["api_hash"] = message.text
        user_sessions[user_id]["step"] = "api_hash"
        message.reply("API hash saxlanıldı! İndi telefon nömrənizi göndərin:")
    elif user_sessions[user_id]["step"] == "api_hash":
        # Telefon nömrəsini saxla və doğrulama kodunu göndər
        user_sessions[user_id]["phone_number"] = message.text
        user_sessions[user_id]["step"] = "phone_number"

        user_client = Client(
            f"user_{user_id}",
            api_id=int(user_sessions[user_id]["api_id"]),
            api_hash=user_sessions[user_id]["api_hash"]
        )

        try:
            user_client.start()
            response = user_client.send_code_request(user_sessions[user_id]["phone_number"])
            user_sessions[user_id]["phone_code_hash"] = response.phone_code_hash
            message.reply("Doğrulama kodu göndərildi! Təsdiq kodunu göndərin:")
        except Exception as e:
            message.reply(f"Doğrulama kodunu göndərmək mümkün olmadı: {e}")
    elif user_sessions[user_id]["step"] == "phone_number":
        # Doğrulama kodunu təsdiq et
        verification_code = message.text

        user_client = Client(
            f"user_{user_id}",
            api_id=int(user_sessions[user_id]["api_id"]),
            api_hash=user_sessions[user_id]["api_hash"]
        )

        try:
            user_client.start()
            user_client.sign_in(
                user_sessions[user_id]["phone_number"],
                verification_code,
                phone_code_hash=user_sessions[user_id]["phone_code_hash"]
            )
            user_sessions[user_id]["verified"] = True
            message.reply("API məlumatlarınız təsdiq edildi!")
        except Exception as e:
            message.reply(f"Doğrulama kodu səhvdir və ya istifadə müddəti bitmişdir: {e}")

bot.run()
