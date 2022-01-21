from sqlalchemy import select, delete, update, distinct
from sqlalchemy.sql.functions import count

from src import db
from src.database.models import LabelingData, ArtifactLabelRelation, Artifact
from src.helper.tools_common import string_none_or_empty


def delete_label(label_id: int):
    labeled_arts = db.session.execute(
        select(ArtifactLabelRelation).where(ArtifactLabelRelation.label_id == label_id)).all()

    if labeled_arts is not None and len(labeled_arts) > 0:
        raise ValueError("artifacts already labeled with this label")

    # TODO: later on check if there are related theme.

    db.session.execute(delete(LabelingData).where(LabelingData.id == label_id))
    db.session.commit()


def update_label_name(label_id: int, name: str):
    if string_none_or_empty(name):
        raise ValueError('label is empty')

    existing = db.session.execute(select(LabelingData).where(LabelingData.labeling == name)).all()
    if existing is not None and len(existing) > 0:
        raise ValueError('label already exists')

    db.session.execute(update(LabelingData).where(LabelingData.id == label_id).values(labeling=name))
    db.session.commit()


def update_label_description(label_id: int, description: str):
    db.session.execute(update(LabelingData).where(LabelingData.id == label_id).values(remark=description))
    db.session.commit()


def update_artifact_label(artifact_id: int, old_label_id: int, new_label_txt: str, creator: str):
    updated_label = get_or_create_label_with_text(new_label_txt, creator)
    artifact_label_rel = db.session.execute(
        select(ArtifactLabelRelation).where(ArtifactLabelRelation.artifact_id == artifact_id).where(
            ArtifactLabelRelation.label_id == old_label_id)).scalar()

    if artifact_label_rel is None:
        raise ValueError("artifact is not labeled with this label")

    artifact_label_rel.label_id = updated_label.id
    db.session.add(artifact_label_rel)
    db.session.flush()
    db.session.commit()


def get_or_create_label_with_text(label_txt: str, creator: str):
    lbl = db.session.execute(select(LabelingData).where(
        LabelingData.labeling == label_txt)).scalar() or LabelingData(
        labeling=label_txt, remark='', created_by=creator)
    db.session.add(lbl)
    db.session.flush()
    db.session.commit()
    return lbl


def label_artifact(artifact_id: int, labeling_data: str, remark: str, duration_sec: int, creator: str):
    lbl = get_or_create_label_with_text(labeling_data, creator)
    labeled_artifact = db.session.execute(
        select(ArtifactLabelRelation).where(ArtifactLabelRelation.artifact_id == artifact_id,
                                            ArtifactLabelRelation.created_by == creator)).scalar()

    if labeled_artifact is not None:
        labeled_artifact.label = lbl
        labeled_artifact.duration_sec = duration_sec
        labeled_artifact.remark = remark
        status = 'updated'
    else:
        ar = db.session.execute(select(Artifact).where(Artifact.id == artifact_id)).scalar()
        labeled_artifact = ArtifactLabelRelation(label=lbl, artifact=ar, created_by=creator,
                                                 duration_sec=duration_sec, remark=remark)
        status = 'success'

    db.session.add(labeled_artifact)
    db.session.commit()
    return status


def get_n_labeled_artifact_per_user():
    """
    Return a dictionary of {username: n_labeled_artifact, ...}
    """
    result = db.session.query(
        ArtifactLabelRelation.created_by, count(distinct(ArtifactLabelRelation.artifact_id))).group_by(
        ArtifactLabelRelation.created_by).all()
    return {user: lab_art for user, lab_art in result}
