import os
import psycopg2
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Настройки подключения к базе данных
db_name = os.getenv('NAME_BD')
db_user = os.getenv('USER_BD')
db_password = os.getenv('PASSWORD_BD')
db_host = os.getenv('HOST_BD')
db_port = os.getenv('PORT_BD')


def get_conn_BD():
    """Создаёт и возвращает подключение к базе данных."""
    return psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )