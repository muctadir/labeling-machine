from sqlalchemy import select, delete

from src import db
from src.database.models import LabelingData, ArtifactLabelRelation


def delete_label(label_id: int):
    labeled_arts = db.session.execute(
        select(ArtifactLabelRelation).where(ArtifactLabelRelation.label_id == label_id)).all()

    if labeled_arts is not None and len(labeled_arts) > 0:
        raise ValueError("artifacts already labeled with this label")

    # TODO: later on check if there are related theme.

    db.session.execute(delete(LabelingData).where(LabelingData.id == label_id))
    db.session.commit()


def update_label_name(label_id: int, name: str):
    pass


def update_label_description(label_id: int, description: str):
    pass


def update_artifact_label(artifact_id: int, old_label_id: int, new_label_txt: str):
    updated_label = get_or_create_label_with_text(new_label_txt)
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
