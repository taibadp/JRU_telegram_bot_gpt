from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, \
    BotCommand, MenuButtonCommands, BotCommandScopeChat, MenuButtonDefault
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes


# конвертує об'єкт user в рядок
def dialog_user_info_to_str(user_data) -> str:
    mapper = {'language_from': 'Мова оригіналу', 'language_to': 'Мова перекладу',
              'text_to_translate': 'Текст для перекладу'}
    return '\n'.join(map(lambda k, v: (mapper[k], v), user_data.items()))


# надсилає в чат текстове повідомлення
async def send_text(update: Update, context: ContextTypes.DEFAULT_TYPE,
                    text: str) -> Message:
    if text.count('_') % 2 != 0:
        message = f"Рядок '{text}' є невалідним з точки зору markdown. Скористайтеся методом send_html()"
        print(message)
        return await update.message.reply_text(message)

    text = text.encode('utf16', errors='surrogatepass').decode('utf16')
    return await context.bot.send_message(chat_id=update.effective_chat.id,
                                          text=text,
                                          parse_mode=ParseMode.MARKDOWN)


# надсилає в чат html повідомлення
async def send_html(update: Update, context: ContextTypes.DEFAULT_TYPE,
                    text: str) -> Message:
    text = text.encode('utf16', errors='surrogatepass').decode('utf16')
    return await context.bot.send_message(chat_id=update.effective_chat.id,
                                          text=text, parse_mode=ParseMode.HTML)


# надсилає в чат текстове повідомлення, та додає до нього кнопки
async def send_text_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE,
                            text: str, buttons: dict) -> Message:
    text = text.encode('utf16', errors='surrogatepass').decode('utf16')
    keyboard = []
    for key, value in buttons.items():
        button = InlineKeyboardButton(str(value), callback_data=str(key))
        keyboard.append([button])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return await context.bot.send_message(
        update.effective_message.chat_id,
        text=text, reply_markup=reply_markup,
        message_thread_id=update.effective_message.message_thread_id)


# надсилає в чат фото
async def send_image(update: Update, context: ContextTypes.DEFAULT_TYPE,
                     name: str) -> Message:
    with open(f'resources/images/{name}.jpg', 'rb') as image:
        return await context.bot.send_photo(chat_id=update.effective_chat.id,
                                            photo=image)


# відображає команду та головне меню
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE,
                         commands: dict):
    command_list = [BotCommand(key, value) for key, value in commands.items()]
    await context.bot.set_my_commands(command_list, scope=BotCommandScopeChat(
        chat_id=update.effective_chat.id))
    await context.bot.set_chat_menu_button(menu_button=MenuButtonCommands(),
                                           chat_id=update.effective_chat.id)


# видаляємо команди для конкретного чату
async def hide_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.delete_my_commands(
        scope=BotCommandScopeChat(chat_id=update.effective_chat.id))
    await context.bot.set_chat_menu_button(menu_button=MenuButtonDefault(),
                                           chat_id=update.effective_chat.id)


# завантажує повідомлення з папки /resources/messages/
def load_message(name):
    with open("resources/messages/" + name + ".txt", "r",
              encoding="utf8") as file:
        return file.read()


# завантажує промпт з папки /resources/messages/
def load_prompt(name):
    with open("resources/prompts/" + name + ".txt", "r",
              encoding="utf8") as file:
        return file.read()


async def default_callback_handler(update: Update,
                                   context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    query = update.callback_query.data
    await send_html(update, context, f'You have pressed button with {query} callback')


class Dialog:
    mode: str = "DEFAULT"  # обраний пункт головного меню
    talk_mode: str = ""
    prompt: str = ""
    quiz_theme: str = ""
    quiz_quest: str = ""
    quiz_score: int = 0
    quiz_total: int = 0
    films_mode = ""
    films_cat = ""
    films_genre = ""
    films_recomend = ""
    films_dict = {}
    transl_lang = ""

    def __init__(self):
        self.mode = "DEFAULT"  # обраний пункт головного меню
        self.talk_mode = ""
        self.prompt = ""
        self.quiz_theme = ""
        self.quiz_quest = ""
        self.quiz_score = 0
        self.quiz_total = 0
        self.films_mode = ""
        self.films_dict = {}
        self.films_cat = ""
        self.films_genre = ""
        self.films_recomend = ""
        self.transl_lang = ""

    def set_mode(self, mode: str, prompt: str = ""):
        self.mode = mode
        self.prompt = prompt

    def end_current_dialog(self):
        self.__init__()

    def start_quiz(self, theme: str):
        self.quiz_theme = theme
        self.quiz_score = 0
        self.quiz_total = 0

    def quiz_count_good_answer(self, response: str):
        if "Правильно" in response:
            self.quiz_score += 1

    def current_quiz_score(self):
        return f"правильних {self.quiz_score}/{self.quiz_total}"
