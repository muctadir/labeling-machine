from datetime import datetime
from typing import List

from sqlalchemy import insert, func, select, distinct

from src import db
from src.database.models import Artifact, LockedArtifact, ArtifactLabelRelation, FlaggedArtifact, LabelingData
from src.helper.tools_common import string_none_or_empty, who_is_signed_in


def add_artifacts(artifact_txt_list: List[str], creator: str) -> List[int]:
    artifact_txt_list = filter(lambda s: not string_none_or_empty(s), artifact_txt_list)
    inserted_ids = []
    for art in artifact_txt_list:
        stmt = insert(Artifact).values(text=art, created_by=creator)
        inserted_ids.append(db.session.execute(stmt).inserted_primary_key[0])
    db.session.commit()
    return inserted_ids


def get_artifacts_with_label(label_text: str) -> List[Artifact]:
    qry = select(Artifact).join(ArtifactLabelRelation.artifact).join(ArtifactLabelRelation.label).where(
        LabelingData.labeling == label_text)
    artifacts = db.session.execute(qry).all()
    return artifacts


def unlock_artifacts_by(username):
    if not username:
        return
    my_lock = LockedArtifact.query.filter_by(created_by=username).first()
    if my_lock is not None:
        db.session.delete(my_lock)
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


def total_artifact_count() -> int:
    return len(db.session.execute(select(Artifact.id)).all())


def artifact_needs_labeling_count() -> int:
    query = select(Artifact.id).except_(
        select(ArtifactLabelRelation.artifact_id).group_by(ArtifactLabelRelation.artifact_id).having(
            func.count(ArtifactLabelRelation.created_by) > 1))
    return len(db.session.execute(query).all())


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
