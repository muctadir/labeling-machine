from flask import render_template
from flask_login import login_required

from src import app
from src.database.queries.label_queries import get_all_labels
from src.database.queries.theme_queries import get_all_themes


@app.route('/theme_management', methods=['GET'])
@login_required
def theme_management_view():
    return render_template('theme_pages/theme_management.html', themes=get_all_themes())


# @app.route('/theme_management/create', methods=['GET'])
# @login_required
# def theme_create_view():
#     all_labels = get_all_labels()
#     return render_template('theme_pages/theme_create.html', all_labels=all_labels)


@app.route('/theme_management/delete_theme/<theme_id>', methods=['DELETE'])
@login_required
def delete_theme(theme_id: int):
    pass
