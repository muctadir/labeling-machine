import os
from os import path

from faker import Faker
from werkzeug.security import generate_password_hash
from sqlalchemy_utils.functions import database_exists

from src import app
from src.database.models import *
# Registers 'initdb' cli command.
# Usage: `flask initdb`
from src.database.queries.artifact_queries import add_artifacts
from src.helper.tools_common import string_none_or_empty, read_artifacts_from_file


@app.cli.command('initdb')
def initdb():
    print("Creating DB. ", end='')
    if not database_exists(app.config['SQLALCHEMY_DATABASE_URI']):
        db.create_all(app=app)  # SQLAlchemy: creates tables defined in `models.py` (only if do not exist)
        print("\t[SUCCESS]")
        initialize_database()
    else:
        # TODO: run db migrations
        print("DB already exists. [SKIP]")


def init_users():
    print("Initializing default users. ", end='')
    env_pass_key = 'API_PASSWORD'
    password = os.environ.get(env_pass_key)

    if string_none_or_empty(password):
        raise ValueError(f'"{env_pass_key}" environment variable for default password is empty.')

    password = generate_password_hash(password, method='sha256')
    db.session.add(User(username='hossain', password=password, gender='male', education='PhD', occupation='',
                        affiliation='TU/e', years_xp=0))
    db.session.add(User(username='david', password=password, gender='male', education='PhD', occupation='',
                        affiliation='TU/e', years_xp=0))
    db.session.add(User(username='raghav', password=password, gender='male', education='PhD', occupation='',
                        affiliation='TiU', years_xp=0))
    db.session.add(User(username='admin', password=password, gender='male', education='Masters', occupation='',
                        affiliation='TU/e', years_xp=0))
    db.session.commit()
    print("\t[SUCCESS]")


def initialize_database():
    init_users()
    import_dummy_data()


def import_dummy_data():
    if not app.env == 'production':
        print("Loading dummy artifacts ...", end='')
        sample_file = './db/sample.txt'
        text = []
        if path.exists(sample_file):
            with open(sample_file) as f:
                read_artifacts_from_file(f)
        else:
            print(f'No file at {sample_file}. Uploading random value with Faker.', end='')
            fake = Faker()
            text = [fake.paragraph(15) for _ in range(100)]

        add_artifacts(text, 'admin')
        print("\t[SUCCESS]")
    else:
        print(f'No dummy data loaded. Application is running in {str.upper(app.env)} mode!!!')
