from typing import List

from sqlalchemy import select, insert

from src import db
from src.database.models import Theme, LabelingData


def get_all_themes() -> List[Theme]:
    return [t for t, in db.session.execute(select(Theme)).all()]


def get_theme_by_id(tid: int) -> Theme:
    return db.session.execute(select(Theme).where(Theme.id == tid)).scalar()


def get_theme_by_name(name: str) -> Theme:
    return db.session.execute(select(Theme).where(Theme.theme == name)).scalar()


def create_theme(name: str, description: str, label_ids: List[int], creator: str) -> Theme:
    if get_theme_by_name(name) is not None:
        raise ValueError('Theme with this name exists')

    labels = db.session.execute(select(LabelingData).where(LabelingData.id in label_ids)).all()
    theme = Theme(theme=name, theme_description=description, labels=labels, created_by=creator)
    db.session.add(theme)
    db.session.commit()
    return theme
