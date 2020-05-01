import telebot
import logging
import os
from peewee import SqliteDatabase, Model, IntegerField, IntegrityError

admin_chat = -123456789  # Айди чата поддержки
bot = telebot.TeleBot('123456789:AAFYqsQoAo01LcIH7Kn-oUEm474_Zdkgy8')   # Ваш токен

logging.basicConfig(filename="support.log", level=logging.ERROR, format='[LINE:%(lineno)d] %(levelname)-8s [%(asctime)s]  %(message)s')
db = SqliteDatabase('db.sqlite3')


class Block(Model):
    user_id = IntegerField(unique=True)

    class Meta:
        database = db


class Message(Model):
    from_ = IntegerField()
    id = IntegerField(unique=True)

    class Meta:
        database = db


if not os.path.exists('db.sqlite3'):
    Message.create_table()
    Block.create_table()


class Filters:
    def is_user(message):
        return message.chat.id != admin_chat and message.chat.type == 'private'

    def is_admin(message):
        return message.chat.id == admin_chat

    def is_answer(message):
        return message.chat.id == admin_chat and message.reply_to_message is not None and message.reply_to_message.forward_date is not None

    def is_blocked(message):
        return Block.select().where(Block.user_id == message.chat.id).exists()

    def is_not_blocked(message):
        return not Block.select().where(Block.user_id == message.chat.id).exists()


@bot.message_handler(commands=['start'])
def send_start(message):
    print(message.chat.id)
    bot.send_message(message.chat.id, text='Здравствуйте! Это бот для поддержки моих разработок. Если есть вопросы то пишите не стесняйтесь 😊\n\n👨🏻‍💻 with ♥ by BPRO')


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, text="Отправьте ваш вопрос в этот чат с ботом, я доставлю его моему госпоодину.\n\n👨🏻‍💻 with ♥ by BPRO")


@bot.message_handler(content_types=['text', 'audio', 'document', 'photo', 'sticker', 'video', 'voice', 'location', 'contact'], func=lambda msg:
                     Filters.is_user(msg) and Filters.is_not_blocked(msg))
def get_question(message):
    bot.send_message(message.chat.id, text='😃 Ватсон, у нас хорошие новости!\n\nЯ успешно отправил ваш вопрос моему господину!\n\n👨🏻‍💻 with ♥ by BPRO')
    sent = bot.forward_message(admin_chat, message.chat.id, message.message_id)
    Message.create(from_=message.chat.id, id=sent.message_id).save()


@bot.message_handler(func=Filters.is_user)
def get_error_question(message):
    bot.send_message(message.chat.id, text='😵 Упс... Ватсон у нас проблемы!\n\nСервер не смог обработать запрос, приносим свои извенения в скором времени мы это исправим!')


@bot.message_handler(commands=['block'], func=Filters.is_answer)
def block(message):
    user_id = Message.select().where(Message.id == message.reply_to_message.message_id).get().from_
    try:
        Block.create(user_id=user_id).save()
    except IntegrityError:
        pass

    bot.send_message(message.chat.id, f'Пользователь {user_id} успешно заблокирован!')


@bot.message_handler(commands=['unblock'], func=Filters.is_answer)
def unblock(message):
    user_id = Message.select().where(Message.id == message.reply_to_message.message_id).get().from_
    try:
        Block.select().where(user_id == user_id).get().delete_instance()
    except Block.DoesNotExist:
        pass

    bot.send_message(message.chat.id, text='Пользователь {user_id} успешно разаблокирован!')


@bot.message_handler(content_types=['text', 'photo'], func=Filters.is_answer)
def answer_question(message):
    to_user_id = Message.select().where(Message.id == message.reply_to_message.message_id).get().from_
    if message.photo is not None:
        bot.send_photo(to_user_id, message.photo[-1].file_id, message.caption)
    else:
        bot.send_message(to_user_id, message.text)
    bot.send_message(message.chat.id, text='😺 Успех!\n\n📨 Голуби с письмами уже в пути, ближайщие дни ответ дойдёт до пользователя.', reply_to_message_id=message.message_id)


bot.infinity_polling(none_stop=True, timeout=60)
