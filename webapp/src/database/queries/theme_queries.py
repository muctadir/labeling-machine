from sqlalchemy import select

from src import db
from src.database.models import Theme


def get_all_themes():
    return [t for t, in db.session.execute(select(Theme)).all()]
