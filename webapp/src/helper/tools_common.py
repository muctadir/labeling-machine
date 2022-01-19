from flask import session
from sqlalchemy import func, distinct

from src import db
from src.database.models import User, FlaggedArtifact


def string_none_or_empty(string: str):
    string = string or ''
    return not string.strip()


def sign_in(username):
    session['username'] = username


def sign_out():
    session.pop('username', None)


def is_signed_in():
    if 'username' not in session:
        return False
    else:
        session_username = session['username']
        db_user = User.query.filter_by(username=session_username).first()
        if db_user is None:
            sign_out()
            return False
        else:
            return True


def who_is_signed_in():
    if 'username' in session:
        return session['username']
    else:
        return None


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
