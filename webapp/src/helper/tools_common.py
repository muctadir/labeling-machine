from flask_login import current_user

from src import db


def string_none_or_empty(string: str):
    string = string or ''
    return not string.strip()


def who_is_signed_in():
    return current_user.username if current_user.is_authenticated else None


def get_all_users():
    sql = 'SELECT username FROM User'
    result = db.engine.execute(sql)
    users = [user[0] for user in result]
    return users


def read_artifacts_from_file(file):
    text = []
    for line in file:
        line = str(line, 'utf-8') if line is not None else ''
        if not string_none_or_empty(line):
            text.append(line.strip())
    return text
