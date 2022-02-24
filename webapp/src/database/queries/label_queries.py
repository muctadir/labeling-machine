from sqlalchemy import select, delete, update, distinct
from sqlalchemy.sql.functions import count

from src import db
from src.database.models import LabelingData, ArtifactLabelRelation, Artifact
from src.helper.tools_common import string_none_or_empty


def get_all_labels():
    return [lbl for lbl, in db.session.execute(select(LabelingData)).all()]


def delete_label(label_id: int):
    labeled_arts = db.session.execute(
        select(ArtifactLabelRelation).where(ArtifactLabelRelation.label_id == label_id)).all()

    if labeled_arts is not None and len(labeled_arts) > 0:
        raise ValueError("artifacts already labeled with this label")

    # TODO: later on check if there are related theme.

    db.session.execute(delete(LabelingData).where(LabelingData.id == label_id))
    db.session.commit()


def update_label(label_id: int, name: str, description: str):
    if string_none_or_empty(name):
        raise ValueError('label is empty')

    existing = db.session.execute(
        select(LabelingData).where(LabelingData.labeling == name, LabelingData.id != label_id)).all()
    if existing is not None and len(existing) > 0:
        raise ValueError('label already exists')

    db.session.execute(
        update(LabelingData).where(LabelingData.id == label_id).values(labeling=name, label_description=description))
    db.session.commit()


def update_artifact_label(artifact_id: int, old_label_id: int, new_label_txt: str, label_remark: str,
                          creator: str):
    new_label_id = db.session.execute(select(LabelingData.id).where(LabelingData.labeling == new_label_txt)).scalar()
    qry = update(ArtifactLabelRelation).where(
        ArtifactLabelRelation.artifact_id == artifact_id, ArtifactLabelRelation.label_id == old_label_id).values(
        label_id=new_label_id, remark=label_remark, created_by=creator)
    db.session.execute(qry)
    db.session.commit()


def get_or_create_label_with_text(label_txt: str, label_description: str, creator: str):
    lbl = get_label(label_txt) or LabelingData(
        labeling=label_txt, created_by=creator, label_description=label_description)
    db.session.add(lbl)
    db.session.flush()
    db.session.commit()
    return lbl


def get_label(label_txt):
    return db.session.execute(select(LabelingData).where(
        LabelingData.labeling == label_txt)).scalar()


def label_artifact(artifact_id: int, labeling_data: str, label_description: str, remark: str, duration_sec: int,
                   creator: str):
    lbl = get_or_create_label_with_text(labeling_data, label_description, creator)
    labeled_artifact = db.session.execute(
        select(ArtifactLabelRelation).where(ArtifactLabelRelation.artifact_id == artifact_id,
                                            ArtifactLabelRelation.created_by == creator)).scalar()

    if labeled_artifact is not None:
        labeled_artifact.label = lbl
        labeled_artifact.duration_sec = duration_sec
        labeled_artifact.label_update_count = labeled_artifact.label_update_count + 1
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
