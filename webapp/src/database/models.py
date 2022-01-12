from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import validates, relationship
from sqlalchemy.sql import func

from src import db


class __TrackedModel(db.Model):
    __abstract__ = True
    created_at = db.Column(db.DateTime, default=func.now())
    created_by = db.Column(db.Text, nullable=True)


class User(db.Model):
    """
    Registered Users
    """
    __tablename__ = 'User'
    username = db.Column(db.Text, primary_key=True)
    gender = db.Column(db.Text)
    education = db.Column(db.Text)
    occupation = db.Column(db.Text)
    affiliation = db.Column(db.Text)
    years_xp = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=func.now())

    @validates('username', 'gender', 'education', 'occupation')
    def convert_lower(self, key, value):
        return value.title()


class Note(__TrackedModel):
    """
    Additional notes on artifacts. e.g., "Nice example", "Needs extra caution".
    """
    __tablename__ = 'Note'
    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    note = db.Column(db.Text, nullable=False)
    artifact_id = db.Column(db.Integer, ForeignKey('Artifact.id'))
    artifact = relationship('Artifact')


class FlaggedArtifact(__TrackedModel):
    __tablename__ = 'FlaggedArtifact'
    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    artifact_id = db.Column(db.Integer, ForeignKey('Artifact.id'))
    artifact = relationship('Artifact')


class LockedArtifact(__TrackedModel):
    __tablename__ = 'LockedArtifact'
    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    artifact_id = db.Column(db.Integer, ForeignKey('Artifact.id'))
    artifact = relationship('Artifact')


class __ArtifactLabelRelation(__TrackedModel):
    __tablename__ = 'ArtifactLabelRelation'
    artifact_id = Column(ForeignKey('Artifact.id'), primary_key=True)
    label_id = Column(ForeignKey('Label.id'), primary_key=True)
    artifact = relationship('Artifact', back_populates='labels')
    label = relationship('LabelingData', back_populates='artifacts')


class Artifact(__TrackedModel):
    __tablename__ = 'Artifact'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text = db.Column(db.Text, nullable=False)
    labels = relationship('__ArtifactLabelRelation', back_populates='artifact')


class LabelingData(__TrackedModel):
    __tablename__ = 'Label'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # update the following two lines to store labeled data from users
    labeling = db.Column(db.Text, nullable=False)  # actual data provided by labelers
    remark = db.Column(db.Text)  # optional data provided by labelers
    duration_sec = db.Column(db.Integer)
    artifacts = relationship('__ArtifactLabelRelation', back_populates='label')

# class ReviewedParagraph(db.Model):
#     __tablename__ = 'ReviewedParagraph'
#     reviewId = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     apiId = db.Column(db.Integer)
#     charStart = db.Column(db.Integer)
#     charEnd = db.Column(db.Integer)
#     text = db.Column(db.Text)
#     username = db.Column(db.Text)
#     created_at = db.Column(db.DateTime, default=func.now())
#
#     def __init__(self, _api_id, _char_start, _char_end, _text, _username):
#         self.apiId = _api_id
#         self.charStart = _char_start
#         self.charEnd = _char_end
#         self.text = _text
#         self.username = _username

# class ApprovedParagraphDocTypes(db.Model):
#     __tablename__ = 'ApprovedParagraphDocTypes'
#     reviewId = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     apiId = db.Column(db.Integer)
#     charStart = db.Column(db.Integer)
#     charEnd = db.Column(db.Integer)
#     text = db.Column(db.Text)
#     parentLabelingIds = db.Column(db.Text)
#     docType = db.Column(db.Text)
#     rate = db.Column(db.Integer)
#     username = db.Column(db.Text)
#     created_at = db.Column(db.DateTime, default=func.now())
#     remark = db.Column(db.Text)
#
#     def __init__(self, _api_id, _char_start, _char_end, _text, _parent_labling_ids, _docTypes, _username):
#         self.apiId = _api_id
#         self.charStart = _char_start
#         self.charEnd = _char_end
#         self.text = _text
#         self.parentLabelingIds = _parent_labling_ids
#         self.docType = _docTypes
#         self.rate = None
#         self.username = _username
#         self.remark = ""
#
