from flask import render_template, request, jsonify
from flask_login import login_required

from src import app
from src.database.queries.label_queries import get_labels_without_theme
from src.database.queries.theme_queries import get_all_themes, create_theme, get_theme_by_id, remove_theme, update_theme
from src.helper.tools_common import string_none_or_empty, who_is_signed_in


@app.route('/theme_management', methods=['GET'])
@login_required
def theme_management_view():
    return render_template('theme_pages/theme_management.html', themes=get_all_themes())


@app.route('/theme_management/view_theme/<theme_id>', methods=['GET'])
@login_required
def view_theme_details(theme_id: int):
    theme = get_theme_by_id(theme_id)
    return render_template('theme_pages/theme_view.html', theme=theme)


@app.route('/theme_management/create_theme', methods=['GET'])
@login_required
def theme_create_view():
    labels = get_labels_without_theme()
    return render_template('theme_pages/theme_create.html', labels=labels)


@app.route('/theme_management/create_theme', methods=['POST'])
@login_required
def theme_create_post():
    name = request.form.get('theme', '', str)
    description = request.form.get('description', '', str)
    label_ids = request.form.getlist('label_ids[]', int)

    if string_none_or_empty(name) or string_none_or_empty(description) or len(label_ids) == 0:
        return jsonify({'status': 'Empty arguments'}), 400

    try:
        create_theme(name.strip(), description.strip(), label_ids, who_is_signed_in())
    except (ValueError, Exception) as e:
        return jsonify({'status': str(e)}), 400

    return jsonify({'status': 'theme created'})


@app.route('/theme_management/delete_theme/<theme_id>', methods=['DELETE'])
@login_required
def delete_theme(theme_id: int):
    try:
        remove_theme(theme_id)
    except ValueError as e:
        return jsonify({'status': str(e)}), 400

    return jsonify({'status': 'deleted successfully'})


@app.route('/theme_management/edit_theme/<theme_id>', methods=['GET'])
@login_required
def update_theme_view(theme_id: int):
    theme = get_theme_by_id(theme_id)
    labels_without_theme = get_labels_without_theme()
    return render_template('theme_pages/theme_edit.html', theme=theme, labels_without_theme=labels_without_theme)


@app.route('/theme_management/update_theme/<theme_id>', methods=['PUT'])
@login_required
def update_theme_put(theme_id: int):
    name = request.form.get('name', '', str)
    description = request.form.get('description', '', str)
    label_ids = request.form.getlist('label_ids[]', int)

    if string_none_or_empty(name) or string_none_or_empty(description) or theme_id is None:
        return jsonify({'status': 'empty arguments'}), 400

    try:
        update_theme(theme_id, name, description, label_ids, who_is_signed_in())
    except (ValueError, Exception) as e:
        return jsonify({'status': str(e)}), 400

    return jsonify({'status': 'success'})


@app.route('/theme_management/merge_theme', methods=['GET'])
@login_required
def merge_theme_view():
    return 'NOT IMPLEMENTED', 404
