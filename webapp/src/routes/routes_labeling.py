import itertools

from flask import render_template, request, redirect, url_for, jsonify
from flask_login import login_required
from sqlalchemy import select

from src import app
from src.database.models import Note, LabelingData
from src.database.queries.artifact_queries import lock_artifact_by, add_artifacts, get_artifacts_with_label, \
    get_artifact_by_id
from src.database.queries.label_queries import delete_label, update_artifact_label, \
    label_artifact, get_label, get_or_create_label_with_text, update_label, get_all_labels, get_label_by_id
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


@app.route("/labeling/<target_artifact_id>", methods=['GET'])
@login_required
def labeling_with_artifact(target_artifact_id):
    if not IS_SYSTEM_UP:
        return SYSTEM_STATUS_MESSAGE

    target_artifact_id = int(target_artifact_id)

    artifact_data = get_artifact_by_id(target_artifact_id)
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


@app.route('/update_label_for_artifact/<artifact_id>/<label_id>', methods=['PUT'])
@login_required
def update_label_for_artifact(artifact_id, label_id):
    updated_label = str.strip(request.form['new_label'] or '')
    remark = str.strip(request.form['remark'] or '')
    if string_none_or_empty(artifact_id) or string_none_or_empty(label_id) or string_none_or_empty(
            updated_label):
        return jsonify('{ "status": "Empty arguments" }'), 400

    artifact_id = int(artifact_id)
    label_id = int(label_id)

    try:
        old_remark, old_creator, old_lbl = db.session.execute(
            select(ArtifactLabelRelation.remark, ArtifactLabelRelation.created_by, LabelingData.labeling).join(
                ArtifactLabelRelation.label).where(
                ArtifactLabelRelation.artifact_id == artifact_id, ArtifactLabelRelation.label_id == label_id)).first()
        remark += f' [(OLD) label: {old_lbl}, remark: {old_remark}, by: {old_creator}]'
        update_artifact_label(artifact_id, label_id, updated_label, remark, who_is_signed_in())
    except ValueError as e:
        return jsonify({"status": f"{e}"}), 400
    except TypeError as e:
        return jsonify({'status': 'invalid data'}), 400

    return jsonify({"status": f"successfully updated artifact (id:{artifact_id}) with label ({updated_label})"})


@app.route('/manual_label', methods=['GET'])
@login_required
def manual_label_view():
    all_labels = db.session.execute(select(LabelingData.id, LabelingData.labeling)).all()
    return render_template('labeling_pages/manual_labeling.html',
                           existing_labeling_data=all_labels,
                           overall_labeling_status=get_overall_labeling_progress())


@app.route('/manual_label', methods=['GET', 'POST'])
@login_required
def manual_label_post():
    if string_none_or_empty(request.form['artifact_txt']) or string_none_or_empty(
            request.form['duration']) or string_none_or_empty(request.form['labeling_data']) or string_none_or_empty(
        request.form['parent_artifact_id']):
        return jsonify({"status": "Empty arguments"}), 400

    parent_artifact = get_artifact_by_id(int(request.form['parent_artifact_id'].strip()))
    if parent_artifact is None:
        return jsonify({"status": "invalid parent artifact"}), 400

    labeling_data = request.form['labeling_data'].strip()
    label_description = (request.form['label_description'] or '').strip()
    remark = request.form['remark'].strip() if not string_none_or_empty(request.form['remark']) else None
    duration_sec = int(request.form['duration'])
    artifact_id = add_artifacts([request.form['artifact_txt'].strip()], parent_artifact.identifier, who_is_signed_in())
    status = label_artifact(artifact_id[0], labeling_data, label_description, remark, duration_sec, who_is_signed_in())
    return jsonify({"status": f"{status}"})


@app.route('/get_label_description/<label_data>', methods=['GET'])
@login_required
def get_label_description(label_data: str):
    label_data = (label_data or '').strip()
    description = db.session.execute(
        select(LabelingData.label_description).where(LabelingData.labeling == label_data)).scalar()
    return description or ''


@app.route('/label_management', methods=['GET'])
@login_required
def label_management_view():
    all_labels = get_all_labels()
    return render_template('labeling_pages/label_management.html', all_labels=all_labels)


@app.route('/label_management/create_or_update_label', methods=['POST'])
@login_required
def create_or_update_label():
    lid = request.form['id']
    new_label_name = request.form['label']
    new_description = request.form['description']
    if string_none_or_empty(new_label_name) or string_none_or_empty(new_description):
        return jsonify({"status": "Empty arguments"}), 400

    try:
        lbl = get_label_by_id(int(lid))
        get_or_create_label_with_text(new_label_name, new_description, who_is_signed_in()) if lbl is None \
            else update_label(lid, new_label_name, new_description)
        status = 'success'
        msg = "saved successfully"
    except (ValueError, Exception) as e:
        status = 'error'
        msg = str(e)

    return (jsonify({"status": msg}), 200) if status == 'success' \
        else (jsonify({"status": msg}), 400)


@app.route('/label_management/delete_label/<label_id>', methods=['DELETE'])
@login_required
def remove_label_by_id(label_id):
    if request.method != 'DELETE':
        return "Not DELETE!", 400
    if string_none_or_empty(label_id):
        return "parameter empty", 400

    label_id = int(label_id)
    try:
        delete_label(label_id)
    except ValueError as e:
        return jsonify({"status": str(e)}), 400

    return jsonify({"status": "deleted successfully!"}), 200


@app.route('/label_management/merge_label', methods=['GET'])
@login_required
def merge_labels_view():
    return render_template('labeling_pages/merge_label.html', labels=get_all_labels())


@app.route('/label_management/merge_label', methods=['POST'])
@login_required
def merge_labels():
    old_label_names = list(filter(lambda i: not string_none_or_empty(i), request.form.getlist('labelNames[]') or []))
    new_label_txt = request.form['newLabel']
    new_label_description = request.form['newLabelDescription'] or ''
    remark = request.form['remark'] or ''

    if string_none_or_empty(new_label_txt) or len(old_label_names) < 2:
        return jsonify({'status': 'parameters are not valid'}), 400

    if get_label(new_label_txt) is not None:
        return jsonify({'status': f'label "{new_label_txt}" already exists'}), 400

    old_labels = [get_label(lbl) for lbl in old_label_names]

    new_label_description += '[Merged: ' + '. '.join(
        [f'{lbl.labeling} ({lbl.label_description}) [{lbl.created_by}]' for lbl in old_labels]) + ']'
    labelled_artifacts = itertools.chain(*[get_artifacts_with_label(lbl) for lbl in old_label_names])
    for art in labelled_artifacts:
        label_artifact(art.id, new_label_txt, new_label_description, remark, 0, who_is_signed_in())

    return jsonify({'status': f'merged labels: {", ".join(old_label_names)}'})


@app.route("/labels", methods=['GET'])
@login_required
def labels():
    all_labels = LabelingData.query.with_entities(LabelingData.labeling, LabelingData.id).all()
    return render_template('common_pages/labels.html', all_labels=all_labels)
