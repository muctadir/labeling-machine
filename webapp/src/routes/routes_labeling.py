from flask import render_template, request, redirect, url_for, jsonify
from flask_login import login_required
from sqlalchemy import select

from src import app
from src.database.models import Note, LabelingData
from src.database.queries.artifact_queries import lock_artifact_by, add_artifacts
from src.database.queries.label_queries import delete_label, update_artifact_label, \
    label_artifact
from src.helper.consts import *
from src.helper.tools_common import string_none_or_empty
from src.helper.tools_labeling import *


@app.route("/labeling", methods=['GET', 'POST'])
@login_required
def labeling():
    if request.method != 'POST':
        # This is not fully correct! because maybe tagger A label N needed artifacts,
        # but since #tagged_by_two is less than two, app still propose artifacts to guy A
        n_api_tagged_by_two_or_more = get_n_artifacts_labeled_by_n_or_more(2)
        if n_api_tagged_by_two_or_more >= total_artifact_count():
            return "We are done. All {} APIs are tagged by 2+ taggers.".format(total_artifact_count())
        else:
            selected_artifact_id = choose_next_random_api()
            if selected_artifact_id < 0:
                return "It seems you are done. Please Wait for others [Code: {}]".format(selected_artifact_id)
            return redirect(url_for('labeling_with_artifact', target_artifact_id=selected_artifact_id))
    else:
        return "Why POST?"


@app.route("/labeling/<target_artifact_id>", methods=['GET', 'POST'])
@login_required
def labeling_with_artifact(target_artifact_id):
    if not IS_SYSTEM_UP:
        return SYSTEM_STATUS_MESSAGE

    if request.method != 'POST':
        target_artifact_id = int(target_artifact_id)

        artifact_data = Artifact.query.filter_by(id=target_artifact_id).first()
        all_labels = db.session.execute(select(LabelingData.id, LabelingData.labeling)).all()
        all_taggers = [a for a, in db.session.execute(select(ArtifactLabelRelation.created_by).where(
            ArtifactLabelRelation.artifact_id == target_artifact_id)).all()]
        lock_artifact_by(who_is_signed_in(), target_artifact_id)

        return render_template('labeling_pages/artifact.html',
                               artifact_id=target_artifact_id,
                               artifact_data=artifact_data,
                               overall_labeling_status=get_overall_labeling_progress(),
                               user_info=get_labeling_status(who_is_signed_in()),
                               existing_labeling_data=all_labels,
                               all_taggers=', '.join(all_taggers) if all_taggers is not None else None)
    else:
        return "Why POST?"


@app.route("/note", methods=['GET', 'POST'])
@login_required
def note():
    if CURRENT_TASK['level'] != 0:  # We are not at Labeling phase anymore.
        return jsonify('{{ "error": "We are not labeling. Labeling data is in read-only mode." }}')

    if request.method == 'POST':
        artifact_id = request.form['artifact_id']
        note_text = request.form['note']
        action = request.form['action']

        n = len(Note.query.filter_by(artifact_id=artifact_id).filter_by(note=note_text).all())
        my_note_report_on_artifact = Note.query.filter_by(artifact_id=artifact_id).filter_by(note=note_text).filter_by(
            created_by=who_is_signed_in()).first()
        if my_note_report_on_artifact is None:
            status = "false"
        else:
            status = "true"

        if action == 'status':
            return jsonify('{{ "error": "", "{}_new_status": {}, "total": {} }}'.format(note_text, status, n))
        if action == 'toggle':
            if my_note_report_on_artifact is None:
                noteed_post = Note(artifact_id=artifact_id, note=note_text, created_by=who_is_signed_in())
                db.session.add(noteed_post)
                db.session.commit()
                n += 1
                status = "true"
            else:
                db.session.delete(my_note_report_on_artifact)
                db.session.commit()
                n -= 1
                status = "false"
            return jsonify('{{ "error": "", "{}_new_status": {}, "total": {} }}'.format(note_text, status, n))
        else:
            return jsonify('{{ "error": "Bad Request: {}" }}'.format(action))
    else:
        return "Not POST!"


@app.route("/flag_artifact", methods=['GET', 'POST'])
@login_required
def toggle_fp():
    if CURRENT_TASK['level'] != 0:  # We are not at Labeling phase anymore.
        return jsonify('{{ "error": "We are not labeling. Labeling data is in read-only mode." }}')

    if request.method == 'POST':
        artifact_id = request.form['artifact_id']
        action = request.form['action']

        n_flaggers = len(FlaggedArtifact.query.filter_by(artifact_id=artifact_id).all())
        my_flag_report_on_artifact = FlaggedArtifact.query.filter_by(artifact_id=artifact_id).filter_by(
            created_by=who_is_signed_in()).first()

        if my_flag_report_on_artifact is None:
            status = "false"
        else:
            status = "true"

        if action == 'status':
            return jsonify('{{ "error": "", "new_status": {}, "nFP": {} }}'.format(status, n_flaggers))
        if action == 'toggle':
            if my_flag_report_on_artifact is None:
                new_fp_report = FlaggedArtifact(artifact_id=artifact_id, created_by=who_is_signed_in())
                db.session.add(new_fp_report)
                db.session.commit()
                n_flaggers += 1
                status = "true"
            else:
                db.session.delete(my_flag_report_on_artifact)
                db.session.commit()
                n_flaggers -= 1
                status = "false"
            return jsonify('{{ "error": "", "new_status": {}, "nFP": {} }}'.format(status, n_flaggers))
        else:
            return jsonify('{{ "error": "Bad Request: {}" }}'.format(action))

    else:
        return "Not POST!", 400


@app.route("/label", methods=['POST'])
@login_required
def label():
    if CURRENT_TASK['level'] != 0:  # We are not at Labeling phase anymore.
        return jsonify('{ "error": "We are not labeling. Labeling data is in read-only mode." }'), 400

    if request.method == 'POST':
        if string_none_or_empty(request.form['artifact_id']) or string_none_or_empty(
                request.form['duration']) or string_none_or_empty(request.form['labeling_data']):
            return jsonify('{ "status": "Empty arguments" }'), 400

        duration_sec = int(request.form['duration'])
        if duration_sec <= 1:
            return jsonify('{ "status": "Too fast?" }')

        labeling_data = request.form['labeling_data'].strip()
        remark = request.form['remark'].strip() if not string_none_or_empty(request.form['remark']) else None
        artifact_id = int(request.form['artifact_id'])
        label_description = (request.form['label_description'] or '').strip()

        status = label_artifact(artifact_id, labeling_data, label_description, remark, duration_sec, who_is_signed_in())
        return jsonify(f'{{ "status": "{status}" }}')

    else:
        return "Not POST!", 400


@app.route('/update_label_for_artifact/<artifact_id>/<label_id>/<updated_label>', methods=['PUT'])
@login_required
# todo: add description to a newly added label
def update_label_for_artifact(artifact_id, label_id, updated_label):
    if request.method != 'PUT':
        return "Not PUT!", 400

    if string_none_or_empty(artifact_id) or string_none_or_empty(label_id) or string_none_or_empty(
            updated_label):
        return jsonify('{ "status": "Empty arguments" }'), 400

    artifact_id = int(artifact_id)
    label_id = int(label_id)
    try:
        update_artifact_label(artifact_id, label_id, updated_label, '', who_is_signed_in())
    except ValueError as e:
        return jsonify(f'{{"error": "{e}"}}'), 400
    return jsonify('{"status":"successfully updated artifact with new label"}')


@app.route('/remove_label/<label_id>', methods=['DELETE'])
@login_required
def remove_label(label_id):
    if request.method != 'DELETE':
        return "Not DELETE!", 400
    if string_none_or_empty(label_id):
        return "parameter empty", 400

    label_id = int(label_id)
    try:
        delete_label(label_id)
    except ValueError as e:
        return jsonify(f'{{"error":"{e}"}}'), 400

    return jsonify('{"status":"deleted successfully!"}')


@app.route('/manual_label', methods=['GET', 'POST'])
@login_required
def manual_label():
    if request.method == 'GET':
        all_labels = db.session.execute(select(LabelingData.id, LabelingData.labeling)).all()
        return render_template('labeling_pages/manual_labeling.html',
                               existing_labeling_data=all_labels,
                               overall_labeling_status=get_overall_labeling_progress())
    elif request.method == 'POST':
        if string_none_or_empty(request.form['artifact_txt']) or string_none_or_empty(
                request.form['duration']) or string_none_or_empty(request.form['labeling_data']):
            return jsonify('{ "status": "Empty arguments" }'), 400

        labeling_data = request.form['labeling_data'].strip()
        label_description = (request.form['label_description'] or '').strip()
        remark = request.form['remark'].strip() if not string_none_or_empty(request.form['remark']) else None
        duration_sec = int(request.form['duration'])
        artifact_id = add_artifacts([request.form['artifact_txt'].strip()], who_is_signed_in())[0]
        status = label_artifact(artifact_id, labeling_data, label_description, remark, duration_sec, who_is_signed_in())
        return jsonify(f'{{ "status": "{status}" }}')

    else:
        return 'invalid', 400


@app.route('/get_label_description/<label_data>', methods=['GET'])
@login_required
def get_label_description(label_data: str):
    label_data = (label_data or '').strip()
    description = db.session.execute(
        select(LabelingData.label_description).where(LabelingData.labeling == label_data)).scalar()
    return description
