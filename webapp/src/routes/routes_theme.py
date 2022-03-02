from typing import List

from flask import render_template, request, jsonify
from flask_login import login_required

from src import app
from src.database.queries.label_queries import get_all_labels, get_labels_without_theme
from src.database.queries.theme_queries import get_all_themes, create_theme, get_theme_by_id, remove_theme
from src.helper.tools_common import string_none_or_empty, who_is_signed_in


@app.route('/theme_management', methods=['GET'])
@login_required
def theme_management_view():
    return render_template('theme_pages/theme_management.html', themes=get_all_themes())


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
