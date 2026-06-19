#from http.client import responses

from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler, MessageHandler, filters

from gpt import ChatGptService
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt, send_text_buttons, Dialog, dialog_user_info_to_str)

import credentials

def init_dialog_if_not(context: ContextTypes.DEFAULT_TYPE):
    dialog = context.user_data.get("dialog")
    if dialog is None:
        context.user_data["dialog"] = Dialog()

async def show_mode_head(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str, buttons: dict = None):
    try:
        await send_image(update, context, mode)
    except:
        pass
    text = load_message(mode)
    if buttons is None:
        await send_text(update, context, text)
    else:
        await send_text_buttons(update, context, text, buttons)


async def plain_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_dialog_if_not(context)
    dialog = context.user_data.get("dialog")

    text = update.message.text
    mode = context.user_data['dialog'].mode
    """
    if context.user_data['dialog'].mode is None:
        if text == "/start":
            await start(update, context)
        elif text == "/random":
            await random(update, context)
        elif test == "/gpt":
            await gpt(update, context)
        else:
            await send_text(update, context, "I don't know such command. Use /start command for information")
    """
    if text[0] == "/":
        await send_text(update, context, "I don't know such command. Use /start command for information")

    elif mode == "GPT":
        response = await chat_gpt.send_question(dialog.prompt, update.message.text)
        await send_text_buttons(update, context, response, {"gpt_finish": "🛑 Закінчити"})

    elif mode == "TALK":
        response = await chat_gpt.send_question(dialog.prompt, update.message.text)
        await send_text_buttons(update, context, response, {"talk_finish": "🛑 Закінчити"})

    elif mode == "QUIZ":
        dialog.quiz_total += 1
        response = await chat_gpt.add_message(text)

        dialog.quiz_count_good_answer(response)

        await send_text_buttons(update, context, f'{response} {dialog.current_quiz_score()}', quiz_buttons_menu())

    elif mode == "TRANSLATOR":
        response = await chat_gpt.send_question(dialog.prompt, text)
        await send_text_buttons(update, context, "це перекладається як:")
        await send_text_buttons(update, context, response, {
            "transl_change": "інша мова",
            "transl_finish": "🛑 вийти в меню"
        })


    else:
        await send_text(update, context, "Ви не обрали режим спілкування. За подробицями зверніться до /start")

async def finish_buttons_handler(update: Update, context):
    init_dialog_if_not(context)
    context.user_data['dialog'].end_current_dialog()
    await start(update, context)
    await update.callback_query.answer()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # тут зберігаємо поточний стан користувача
    init_dialog_if_not(context)
    dialog = context.user_data.get("dialog")

    if dialog.mode not in [None, "DEFAULT"]:
        return

    dialog.end_current_dialog()

    await show_mode_head(update, context, 'main')
    await show_main_menu(update, context, {
        'start': 'Головне меню',
        'random': 'Дізнатися випадковий цікавий факт 🧠',
        'gpt': 'Задати питання чату GPT 🤖',
        'talk': 'Поговорити з відомою особистістю 👤',
        'quiz': 'Взяти участь у квізі ❓',
        'translator': 'перекласти іншою мовою'
        # Додати команду в меню можна так:
        # 'command': 'button text'

    })


async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_dialog_if_not(context)
    dialog = context.user_data['dialog']

    await show_mode_head(update, context, 'random')

    dialog.set_mode("RANDOM", load_prompt('random'))
    try:
        response = await chat_gpt.send_question(dialog.prompt, 'Давай рандомний факт')
    except:
        response = f'Interesting fact failed '
    # await send_text(update, context, response)
    await send_text_buttons(
        update, context,
        response,
        {
            'random_finish' : '🛑 Закінчити',
            'random_one_more' :'🔁 Хочу ще факт',
        }
    )

async def random_buttons_handler(update: Update, context):
    init_dialog_if_not(context)
    query = update.callback_query.data
    if query == 'random_finish':
        context.user_data['dialog'].end_current_dialog()
        await start(update, context)
    elif query == 'random_one_more':
        await random(update, context)
    await update.callback_query.answer()


async def gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_dialog_if_not(context)
    dialog = context.user_data['dialog']
    dialog.set_mode("GPT", load_prompt('gpt'))
    await show_mode_head(update, context, 'gpt', {
            'gpt_finish' : '🛑 Закінчити',
        })

"""
async def gpt_buttons_handler(update: Update, context):
    init_dialog_if_not(context)
    query = update.callback_query.data
    if query == 'gpt_finish':
        context.user_data['dialog'].end_current_dialog()
        await start(update, context)
    await update.callback_query.answer()
"""


async def talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_dialog_if_not(context)
    dialog = context.user_data['dialog']
    dialog.set_mode("TALK", "")

    await show_mode_head(update, context, 'talk', {
                            "talk_cobain": "Курт Кобейн - Соліст гурту Nirvana 🎸",
                            "talk_queen": "Єлизавета II - Королева Об'єднаного Королівства 👑",
                            "talk_tolkien": 'Джон Толкін - Автор книги "Володар Перснів" 📖',
                            "talk_nietzsche": "Фрідріх Ніцше - Філософ 🧠",
                            "talk_hawking": "Стівен Гокінг - Фізик 🔬",
                            "talk_prachett": "Террі Прачет - письменник"
                        })

async def talk_buttons_handler(update: Update, context):
    init_dialog_if_not(context)
    query = update.callback_query.data
    if query == 'talk_finish':
        context.user_data['dialog'].end_current_dialog()
        await start(update, context)

    elif query == 'talk_cobain':
        context.user_data['dialog'].talk_mode = query
        await start_talk_session(update, context)
    elif query == 'talk_queen':
        context.user_data['dialog'].talk_mode = query
        await start_talk_session(update, context)
    elif query == 'talk_tolkien':
        context.user_data['dialog'].talk_mode = query
        await start_talk_session(update, context)
    elif query == 'talk_nietzsche':
        context.user_data['dialog'].talk_mode = query
        await start_talk_session(update, context)
    elif query == 'talk_hawking':
        context.user_data['dialog'].talk_mode = query
        await start_talk_session(update, context)
    elif query == 'talk_prachett':
        context.user_data['dialog'].talk_mode = query
        await start_talk_session(update, context)
    await update.callback_query.answer()

def talk_subject_name(context):
    talk_mode = context.user_data['dialog'].talk_mode
    if talk_mode == "talk_cobain":
        return "Курт Кобейн"
    elif talk_mode == "talk_queen":
        return "Єлизавета II"

    elif talk_mode == "talk_tolkien":
        return "Джон Толкін"
    elif talk_mode == "talk_nietzsche":
        return "Фрідріх Ніцше"
    elif talk_mode == "talk_hawking":
        return "Стівен Гокінг"
    #elif talk_mode == "talk_prachett":
    #    return "Prachett"
    else:
        return talk_mode[5:].capitalize()


async def start_talk_session(update: Update, context):
    init_dialog_if_not(context)
    #context.user_data['dialog'].mode = "TALK"
    context.user_data['dialog'].set_mode("TALK", load_prompt(context.user_data['dialog'].talk_mode))
    await send_image(update, context, context.user_data['dialog'].talk_mode)
    await send_text_buttons(update, context, f"Hello, it's {talk_subject_name(context)}. Ask me anything", {
            'talk_finish' : '🛑 Закінчити',
        })

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_dialog_if_not(context)
    context.user_data['dialog'].set_mode("QUIZ", load_prompt('quiz'))

    await show_mode_head(update, context, 'quiz', {
                            "quiz_prog": "🐍 Python",
                            "quiz_math": "🖩 Math",
                            "quiz_biology": "🧬 Біологія",
                            "quiz_more": "🔁 продовжити обрану тему",
                            "quiz_finish": "🛑 завершити квіз",
                        })

def quiz_buttons_menu() -> dict:
    return {
        'quiz_more': "🔁 Продовжити квіз",
        'quiz_change': "Змінити тему",
        'quiz_finish': "🛑 Закінчити квіз"
        }

async def quiz_buttons_handler(update: Update, context):
    init_dialog_if_not(context)
    dialog = context.user_data['dialog']
    query = update.callback_query.data
    if query == 'quiz_finish':
        dialog.end_current_dialog()
        await start(update, context)

    elif query == 'quiz_change':
        dialog.end_current_dialog()
        await quiz(update, context)

    elif query == "quiz_more":
        if dialog.quiz_theme == "":
            await send_text(update, context, "Ви не обрали тему, тому поговорімо про Python")
            dialog.quiz_theme = "quiz_prog"

            # перше питання - даємо промпт і тему
            quiz_quest = await chat_gpt.send_question(dialog.prompt, dialog.quiz_theme)
            await send_text(update, context, quiz_quest)
        else:
            quiz_quest = await chat_gpt.add_message('quiz_more')
            await send_text(update, context, quiz_quest)
    else:
        # старт нового квізу. Онулимо дані
        dialog.start_quiz(query)

        #перше питання - даємо промпт і тему
        quiz_quest = await chat_gpt.send_question(dialog.prompt, dialog.quiz_theme)
        await send_text(update, context, quiz_quest)
    await update.callback_query.answer()

"""
Бот пропонує вибрати мову, на яку потрібно перекласти текст, використовуючи кнопки.
Після вибору мови користувач надсилає текст, який потрібно перекласти.
Бот використовує ChatGPT для перекладу тексту та надсилає результат користувачеві.
До повідомлення має бути прикріплена кнопка зміни мови та кнопка "Закінчити", натискання на яку
працює так само, як команда /start.
"""

async def translator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_dialog_if_not(context)
    context.user_data['dialog'].set_mode("TRANSLATOR", "")

    await send_text_buttons(update, context, "textОберіть на яку мову перекласти", {
                            "transl_eng": "англійська",
                            "transl_de": "німецька",
                            "transl_es": "іспанська",
                            "transl_jp": "японська",
                            "transl_finish": "🛑 вийти в меню"
                        })

async def transl_buttons_handler(update: Update, context):
    init_dialog_if_not(context)
    dialog = context.user_data['dialog']
    query = update.callback_query.data
    if query == 'transl_eng':
        dialog.set_mode("TRANSLATOR", "Переклади надане далі речення на мову англійська")
    elif query == 'transl_de':
        dialog.set_mode("TRANSLATOR", "Переклади надане далі речення на мову німецька")
    elif query == 'transl_es':
        dialog.set_mode("TRANSLATOR", "Переклади надане далі речення на мову іспанська")
    elif query == 'transl_jp':
        dialog.set_mode("TRANSLATOR", "Переклади надане далі речення на мову японська")
    elif query == "transl_change":
        translator(update, context)

    await update.callback_query.answer()

chat_gpt = ChatGptService(credentials.ChatGPT_TOKEN)
app = ApplicationBuilder().token(credentials.BOT_TOKEN).build()

# Зареєструвати обробник команди можна так:
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, plain_text_handler))

app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', random))
app.add_handler(CommandHandler('gpt', gpt))
app.add_handler(CommandHandler('talk', talk))
app.add_handler(CommandHandler('quiz', quiz))
app.add_handler(CommandHandler('translator', translator))

# Зареєструвати обробник колбеку можна так:
app.add_handler(CallbackQueryHandler(finish_buttons_handler, pattern='.*_finish$')) #всі кнопки *_finish однаково вертають на початок
app.add_handler(CallbackQueryHandler(random_buttons_handler, pattern='^random_.*'))
#app.add_handler(CallbackQueryHandler(gpt_buttons_handler, pattern='^gpt_.*'))
app.add_handler(CallbackQueryHandler(talk_buttons_handler, pattern='^talk_.*'))
app.add_handler(CallbackQueryHandler(quiz_buttons_handler, pattern='^quiz_.*'))
app.add_handler(CallbackQueryHandler(transl_buttons_handler, pattern='^transl_.*'))
# app.add_handler(CallbackQueryHandler(default_callback_handler))

app.run_polling()
