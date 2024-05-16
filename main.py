import os
import telebot
import paramiko
import re
import logging
import psycopg2
from psycopg2 import Error
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
SSH_HOST = os.getenv('SSH_HOST')
SSH_PORT = os.getenv('SSH_PORT')
SSH_USERNAME = os.getenv('SSH_USERNAME')
SSH_PASSWORD = os.getenv('SSH_PASSWORD')
POSTGRESQL_USER = os.getenv('POSTGRESQL_USER')
POSTGRESQL_PASSWORD = os.getenv('POSTGRESQL_PASSWORD')
POSTGRESQL_HOST = os.getenv('POSTGRESQL_HOST')
POSTGRESQL_PORT = os.getenv('POSTGRESQL_PORT')
POSTGRESQL_DB = os.getenv('POSTGRESQL_DB')

logging.basicConfig(filename='bot.log', level=logging.INFO)

bot = telebot.TeleBot(TOKEN)


# Функция обработки почты
@bot.message_handler(commands=['find_email'])
def find_email(message):
    logging.info(f"Пользователь {message.from_user.id} запросил поиск email")
    bot.send_message(message.chat.id, "Введите текст для поиска email-адресов:")
    bot.register_next_step_handler(message, process_email_search)


# Функция для обработки текста и поиска email-адресов
def process_email_search(message):
    text = message.text
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        response = "Найденные адреса электронной почты:\n"
        for email in emails:
            response += f"{email}\n"
        bot.send_message(message.chat.id, response)
        bot.send_message(message.chat.id, 'Хотите сохранить найденные адреса в базу данных? (Да/нет)')
        bot.register_next_step_handler(message, save_emails_choice, emails)
    else:
        bot.send_message(message.chat.id, "Email-адреса не найдены.")


# Функция для сохранения найденных email-адресов в БД
def save_emails_to_db(emails):
    try:
        with psycopg2.connect(user=POSTGRESQL_USER,
                              password=POSTGRESQL_PASSWORD,
                              host=POSTGRESQL_HOST,
                              port=POSTGRESQL_PORT,
                              database=POSTGRESQL_DB) as connection:
            with connection.cursor() as cursor:
                for email in emails:
                    cursor.execute(
                        'INSERT INTO "emails" (emailAddress) VALUES (%s) ON CONFLICT (emailAddress) DO NOTHING',
                        (email,)
                    )
        logging.info("Email-адреса успешно сохранены в базе данных.")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)


# Функция для обработки выбора сохранения email-адресов в базе данных
def save_emails_choice(message, emails):
    choice = message.text.lower()
    if choice == 'да':
        save_emails_to_db(emails)
        bot.send_message(message.chat.id, "Email-адреса успешно сохранены в базе данных.")
    elif choice == 'нет':
        bot.send_message(message.chat.id, "Email-адреса не сохранены.")
    else:
        bot.send_message(message.chat.id, "Неверный выбор. Пожалуйста, введите 'Да' или 'Нет'.")


# Функция обработки номеров телефона
@bot.message_handler(commands=['find_phone_number'])
def find_phone_number(message):
    logging.info(f"Пользователь {message.from_user.id} запросил поиск номеров телефона")
    bot.send_message(message.chat.id, "Введите текст для поиска номеров телефонов:")
    bot.register_next_step_handler(message, process_phone_number_search)


# Функция для сохранения найденных номеров телефонов в БД
def save_phone_numbers_to_db(phone_numbers):
    try:
        with psycopg2.connect(user=POSTGRESQL_USER,
                              password=POSTGRESQL_PASSWORD,
                              host=POSTGRESQL_HOST,
                              port=POSTGRESQL_PORT,
                              database=POSTGRESQL_DB) as connection:
            with connection.cursor() as cursor:
                for phone_number in phone_numbers:
                    cursor.execute(
                        'INSERT INTO "phoneNumbers" (phoneNumber) VALUES (%s) ON CONFLICT (phoneNumber) DO NOTHING',
                        (phone_number,)
                    )
        logging.info("Номера телефонов успешно сохранены в базе данных.")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)


# Функция для обработки текста и поиска номеров телефонов
def process_phone_number_search(message):
    text = message.text
    phone_pattern = r'(?:\+7|8)[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}'
    phone_numbers = re.findall(phone_pattern, text)
    if phone_numbers:
        response = "Найденные номера телефонов:\n"
        for phone_number in phone_numbers:
            response += f"{phone_number}\n"
        bot.send_message(message.chat.id, response)
        bot.send_message(message.chat.id, 'Хотите сохранить найденные номера телефонов в базу данных? (Да/нет)')
        bot.register_next_step_handler(message, save_phone_numbers_choice, phone_numbers)
    else:
        bot.send_message(message.chat.id, "Номера телефонов не найдены.")


# Функция для обработки выбора сохранения номеров телефонов в БД
def save_phone_numbers_choice(message, phone_numbers):
    choice = message.text.lower()
    if choice == 'да':
        save_phone_numbers_to_db(phone_numbers)
        bot.send_message(message.chat.id, "Номера телефонов успешно сохранены в базе данных.")
    elif choice == 'нет':
        bot.send_message(message.chat.id, "Номера телефонов не сохранены.")
    else:
        bot.send_message(message.chat.id, "Неверный выбор. Пожалуйста, введите 'Да' или 'Нет'.")


# Функция-обработчик команды /verify_password
@bot.message_handler(commands=['verify_password'])
def verify_password(message):
    logging.info(f"User {message.from_user.id} requested password verification")
    bot.send_message(message.chat.id, "Введите пароль для проверки сложности:")
    bot.register_next_step_handler(message, process_password_verification)


# Функция для обработки пароля и проверки его сложности
def process_password_verification(message):
    password = message.text
    if re.match(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()])[A-Za-z\d!@#$%^&*()]{8,}$', password):
        bot.send_message(message.chat.id, "Пароль сложный")
    else:
        bot.send_message(message.chat.id, "Пароль простой")


@bot.message_handler(commands=['find_email'])
# Функция для установления SSH-соединения с удаленным сервером и выполнения команды
def ssh_command(host, port, username, password, command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=username, password=password)
    stdin, stdout, stderr = client.exec_command(command)
    output = stdout.read().decode()
    client.close()
    return output


# Информация о релизе
@bot.message_handler(commands=['get_release'])
def get_release(message):
    logging.info(f"Пользователь {message.from_user.id} запросил информацию о релизе")
    output = ssh_command(SSH_HOST, int(SSH_PORT), SSH_USERNAME, SSH_PASSWORD, 'lsb_release -a')
    bot.send_message(message.chat.id, output)


# Информация об архитектуре процессора, имени хоста системы и версии ядра
@bot.message_handler(commands=['get_uname'])
def get_uname(message):
    logging.info(
        f"Пользователь {message.from_user.id} запросил информацию об архитектуре процессора, имени хоста системы и версии ядра")
    output = ssh_command(SSH_HOST, int(SSH_PORT), SSH_USERNAME, SSH_PASSWORD, 'uname --all')
    bot.send_message(message.chat.id, output)


# Информация о времени работы системы
@bot.message_handler(commands=['get_uptime'])
def get_uptime(message):
    logging.info(f"Пользователь {message.from_user.id} запросил информацию о времени работы системы")
    output = ssh_command(SSH_HOST, int(SSH_PORT), SSH_USERNAME, SSH_PASSWORD, 'uptime -p')
    bot.send_message(message.chat.id, f"Система работает: {output}")


# Информация о состоянии файловой системы
@bot.message_handler(commands=['get_df'])
def get_df(message):
    logging.info(f"Пользователь {message.from_user.id} запросил информацию о состоянии файловой системы")
    output = ssh_command(SSH_HOST, int(SSH_PORT), SSH_USERNAME, SSH_PASSWORD, 'df --all')
    bot.send_message(message.chat.id, output)


# Сбор информации о состоянии оперативной памяти
@bot.message_handler(commands=['get_free'])
def get_free(message):
    logging.info(f"Пользователь {message.from_user.id} запросил информацию о состоянии оперативной памяти")
    output = ssh_command(SSH_HOST, int(SSH_PORT), SSH_USERNAME, SSH_PASSWORD, 'free --mega')
    bot.send_message(message.chat.id, f"В мегабайтах:\n{output}")


# Информация о производительности системы
@bot.message_handler(commands=['get_mpstat'])
def get_mpstat(message):
    logging.info(f"Пользователь {message.from_user.id} запросил информацию о производительности системы")
    output = ssh_command(SSH_HOST, int(SSH_PORT), SSH_USERNAME, SSH_PASSWORD, 'mpstat')
    bot.send_message(message.chat.id, output)


# Информация о работающих в данной системе пользователях
@bot.message_handler(commands=['get_w'])
def get_w(message):
    logging.info(f"Пользователь {message.from_user.id} запросил информацию о работающих в данной системе пользователях")
    output = ssh_command(SSH_HOST, int(SSH_PORT), SSH_USERNAME, SSH_PASSWORD, 'w')
    bot.send_message(message.chat.id, output)


# Информация о последних 10 входах в систему
@bot.message_handler(commands=['get_auths'])
def get_auths(message):
    logging.info(f"Пользователь {message.from_user.id} запросил информацию о последних 10 входах в систему")
    output = ssh_command(SSH_HOST, int(SSH_PORT), SSH_USERNAME, SSH_PASSWORD, 'last -n 10')
    bot.send_message(message.chat.id, output)


# Информация о последних 5 критических событиях
@bot.message_handler(commands=['get_critical'])
def get_critical(message):
    logging.info(f"Пользователь {message.from_user.id} запросил информацию о последних 5 критических событиях")
    output = ssh_command(SSH_HOST, int(SSH_PORT), SSH_USERNAME, SSH_PASSWORD, "journalctl -p crit -n 5")
    bot.send_message(message.chat.id, output)


# Информация о запущенных процессах
@bot.message_handler(commands=['get_ps'])
def get_ps(message):
    logging.info(f"Пользователь {message.from_user.id} запросил информацию о запущенных процессах")
    output = ssh_command(SSH_HOST, int(SSH_PORT), SSH_USERNAME, SSH_PASSWORD, "ps -A u | head -n 10")
    bot.send_message(message.chat.id, output)


# Информация об используемых портах
@bot.message_handler(commands=['get_ss'])
def get_ss(message):
    logging.info(f"Пользователь {message.from_user.id} запросил информацию об используемых портах")
    output = ssh_command(SSH_HOST, int(SSH_PORT), SSH_USERNAME, SSH_PASSWORD, "ss -l | head -n 20")
    bot.send_message(message.chat.id, output)


# Информация об установленных пакетах
@bot.message_handler(commands=['get_apt_list'])
def get_apt_list(message):
    logging.info(f"Пользователь {message.from_user.id} запросил информацию об установленных пакетах")
    output = ssh_command(SSH_HOST, int(SSH_PORT), SSH_USERNAME, SSH_PASSWORD, "apt list --installed | head -n 11")
    bot.send_message(message.chat.id, output)


# Информация о запущенных сервисах
@bot.message_handler(commands=['get_services'])
def get_services(message):
    logging.info(f"Пользователь {message.from_user.id} запросил информацию о запущенных сервисах")
    output = ssh_command(SSH_HOST, int(SSH_PORT), SSH_USERNAME, SSH_PASSWORD,
                         "systemctl list-units --type=service --state=running")
    bot.send_message(message.chat.id, output)


@bot.message_handler(commands=['get_repl_logs'])
def get_repl_logs(message):
    logging.info(f"Пользователь {message.from_user.id} запросил информацию логов о репликации")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=SSH_HOST, username=SSH_USERNAME, password=SSH_PASSWORD, port=int(SSH_PORT))
    stdin, stdout, stderr = client.exec_command(f'cat /var/log/postgresql/* | grep repl | tail -n 20')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    text = ''
    for line in data.split('\n'):
        if 'repl' in line:
            text += line + '\n'
    if len(text) == 0:
        text = 'Логи репликации не найдены'
    if len(text) > 3000:
        text = text[:3000]
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['get_emails'])
def get_emails(message):
    logging.info(f"Пользователь {message.from_user.id} запросил информацию из БД о email-адресах")
    connection = None
    cursor = None
    output = ''

    try:
        connection = psycopg2.connect(user=POSTGRESQL_USER,
                                      password=POSTGRESQL_PASSWORD,
                                      host=POSTGRESQL_HOST,
                                      port=POSTGRESQL_PORT,
                                      database=POSTGRESQL_DB)

        cursor = connection.cursor()
        cursor.execute('SELECT * FROM "emails"')
        data = cursor.fetchall()

        for row in data:
            output += f"{row[0]}. {row[1]}\n"

        logging.info("Команда 'SELECT * FROM emails' успешно выполнена")
        if output:
            bot.send_message(message.chat.id, output)
        else:
            bot.send_message(message.chat.id, 'Email-адреса не найдены...')
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()


@bot.message_handler(commands=['get_phone_numbers'])
def get_phone_numbers(message):
    logging.info(f"Пользователь {message.from_user.id} запросил информацию из БД о номерах телефона")
    connection = None
    cursor = None
    output = ''

    try:
        connection = psycopg2.connect(user=POSTGRESQL_USER,
                                      password=POSTGRESQL_PASSWORD,
                                      host=POSTGRESQL_HOST,
                                      port=POSTGRESQL_PORT,
                                      database=POSTGRESQL_DB)

        cursor = connection.cursor()
        cursor.execute('SELECT * FROM "phoneNumbers"')
        data = cursor.fetchall()

        for row in data:
            output += f"{row[0]}. {row[1]}\n"

        logging.info("Команда 'SELECT * FROM phoneNumbers' успешно выполнена")
        if output:
            bot.send_message(message.chat.id, output)
        else:
            bot.send_message(message.chat.id, 'Номера телефонов не найдены...')
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()


# Запуск бота
bot.polling()
