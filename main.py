import os
import random
import telebot
from telebot import types, custom_filters
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage
from conn_BD import get_conn_BD

# Подключаемся к БД
get_conn_BD()

print("Бот работает")

# Инициализация хранилища состояний и бота
state_storage = telebot.StateMemoryStorage()
token_bot = os.getenv('TOKEN')
bot =  telebot.TeleBot(token_bot, state_storage=state_storage)

buttons = []

class Command:
    """Класс для хранения команд"""
    ADD_WORD = 'Добавить слово'
    DELETE_WORD = 'Удалить слово'
    NEXT = 'Дальше ⏭'
    MYWORDS = 'Мои слова'
    GENERAL = 'Общие слова'


class MyStates(StatesGroup):
    """Класс для хранения состояний бота"""
    target_word = State()
    translate_word = State()


# Функции для работы с подсказками и отображением переводов
def show_hint(*lines):
    return '\n'.join(lines)


def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']} "


def get_user_data(user_id):
    """Получить данные пользователя. Если нет — создать запись."""
    conn = get_conn_BD()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT step, target_word, translate_word FROM users WHERE user_id = %s",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            return {"step": row[0], "target_word": row[1], "translate_word": row[2]}
        else:
            # Создаём нового пользователя
            cursor.execute(
                "INSERT INTO users (user_id, step) VALUES (%s, 0)",
                (user_id,)
            )
            conn.commit()
            return {"step": 0, "target_word": None, "translate_word": None}
    except Exception as e:
        print(f"Ошибка при получении данных пользователя {user_id}: {e}")
        return {"step": 0, "target_word": None, "translate_word": None}
    finally:
        cursor.close()


def update_user_step(user_id, step):
    """Обновить шаг пользователя в БД"""
    conn = get_conn_BD()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET step = %s WHERE user_id = %s",
        (step, user_id)
    )
    conn.commit()
    cursor.close()


def save_target_word(user_id, target_word, translate_word):
    """Сохранить текущее слово в БД"""
    conn = get_conn_BD()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET target_word = %s, translate_word = %s WHERE user_id = %s",
        (target_word, translate_word, user_id)
    )
    conn.commit()
    cursor.close()


def get_four_words(user_id, use_user_words=False):
    conn = get_conn_BD()
    cursor = conn.cursor()
    try:
        query = """
        SELECT english_word, russian_translation
        FROM (
            SELECT english_word, russian_translation FROM words
            UNION
            SELECT english_word, russian_translation FROM userwords WHERE user_id = %s
        ) AS combined_words
        ORDER BY random()
        LIMIT 4;
        """
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        cursor.close()
        return results  # список из 4 кортежей (english_word, russian_translation)
    except Exception as e:
        print(f"Ошибка в get_four_words: {e}")
        cursor.close()
        return None


@bot.message_handler(commands=['help'])
def show_help(message):
    """Обработчик команды /help - выводит справочную информацию о боте"""
    help_text = (
        "📘 *Справка по использованию бота «EnglishCard»*\n\n"
        
        "🔹 *Основные команды:*\n"
        "/start — запустить бота и начать обучение\n"
        "/help — показать это справочное сообщение\n\n"

        "🔹 *Режимы обучения:*\n"
        "• «Общие слова» — изучение слов из общей базы данных\n"
        "• «Мои слова» — изучение только ваших персональных слов\n\n"

        "🔹 *Как работать с карточками:*\n"
        "1. Вам показывается русское слово и 4 варианта перевода\n"
        "2. Выберите правильный английский перевод\n"
        "3. Если ответ верный — появится сообщение «Отлично!❤»\n"
        "4. Если неверный — вариант отметится ❌\n\n"

        "🔹 *Доступные действия (кнопки):*\n"
        f"• {Command.NEXT} — следующая карточка\n"
        f"• {Command.ADD_WORD} — добавить новое слово в персональную коллекцию\n"
        f"• {Command.DELETE_WORD} — удалить текущее слово из коллекции\n"
        f"• {Command.MYWORDS} — переключиться на режим «Мои слова»\n"
        f"• {Command.GENERAL} — переключиться на режим «Общие слова»\n\n"

        "🔹 *Добавление нового слова:*\n"
        f"1. Нажмите кнопку {Command.ADD_WORD}\n"
        "2. Введите: английское_слово -> русский_перевод\n"
        "   Пример: peace -> мир\n"
        "3. Бот подтвердит добавление или сообщит об ошибке\n\n"

        "🔹 *Важные примечания:*\n"
        f"• Если в персональной коллекции нет слов, режим «{Command.MYWORDS}» покажет предупреждение\n"
        "• Нельзя добавить слово, которое уже есть в коллекции\n"
        "• Для начала работы обязательно используйте /start"
    )

    bot.send_message(message.chat.id, help_text)


# Обработчик команды /cards
@bot.message_handler(commands=['start'])
def create_cards(message):
    cid = message.chat.id
    user_id = message.from_user.id

    # Получаем состояние пользователя из БД
    user_state = get_user_data(user_id)
    use_user_words = (user_state["step"] == 2)

    # Получаем 4 случайных слова (целевое + 3 альтернативы)
    four_words = get_four_words(user_id, use_user_words)
    if not four_words:
        if use_user_words:
            bot.send_message(cid, "В вашей коллекции нет слов!")
        else:
            bot.send_message(cid, "База данных пуста!")
        return

    # Выбираем одно слово как целевое (например, первое в списке)
    target_word, translate = four_words[0]
    # Остальные 3 слова — варианты ответа
    other_words = [word[0] for word in four_words[1:]]

    # Формируем клавиатуру
    markup = types.ReplyKeyboardMarkup(row_width=2)
    buttons = []

    # Добавляем целевое слово (правильный ответ)
    target_word_btn = types.KeyboardButton(target_word)
    buttons.append(target_word_btn)

    # Добавляем 3 альтернативных варианта
    for word in other_words:
        btn = types.KeyboardButton(word)
        buttons.append(btn)

    random.shuffle(buttons)

    # Добавляем служебные кнопки
    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    mywords_btn = types.KeyboardButton(Command.MYWORDS)
    general_btn = types.KeyboardButton(Command.GENERAL)
    buttons.extend([next_btn, add_word_btn, delete_word_btn, mywords_btn, general_btn])

    markup.add(*buttons)

    text = f"Выбери перевод слова:\n🇷🇺 {translate}"
    bot.send_message(cid, text, reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.target_word, cid)

    with bot.retrieve_data(message.from_user.id, cid) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate
        data['other_words'] = other_words

    save_target_word(user_id, target_word, translate)


@bot.message_handler(func=lambda message: message.text == Command.MYWORDS)
def switch_to_my_words(message):
    cid = message.chat.id
    user_id = message.from_user.id
    update_user_step(user_id, 2)  # Режим «мои слова»
    bot.send_message(cid, "Теперь вы учите только свои слова!")


@bot.message_handler(func=lambda message: message.text == Command.GENERAL)
def switch_to_general(message):
    cid = message.chat.id
    user_id = message.from_user.id
    update_user_step(user_id, 0)  # Режим «общие слова»
    bot.send_message(cid, "Теперь вы учите слова из общей базы!")


# Обработчик команды "Добавить слово" (верно)
@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    cid = message.chat.id
    user_id = message.from_user.id
    # Переводим пользователя в состояние ввода слова
    bot.set_state(user_id, MyStates.translate_word, cid)

    bot.send_message(cid, "Введите новое слово и его перевод через -> (например: Peace -> Мир)")


@bot.message_handler(state=MyStates.translate_word)
def hundler_add_word(message):
    user_id = message.from_user.id
    cid = message.chat.id

    try:
        # Разбираем ввод
        parts = message.text.split(' -> ', 1)
        if len(parts) != 2:
            bot.send_message(message.chat.id, "Ошибка: используйте формат «Слово -> Перевод»")
            return

        word, translation = parts[0].strip().lower(), parts[1].strip()

        # Проверяем, что поля не пустые
        if not word or not translation:
            bot.send_message(message.chat.id, "Ошибка: слово или перевод не указаны")
            return

        conn = get_conn_BD()
        cursor = conn.cursor()

        # Сначала проверяем, существует ли слово в БД
        cursor.execute(
            "SELECT 1 FROM userwords WHERE user_id = %s AND english_word = %s",
            (user_id, word)
        )
        if cursor.fetchone():
            bot.send_message(cid, "Это слово уже есть в вашей коллекции!")
            return

        # Если слова нет - добавляем
        cursor.execute("INSERT INTO userwords (user_id, english_word, russian_translation) VALUES (%s, %s, %s)",
                    (user_id, word, translation)
        )
        conn.commit()
        cursor.close()

        bot.send_message(message.chat.id, "Новое слово добавлено!")

        # Возвращаем пользователя в основное состояние
        bot.delete_state(user_id, cid)

    except Exception as e:
        bot.send_message(cid, "Ошибка при добавлении слова. Попробуйте ещё раз.")
        print(f'Error in handle_add_word: {e}')


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)


# Обработчик команды "Удалить слово"
@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        english_word = data["target_word"]
        user_id = message.from_user.id

        conn = get_conn_BD()
        cursor = conn.cursor()

        cursor.execute(
            'DELETE FROM UserWords '
            'WHERE user_id = %s AND english_word=%s',
            (user_id, english_word)
        )
        conn.commit()

        if cursor.rowcount > 0:
            bot.send_message(message.chat.id, "Слово удалено!")
        else:
            bot.send_message(message.chat.id, "Данное слово не найдено в ваших карточках")

        cursor.close()


# Обработчик любых текстовых сообщений
@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    text = message.text
    cid = message.chat.id

    try:
        with bot.retrieve_data(message.from_user.id, cid) as data:
            if 'target_word' not in data:
                bot.send_message(cid, "Начните с /start")
                return

            target_word = data['target_word']
            translate = data['translate_word']

            markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            buttons = []

            if text == target_word:
                # Правильный ответ
                hint = show_target(data)
                hint_text = ["Отлично!❤", hint]
                buttons = [
                    types.KeyboardButton(Command.NEXT),
                    types.KeyboardButton(Command.ADD_WORD),
                    types.KeyboardButton(Command.DELETE_WORD)
                ]
                hint = show_hint(*hint_text)
            else:
                # Неправильный ответ — показываем все варианты
                hint = show_hint(
                    "Допущена ошибка!",
                    f"Попробуй ещё раз вспомнить слово 🇷🇺{translate}"
                )

                # Собираем все варианты (целевое + альтернативы)
                all_words = [target_word]
                if 'other_words' in data:
                    all_words.extend(data['other_words'])

                # Создаём кнопки: ошибочный вариант отмечаем ❌
                for word in all_words:
                    if word == text:
                        buttons.append(types.KeyboardButton(f"{word}❌"))
                    else:
                        buttons.append(types.KeyboardButton(word))

                # Добавляем служебные кнопки
                buttons.extend([
                    types.KeyboardButton(Command.NEXT),
                    types.KeyboardButton(Command.ADD_WORD),
                    types.KeyboardButton(Command.DELETE_WORD)
                ])

            markup.add(*buttons)
            bot.send_message(cid, hint, reply_markup=markup)

    except KeyError:
        bot.send_message(cid, "Начните с /start")
    except Exception as e:
        print(f"Ошибка в message_reply: {e}")
        bot.send_message(cid, "Произошла ошибка. Попробуйте /start")


# Регистрация фильтров и запуск бота
bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.infinity_polling(skip_pending=True)



