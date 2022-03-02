from flask_login import UserMixin
from sqlalchemy.orm import validates, relationship
from sqlalchemy.sql import func

from src import db


class __TrackedModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=func.now())
    created_by = db.Column(db.Text, nullable=True)


class User(UserMixin, db.Model):
    """
    Registered Users
    """
    __tablename__ = 'User'
    username = db.Column(db.Text, primary_key=True)
    password = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.Text)
    education = db.Column(db.Text)
    occupation = db.Column(db.Text)
    affiliation = db.Column(db.Text)
    years_xp = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=func.now())

    def get_id(self):
        return self.username


class Note(__TrackedModel):
    """
    Additional notes on artifacts. e.g., "Nice example", "Needs extra caution".
    """
    __tablename__ = 'Note'
    note = db.Column(db.Text, nullable=False)
    artifact_id = db.Column(db.Integer, db.ForeignKey('Artifact.id'))
    artifact = relationship('Artifact')


class FlaggedArtifact(__TrackedModel):
    __tablename__ = 'FlaggedArtifact'
    artifact_id = db.Column(db.Integer, db.ForeignKey('Artifact.id'))
    artifact = relationship('Artifact')


class LockedArtifact(__TrackedModel):
    __tablename__ = 'LockedArtifact'
    artifact_id = db.Column(db.Integer, db.ForeignKey('Artifact.id'))
    artifact = relationship('Artifact')


class ArtifactLabelRelation(__TrackedModel):
    __tablename__ = 'ArtifactLabelRelation'
    artifact_id = db.Column(db.ForeignKey('Artifact.id'))
    label_id = db.Column(db.ForeignKey('Label.id'))
    remark = db.Column(db.Text)
    artifact = relationship('Artifact', back_populates='labels_relation')
    label = relationship('LabelingData', back_populates='artifacts_relation')
    duration_sec = db.Column(db.Integer)
    label_update_count = db.Column(db.Integer, default=1, nullable=False)


class Artifact(__TrackedModel):
    __tablename__ = 'Artifact'
    text = db.Column(db.Text, nullable=False)
    identifier = db.Column(db.Text)
    labels_relation = relationship('ArtifactLabelRelation', back_populates='artifact')
    uploaded_manually = db.Column(db.Boolean, default=False, nullable=False)


class LabelingData(__TrackedModel):
    __tablename__ = 'Label'
    labeling = db.Column(db.Text, nullable=False, unique=True)
    label_description = db.Column(db.Text)
    artifacts_relation = relationship('ArtifactLabelRelation', back_populates='label')
    theme_id = db.Column(db.ForeignKey('Theme.id'))
    theme = relationship('Theme', back_populates='labels')


class Theme(__TrackedModel):
    __tablename__ = 'Theme'
    theme = db.Column(db.Text, nullable=False, unique=True)
    theme_description = db.Column(db.Text)
    update_count = db.Column(db.Integer, default=1, nullable=False)
    labels = relationship('LabelingData', back_populates='theme')
