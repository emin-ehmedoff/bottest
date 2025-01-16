from pyrogram import Client, filters
from pyrogram.types import Message

bot_token = "7631661650:AAFyLxGS_2tTirwd8A1Jxn3QEi_FERqnREg"  # Əvəz edin və ya mühit dəyişənindən çəkin

bot = Client("my_bot", bot_token=bot_token)

user_sessions = {}

@bot.on_message(filters.command("start"))
def start(client, message: Message):
    message.reply("Salam! Mənə API ID göndərin:")

@bot.on_message(filters.text & ~filters.command())
def handle_message(client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_sessions:
        user_sessions[user_id] = {"step": "api_id", "api_id": message.text}
        message.reply("API ID saxlanıldı! İndi API hash kodunu göndərin:")
    elif user_sessions[user_id]["step"] == "api_id":
        user_sessions[user_id]["api_hash"] = message.text
        user_sessions[user_id]["step"] = "api_hash"
        message.reply("API hash saxlanıldı! İndi telefon nömrənizi göndərin:")
    elif user_sessions[user_id]["step"] == "api_hash":
        user_sessions[user_id]["phone_number"] = message.text
        user_sessions[user_id]["step"] = "phone_number"

        user_client = Client(
            f"user_{user_id}",
            api_id=user_sessions[user_id]["api_id"],
            api_hash=user_sessions[user_id]["api_hash"]
        )

        with user_client:
            try:
                response = user_client.send_code_request(user_sessions[user_id]["phone_number"])
                user_sessions[user_id]["phone_code_hash"] = response.phone_code_hash
                message.reply("Doğrulama kodu göndərildi! Təsdiq kodunu göndərin:")
            except Exception as e:
                message.reply(f"Doğrulama kodunu göndərmək mümkün olmadı: {e}")
    elif user_sessions[user_id]["step"] == "phone_number":
        verification_code = message.text

        user_client = Client(
            f"user_{user_id}",
            api_id=user_sessions[user_id]["api_id"],
            api_hash=user_sessions[user_id]["api_hash"]
        )

        with user_client:
            try:
                user_client.sign_in(
                    user_sessions[user_id]["phone_number"],
                    verification_code,
                    phone_code_hash=user_sessions[user_id]["phone_code_hash"]
                )
                user_sessions[user_id]["verified"] = True
                message.reply("API məlumatlarınız təsdiq edildi! İndi qrupların ID-lərini göndərin:\nFormat: <source_chat_id> <target_chat_id>")
            except Exception as e:
                message.reply(f"Doğrulama kodu səhvdir və ya istifadə müddəti bitmişdir: {e}")
    elif user_sessions[user_id]["step"] == "verified":
        args = message.text.split()
        if len(args) != 2:
            message.reply("Zəhmət olmasa, qrupların ID-lərini düzgün formatda göndərin:\nFormat: <source_chat_id> <target_chat_id>")
            return

        source_chat_id = int(args[0])
        target_chat_id = int(args[1])

        user_client = Client(
            f"user_{user_id}",
            api_id=user_sessions[user_id]["api_id"],
            api_hash=user_sessions[user_id]["api_hash"]
        )

        with user_client:
            try:
                members = user_client.get_chat_members(source_chat_id)
                for member in members:
                    try:
                        user_client.add_chat_members(target_chat_id, member.user.id)
                        message.reply(f"İstifadəçi {member.user.id} uğurla köçürüldü!")
                    except Exception as e:
                        message.reply(f"İstifadəçi {member.user.id} köçürülə bilmədi: {e}")
            except Exception as e:
                message.reply(f"Qrup üzvlərini əldə etmək mümkün olmadı: {e}")

bot.run()
