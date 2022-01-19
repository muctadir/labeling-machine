from datetime import datetime
from typing import List

from sqlalchemy import insert, func

from src import db
from src.database.models import Artifact, LockedArtifact
from src.helper.tools_common import string_none_or_empty


def add_artifacts(artifact_txt_list: List[str], creator: str):
    artifact_txt_list = filter(lambda s: not string_none_or_empty(s), artifact_txt_list)
    stmt = insert(Artifact).values([dict(text=art, created_by=creator) for art in artifact_txt_list])
    db.session.execute(stmt)
    db.session.commit()


def unlock_artifacts_by(username):
    if not username:
        return
    myLock = LockedArtifact.query.filter_by(created_by=username).first()
    if myLock is not None:
        db.session.delete(myLock)
        db.session.commit()


def lock_artifact_by(username, artifact_id):
    if not username:
        return
    unlock_artifacts_by(username)
    db.session.add(LockedArtifact(created_by=username, artifact_id=artifact_id))
    db.session.commit()


def get_locked_artifacts():
    update_api_locks()
    result = db.session.query(LockedArtifact.artifact_id, func.count(LockedArtifact.created_by)).group_by(
        LockedArtifact.artifact_id).all()
    all_locks = {row[0]: row[1] for row in result}
    return all_locks


def update_api_locks():
    all_locks = LockedArtifact.query.all()
    now_datetime = datetime.utcnow()
    for aLock in all_locks:
        if (now_datetime - aLock.created_at).total_seconds() / 60 >= 15:  # 15min
            # print("Unlocking Artifact: {} ->  {}:{}".format(aLock.username, aLock.sourceId, aLock.artifact_post_id))
            db.session.delete(aLock)
    db.session.commit()
