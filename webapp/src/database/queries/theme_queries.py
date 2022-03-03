from typing import List

from sqlalchemy import select, delete

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

    labels = [lbl for lbl, in
              db.session.execute(select(LabelingData).where(LabelingData.id.in_(label_ids))).all()] or []
    theme = Theme(theme=name, theme_description=description, labels=labels, created_by=creator)
    db.session.add(theme)
    db.session.commit()
    return theme


def update_theme(tid: int, name: str, description: str, label_ids: List[int], creator: str) -> Theme:
    same_name_theme = db.session.execute(select(Theme).where(Theme.theme == name).where(not (Theme.id == tid))).all()
    if same_name_theme is not None and len(same_name_theme) > 0:
        raise ValueError('theme with same name exists')

    old_theme = get_theme_by_id(tid)
    old_theme.theme = name
    old_theme.theme_description = description
    old_theme.created_by = creator
    old_theme.labels = [lbl for lbl, in
                        db.session.execute(select(LabelingData).where(LabelingData.id.in_(label_ids))).all()] or []

    db.session.add(old_theme)
    db.session.commit()
    return old_theme


def remove_theme(tid: int):
    theme = get_theme_by_id(tid)
    if theme is None:
        raise ValueError('theme does not exist')

    if theme.labels is not None and len(theme.labels) > 0:
        raise ValueError('theme has labels')

    db.session.execute(delete(Theme).where(Theme.id == tid))
    db.session.commit()
