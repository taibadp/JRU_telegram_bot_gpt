#from http.client import responses

from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler, MessageHandler, filters

from gpt import ChatGptService
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt, send_text_buttons, Dialog, dialog_user_info_to_str)

import credentials

# якщо користувач продовжує сесію після перезапуску бота - діалог не існує
def init_dialog_if_not(context: ContextTypes.DEFAULT_TYPE):
    dialog = context.user_data.get("dialog")
    if dialog is None:
        context.user_data["dialog"] = Dialog()

# для обраного режиму показує картинку та заголовочний текст
# якщо додані кнопки - виводить і їх
async def show_mode_head(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str, buttons: dict = None):
    await send_image(update, context, mode)
    text = load_message(mode)
    if buttons is None:
        await send_text(update, context, text)
    else:
        await send_text_buttons(update, context, text, buttons)

# обробник ручного введення
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

    # раптом введена неіснуюча команда
    if text[0] == "/":
        await send_text(update, context, "I don't know such command. Use /start command for information")

    else:
        match mode:
            case "GPT":
                response = await chat_gpt.add_message(update.message.text)
                await send_text_buttons(update, context, response, {"gpt_finish": "🛑 Закінчити"})

            case "TALK":
                response = await chat_gpt.add_message(update.message.text)
                await send_text_buttons(update, context, response, {"talk_finish": "🛑 Закінчити"})

            case "QUIZ":
                dialog.quiz_total += 1
                response = await chat_gpt.add_message(text)

                dialog.quiz_count_good_answer(response)

                await send_text_buttons(update, context, f'{response} {dialog.current_quiz_score()}', quiz_buttons_menu())

            case "TRANSLATOR":
                if dialog.transl_lang == "":
                    await send_text(update, context, "ви не обрали мову")
                    await translate(update, context)
                else:
                    response = await chat_gpt.send_question(dialog.prompt, text)
                    await send_text(update, context, "це перекладається як:")
                    await send_text_buttons(update, context, response, {
                        "transl_change": "інша мова",
                        "transl_finish": "🛑 Закінчити"
                    })


            case "FILMS":

                if dialog.films_mode == "GENRE":
                    dialog.films_genre = text
                # test
                response = await chat_gpt.send_question(f"Перевір наявність вказаного жанру у вказаній категорії творів мистецтва", f"чи існує жанр {text} в категорії {dialog.films_cat}? Відповідь ТАК або НІ")
                if response == "НІ":
                    await send_text_buttons(update, context, "Такого жанру не існує. Спробуйте ще", {"films_finish": "🛑 Закінчити"})
                else:
                    await films_ask(update, context)

            case _:
                await send_text(update, context, "Ви не обрали режим спілкування. За подробицями зверніться до /start")

# всі кнопки _finish діють однаково - направляють на /start, де завершується діалог
async def finish_buttons_handler(update: Update, context):
    await start(update, context)
    await update.callback_query.answer()

# команда Старт - головне меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # тут зберігаємо поточний стан користувача
    init_dialog_if_not(context)
    dialog = context.user_data.get("dialog")

    #if dialog.mode not in [None, "DEFAULT"]:
    #    return

    dialog.end_current_dialog()

    await show_mode_head(update, context, 'main')
    await show_main_menu(update, context, {
        'start': 'Головне меню',
        'random': 'Дізнатися випадковий цікавий факт 🧠',
        'gpt': 'Задати питання чату GPT 🤖',
        'talk': 'Поговорити з відомою особистістю 👤',
        'quiz': 'Взяти участь у квізі ❓',
        'translator': 'перекласти іншою мовою',
        'films': 'Рекомендації фільмів'
    })

# команда Випадковий факт
async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_dialog_if_not(context)
    dialog = context.user_data['dialog']

    if dialog.mode != "RANDOM":
        await show_mode_head(update, context, 'random')
    else:
        await send_text(update, context, "і ще факт...")

    dialog.set_mode("RANDOM", load_prompt('random'))
    try:
        response = await chat_gpt.send_question(dialog.prompt, 'Давай рандомний факт')
    except:
        response = f'Interesting fact failed '
    await send_text_buttons(
        update, context,
        response,
        {
            'random_finish' : '🛑 Закінчити',
            'random_one_more' :'🔁 Хочу ще факт',
        }
    )

async def random_buttons_handler(update: Update, context):
    query = update.callback_query.data
    if query == 'random_finish':
        await start(update, context)
    elif query == 'random_one_more':
        await random(update, context)
    await update.callback_query.answer()

# режим розмови з Gpt
async def gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_dialog_if_not(context)
    dialog = context.user_data['dialog']
    dialog.set_mode("GPT", load_prompt('gpt'))
    chat_gpt.set_prompt(dialog.prompt)
    await show_mode_head(update, context, 'gpt', {
            'gpt_finish' : '🛑 Закінчити',
        })

# режим розмова з особистістю
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
    match query:
        case 'talk_finish':
            context.user_data['dialog'].end_current_dialog()
            await start(update, context)
        case 'talk_cobain':
            context.user_data['dialog'].talk_mode = query
            await start_talk_session(update, context)
        case 'talk_queen':
            context.user_data['dialog'].talk_mode = query
            await start_talk_session(update, context)
        case 'talk_tolkien':
            context.user_data['dialog'].talk_mode = query
            await start_talk_session(update, context)
        case 'talk_nietzsche':
            context.user_data['dialog'].talk_mode = query
            await start_talk_session(update, context)
        case 'talk_hawking':
            context.user_data['dialog'].talk_mode = query
            await start_talk_session(update, context)
        case 'talk_prachett':
            context.user_data['dialog'].talk_mode = query
            await start_talk_session(update, context)
        case _:
            await send_text(update, context, "Нажаль, ця персона зараз у відпустці. Оберіть іншу")
            #talk(update, context)
    await update.callback_query.answer()

def talk_subject_name(context):
    talk_mode = context.user_data['dialog'].talk_mode
    match talk_mode:
        case "talk_cobain":
            return "Курт Кобейн"
        case "talk_queen":
            return "Єлизавета II"
        case "talk_tolkien":
            return "Джон Толкін"
        case "talk_nietzsche":
            return "Фрідріх Ніцше"
        case "talk_hawking":
            return "Стівен Гокінг"
        #elif talk_mode == "talk_prachett":
        #    return "Prachett"
        case _:
            return talk_mode[5:].capitalize()

async def start_talk_session(update: Update, context):
    init_dialog_if_not(context)
    #context.user_data['dialog'].mode = "TALK"
    context.user_data['dialog'].set_mode("TALK", load_prompt(context.user_data['dialog'].talk_mode))
    chat_gpt.set_prompt(context.user_data['dialog'].prompt)
    await send_image(update, context, context.user_data['dialog'].talk_mode)
    await send_text_buttons(update, context, f"Hello, it's {talk_subject_name(context)}. Ask me anything", {
            'talk_finish' : '🛑 Закінчити',
        })

# режим Квіз - серії запитань на обрану тему
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

async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_dialog_if_not(context)
    context.user_data['dialog'].set_mode("TRANSLATOR", "")

    await send_text_buttons(update, context, "Оберіть на яку мову перекласти", {
                            "transl_eng": "англійська",
                            "transl_de": "німецька",
                            "transl_es": "іспанська",
                            "transl_jp": "японська",
                            "transl_finish": "🛑 Закінчити"
                        })

async def transl_buttons_handler(update: Update, context):
    init_dialog_if_not(context)
    dialog = context.user_data['dialog']
    query = update.callback_query.data
    match query:
        case 'transl_eng':
            dialog.transl_lang = query
            dialog.set_mode("TRANSLATOR", "Переклади надане далі речення на мову англійська")
            await send_text(update, context, "Обрано англійську")
        case 'transl_de':
            dialog.transl_lang = query
            dialog.set_mode("TRANSLATOR", "Переклади надане далі речення на мову німецька")
            await send_text(update, context, "Обрано німецьку")
        case 'transl_es':
            dialog.transl_lang = query
            dialog.set_mode("TRANSLATOR", "Переклади надане далі речення на мову іспанська")
            await send_text(update, context, "Обрано іспанську")
        case 'transl_jp':
            dialog.transl_lang = query
            dialog.set_mode("TRANSLATOR", "Переклади надане далі речення на мову японська")
            await send_text(update, context, "Обрано японську")
        case "transl_change":
            dialog.transl_lang = ""
            await translate(update, context)
        case _:
            dialog.transl_lang = ""
            await send_text(update, context, "Нажаль, ця мова ще не підтримується. Ви можете обрати іншу")
            await translate(update, context)
    await update.callback_query.answer()

# порадь фільм/книгу/музику, а я покажу, якщо не подобається
async def films(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_dialog_if_not(context)
    dialog = context.user_data['dialog']
    dialog.set_mode("FILMS", "")
    dialog.films_mode = "CAT"
    dialog.films_genre = ""
    await send_text_buttons(update, context, "Оберіть категорію", {
                            "films_films": "фільми",
                            "films_books": "книги",
                            "films_music": "музика",
                            "films_finish": "🛑 Закінчити"
                        })

async def films_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_dialog_if_not(context)
    dialog = context.user_data['dialog']

    if not dialog.films_dict:
        message = ""
    else:
        message = f"Врахуй, що не подобаються наступні твори: {', '.join(dialog.films_dict.keys())}"
    response = await chat_gpt.send_question(
        f"Порекомендуй твір у категорії {dialog.films_cat} жанра {dialog.films_genre}. Просто надай назву і рік",
        message)
    dialog.films_recomend = response
    await send_text_buttons(update, context, response, {"films_dislike": "фуууу", "films_finish": "🛑 Закінчити"})

async def films_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_dialog_if_not(context)
    dialog = context.user_data['dialog']
    query = update.callback_query.data
    if query == "films_films":
        dialog.films_cat = "фільми"
    elif query == "films_books":
        dialog.films_cat = "книги"
    elif query == "films_music":
        dialog.films_cat = "музика"
    elif query == "films_dislike":
        #попередня строка - взяти назву - занести
        last_film = dialog.films_recomend
        dialog.films_dict[last_film] = False
        await films_ask(update, context)

    if dialog.films_mode == "CAT":
        dialog.films_mode = "GENRE"
        await send_text_buttons(update, context, "Тепер напишіть жанр", {
            "films_finish": "🛑 Закінчити"
        })


chat_gpt = ChatGptService(credentials.ChatGPT_TOKEN)
app = ApplicationBuilder().token(credentials.BOT_TOKEN).build()

# Зареєструвати обробник команди можна так:
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, plain_text_handler))

app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', random))
app.add_handler(CommandHandler('gpt', gpt))
app.add_handler(CommandHandler('talk', talk))
app.add_handler(CommandHandler('quiz', quiz))
app.add_handler(CommandHandler('translate', translate))
app.add_handler(CommandHandler('films', films))

# Зареєструвати обробник колбеку можна так:
app.add_handler(CallbackQueryHandler(finish_buttons_handler, pattern='.*_finish$')) #всі кнопки *_finish однаково вертають на початок
app.add_handler(CallbackQueryHandler(random_buttons_handler, pattern='^random_.*'))
#app.add_handler(CallbackQueryHandler(gpt_buttons_handler, pattern='^gpt_.*'))
app.add_handler(CallbackQueryHandler(talk_buttons_handler, pattern='^talk_.*'))
app.add_handler(CallbackQueryHandler(quiz_buttons_handler, pattern='^quiz_.*'))
app.add_handler(CallbackQueryHandler(transl_buttons_handler, pattern='^transl_.*'))
app.add_handler(CallbackQueryHandler(films_buttons_handler, pattern='^films_.*'))

# app.add_handler(CallbackQueryHandler(default_callback_handler))

app.run_polling()
