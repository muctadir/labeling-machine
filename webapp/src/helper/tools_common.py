from flask_login import login_user, logout_user, current_user
from sqlalchemy import func, distinct

from src import db
from src.database.models import FlaggedArtifact


def string_none_or_empty(string: str):
    string = string or ''
    return not string.strip()


def sign_in(user):
    login_user(user, force=True)


def sign_out():
    logout_user()


def is_signed_in():
    return current_user.is_authenticated


def who_is_signed_in():
    return current_user.username if current_user.is_authenticated else None


def get_all_users():
    sql = 'SELECT username FROM User'
    result = db.engine.execute(sql)
    users = [user[0] for user in result]
    return users


def get_false_positive_artifacts():
    """
    Return artifacts marked as false positive by me, or marked as false positive by at least 2 people
    """
    q_artifacts_marked_fp_by_me = db.session.query(distinct(FlaggedArtifact.artifact_id)).filter(
        FlaggedArtifact.created_by == who_is_signed_in())
    q_artifacts_marked_fp_by_2 = db.session.query(
        distinct(FlaggedArtifact.artifact_id)).group_by(FlaggedArtifact.artifact_id).having(func.count() > 1)
    result = {row[0] for row in q_artifacts_marked_fp_by_me.union(q_artifacts_marked_fp_by_2).all()}
    return result
