#!flask/bin/python

from datetime import datetime
from datetime import timedelta
import os

from flask import Flask, jsonify, abort, make_response, request
from flask_sqlalchemy import SQLAlchemy
from celery import Celery


BASEDIR = os.path.abspath(os.path.dirname(__file__))
DB_NAME = 'data.sqlite'
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASEDIR, DB_NAME)
NUM_OF_ASYNC_TASKS = 20     # arbitrary number of tasks to be sent to celery worker


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True  # enable auto commits on the end of each request
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379',
    CELERYBEAT_SCHEDULE={
        'run-every-15-seconds': {
            'task': 'api_1_0.app.create_random_contact',
            'schedule': timedelta(seconds=15)
        },
        'run-every-1-minute': {
            'task': 'api_1_0.app.remove_old_contacts',
            'schedule': timedelta(minutes=1)
        },
    }
)

db = SQLAlchemy(app)


# TODO move the model definitions to their own module
class Contact(db.Model):
    __tablename__ = 'contacts'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), nullable=False, unique=True, index=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    created_on = db.Column(db.DateTime, default=datetime.now())   # FIXME: bug showing showing same time for all records
    updated_on = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())    # FIXME didnt't seem to auto update
    emails = db.relationship('Email', backref='contact')

    def __repr__(self):
        return '<Contact %r>' % self.username


class Email(db.Model):
    __tablename__ = 'emails'
    id = db.Column(db.Integer, primary_key=True)
    email_addr = db.Column(db.String(50), nullable=False, unique=True, index=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'))

    def __repr__(self):
        return '<Email %r>' % self.email_addr


def make_celery(application):
    celery = Celery(
        application.import_name,
        backend=application.config['CELERY_RESULT_BACKEND'],
        broker=application.config['CELERY_BROKER_URL']
    )
    celery.conf.update(application.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with application.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = make_celery(app)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


@app.errorhandler(409)
def conflict(error):
    return make_response(jsonify({'error': 'Unique constraint failed'}), 409)


@app.route('/')
def index():
    return '<h1>Welcome to a simple contacts api</h1>'


@app.route('/drugdev/api/v1.0/contacts/', methods=['GET'])
def get_contacts():
    contacts = Contact.query  # treat the query as an iterable object
    contacts_info = [
        {
            'id': c.id,
            'username': c.username,
            'first name': c.first_name,
            'last name': c.last_name,
            'created_on': c.created_on,
            'updated_on': c.updated_on,
            'emails_addresses': [obj.email_addr for obj in c.emails]
        } for c in contacts
    ]
    return jsonify({'contacts': contacts_info})


@app.route('/drugdev/api/v1.0/contacts/<string:user_name>', methods=['GET'])
def get_contact_by_username(user_name):
    contact = Contact.query.filter_by(username=user_name).first()
    if contact:
        return jsonify(
            {'contact':
                {
                    'id': contact.id,
                    'username': contact.username,
                    'first name': contact.first_name,
                    'last name': contact.last_name,
                    'created_on': contact.created_on,
                    'updated_on': contact.updated_on,
                    'emails_addresses': [obj.email_addr for obj in contact.emails]
                }
            }
        )
    abort(404)


@app.route('/drugdev/api/v1.0/contacts/<int:user_id>', methods=['GET'])
def get_contact_by_id(user_id):
    contact = Contact.query.filter_by(id=user_id).first()
    if contact:
        return jsonify(
            {'contact':
                {
                    'id': contact.id,
                    'username': contact.username,
                    'first name': contact.first_name,
                    'last name': contact.last_name,
                    'created_on': contact.created_on,
                    'updated_on': contact.updated_on,
                    'emails_addresses': [obj.email_addr for obj in contact.emails]
                }
            }
        )
    abort(404)


@app.route('/drugdev/api/v1.0/contacts/', methods=['POST'])
def create_contact():
    # The request.json will have the request data, but only if it came marked as json
    if not request.json:
        abort(400)

    contact = Contact.query.filter_by(username=request.json['username']).first()
    if contact:
        abort(409)

    # TODO possibly make the email address as a field for new contact
    contact = Contact(username=request.json['username'], first_name=request.json['first_name'],
                      last_name=request.json['last_name'])
    db.session.add(contact)
    db.session.commit()
    return jsonify({'contact': 'created'}), 201


@app.route('/drugdev/api/v1.0/contacts/<string:user_name>', methods=['DELETE'])
def delete_contact_by_username(user_name):
    contact = Contact.query.filter_by(username=user_name).first()
    if contact:
        # check for linked emails to contacts ... (avoid orphaning records in Email table
        emails_deleted = Email.query.filter_by(contact_id=contact.id).delete()
        db.session.delete(contact)
        db.session.commit()
        return jsonify({'contact': 'deleted'}), 200
    abort(404)


@app.route('/drugdev/api/v1.0/contacts/<int:user_id>', methods=['DELETE'])
def delete_contact_by_id(user_id):
    contact = Contact.query.filter_by(id=user_id).first()
    if contact:
        # check for linked emails to contacts ... (avoid orphaning records in Email table
        emails_deleted = Email.query.filter_by(contact_id=contact.id).delete()
        db.session.delete(contact)
        db.session.commit()
        return jsonify({'contact': 'deleted'}), 200
    abort(404)


@app.route('/drugdev/api/v1.0/contacts/<string:user_name>', methods=['PUT'])
def update_contact_by_username(user_name):
    contact = Contact.query.filter_by(username=user_name).first()
    if not contact:
        abort(404)

    if not request.json:
        abort(400)

    if 'username' in request.json and type(request.json['username']) != str:
        abort(400)
    if 'first_name' in request.json and type(request.json['first_name']) != str:
        abort(400)
    if 'last_name' in request.json and type(request.json['last_name']) != str:
        abort(400)
    if 'email' in request.json and type(request.json['email']) != str:
        abort(400)

    contact.username = request.json.get('username', contact.username)
    contact.first_name = request.json.get('first_name', contact.first_name)
    contact.last_name = request.json.get('last_name', contact.last_name)
    contact.updated_on = datetime.now()

    email = request.json.get('email')
    if email:
        contact.emails.append(Email(email_addr=email))

    db.session.add(contact)
    db.session.commit()
    return jsonify({'contact': 'updated'}), 200


# @app.route('/drugdev/api/v1.0/contacts/<int:user_id>', methods=['PUT'])
def update_contact_by_id(user_id):
    # TODO another possibility; use the contact id instead of the contact username
    pass


def delete_email_for_contact():
    # TODO another possible feature
    pass


@celery.task()
def create_random_contact(f_name='foo', l_name='bar'):
    """Task that creates a Contact with random data every n seconds
    """
    # TODO find better way to produce truly random user contact data, for now proof of concept
    try:
        contact = Contact.query[-1]     # get the id of the last record if it exists
        suffix = contact.id + 1
        username = f'{f_name}.{l_name}-{suffix}'
    except IndexError:
        username = f'{f_name}.{l_name}'

    new_contact = Contact(username=username, first_name=f_name, last_name=l_name)
    db.session.add(new_contact)
    db.session.commit()


@celery.task()
def remove_old_contacts():
    """Task removed contacts that are older than 1 minute
    """
    time_diff = datetime.now() - timedelta(minutes=1)
    contacts = Contact.query.filter(Contact.created_on <= time_diff).delete()
    db.session.commit()


if __name__ == '__main__':
    db.drop_all()
    db.create_all()

    # get some starting data in the database ...
    contact1 = Contact(username='foobar', first_name='John', last_name='Gotti')
    contact2 = Contact(username='luckylu', first_name='Lucky', last_name='Luciano')

    email1 = Email(email_addr='j-g@foobar.com')
    email2 = Email(email_addr='jon.gotti.45@yahoo.com')
    contact1.emails.extend([email1, email2])

    email3 = Email(email_addr='lucky.luciano@fubar.com')
    email4 = Email(email_addr='l.luciano_001@fubar.com')
    contact2.emails.extend([email3, email4])

    db.session.add_all([contact1, contact2])
    db.session.commit()

    app.run(debug=True)
