import pytest
import os
import json

from api_1_0.app import app, BASEDIR, db, Contact


TEST_DB_PATH = os.path.join(BASEDIR, 'testing_api.db')
TEST_DATABASE_URI = 'sqlite:///' + TEST_DB_PATH


@pytest.fixture()
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = TEST_DATABASE_URI
    client = app.test_client()
    db.create_all()

    yield client

    db.session.remove()
    db.drop_all()
    if os.path.exists(TEST_DB_PATH):
        os.unlink(TEST_DB_PATH)


class TestContactsAPI(object):
    """Test the endpoints of the Contacts Rest API
    """

    def test_get_contacts(self, client):
        # prepare some existing data in db ...
        contact1 = Contact(username='foobar', first_name='Foo', last_name='Barr')
        db.session.add(contact1)
        db.session.commit()

        response = client.get('/drugdev/api/v1.0/contacts/')
        # response_data = json.loads(response.get_data(as_text=True))
        response_data = response.json
        assert response.status_code == 200
        assert len(response_data['contacts']) == 1
        assert response_data['contacts'][0]['id'] == 1
        assert response_data['contacts'][0]['first name'] == 'Foo'
        assert response_data['contacts'][0]['last name'] == 'Barr'
        assert response_data['contacts'][0]['username'] == 'foobar'
        assert response_data['contacts'][0]['emails_addresses'] == []
        assert 'created_on' in response_data['contacts'][0]
        assert 'updated_on' in response_data['contacts'][0]

    def test_get_contact_by_username(self, client):
        # prepare some existing data in db ...
        contact1 = Contact(username='foobar', first_name='Foo', last_name='Barr')
        db.session.add(contact1)
        db.session.commit()

        response = client.get('/drugdev/api/v1.0/contacts/foobar')
        response_data = response.json
        assert response.status_code == 200
        assert isinstance(response_data, dict)
        assert response_data['contact']['id'] == 1
        assert response_data['contact']['first name'] == 'Foo'
        assert response_data['contact']['last name'] == 'Barr'
        assert response_data['contact']['username'] == 'foobar'
        assert response_data['contact']['emails_addresses'] == []
        assert 'created_on' in response_data['contact']
        assert 'updated_on' in response_data['contact']

    def test_get_contact_by_username_error_not_found(self, client):
        contact1 = Contact(username='foobar', first_name='Foo', last_name='Barr')
        db.session.add(contact1)
        db.session.commit()

        response = client.get('/drugdev/api/v1.0/contacts/fubarX')
        response_data = response.json
        assert response.status_code == 404
        assert response_data['error'] == 'Not found'

    def test_get_contact_by_id(self, client):
        contact1 = Contact(username='foobar', first_name='Foo', last_name='Barr')
        db.session.add(contact1)
        db.session.commit()

        response = client.get('/drugdev/api/v1.0/contacts/1')
        response_data = response.json
        assert response.status_code == 200
        assert isinstance(response_data, dict)
        assert response_data['contact']['id'] == 1
        assert response_data['contact']['first name'] == 'Foo'
        assert response_data['contact']['last name'] == 'Barr'
        assert response_data['contact']['username'] == 'foobar'
        assert response_data['contact']['emails_addresses'] == []
        assert 'created_on' in response_data['contact']
        assert 'updated_on' in response_data['contact']

    def test_get_contact_by_id_error_not_found(self, client):
        contact1 = Contact(username='foobar', first_name='Foo', last_name='Barr')
        db.session.add(contact1)
        db.session.commit()

        response = client.get('/drugdev/api/v1.0/contacts/99')
        response_data = response.json
        assert response.status_code == 404
        assert response_data['error'] == 'Not found'

    def test_create_contact(self, client):
        payload = {
            'username': 'loa.tzu',
            'first_name': 'Loa',
            'last_name': 'Tzu',
        }

        response = client.post(path='/drugdev/api/v1.0/contacts/', data=json.dumps(payload),
                               content_type='application/json')
        assert response.status_code == 201
        assert response.json['contact'] == 'created'

    def test_create_contact_errors(self, client):
        # load some existing data into db ...
        payload = {
            'username': 'loa.tzu',
            'first_name': 'Loa',
            'last_name': 'Tzu',
        }
        response = client.post(path='/drugdev/api/v1.0/contacts/', data=json.dumps(payload),
                               content_type='application/json')
        assert response.status_code == 201
        assert response.json['contact'] == 'created'

        # test: now attempt to create new contact where username already exists
        response = client.post(path='/drugdev/api/v1.0/contacts/', data=json.dumps(payload),
                               content_type='application/json')
        assert response.status_code == 409
        assert response.json['error'] == 'Unique constraint failed'

        # test: payload in unexpected format
        response = client.post(path='/drugdev/api/v1.0/contacts/', data=payload,
                               content_type='application/json')
        assert response.status_code == 400
        assert response.json['error'] == 'Bad request'

    def test_delete_contact_by_username(self, client):
        # prepare some existing data in db ...
        contact1 = Contact(username='foobar', first_name='Foo', last_name='Barr')
        db.session.add(contact1)
        db.session.commit()

        response = client.delete('/drugdev/api/v1.0/contacts/foobar')
        response_data = response.json
        assert response.status_code == 200
        assert response_data['contact'] == 'deleted'

    def test_delete_contact_by_id(self, client):
        # prepare some existing data in db ...
        contact1 = Contact(username='foobar', first_name='Foo', last_name='Barr')
        db.session.add(contact1)
        db.session.commit()

        response = client.delete('/drugdev/api/v1.0/contacts/1')
        response_data = response.json
        assert response.status_code == 200
        assert response_data['contact'] == 'deleted'

    def test_delete_contact_errors(self, client):
        # test: delete non existing username
        response = client.delete('/drugdev/api/v1.0/contacts/foobar')
        response_data = response.json
        assert response.status_code == 404
        assert response_data['error'] == 'Not found'

        # test: delete non existing contact id
        response = client.delete('/drugdev/api/v1.0/contacts/1')
        response_data = response.json
        assert response.status_code == 404
        assert response_data['error'] == 'Not found'

    def test_update_contact_by_username(self, client):
        # prepare some existing data in db ...
        contact1 = Contact(username='foobar', first_name='Foo', last_name='Barr')
        db.session.add(contact1)
        db.session.commit()

        payload = {
            'username': 'foobar-supreme',
            'first_name': 'Loa',
            'last_name': 'Tzu',
            'email': 'lao.tzu.3033@example.com'
        }
        response = client.put(path='/drugdev/api/v1.0/contacts/foobar', data=json.dumps(payload),
                              content_type='application/json')
        response_data = response.json
        assert response.status_code == 200
        assert response_data['contact'] == 'updated'

    def test_update_contact_by_username_errors(self, client):
        # prepare some existing data in db ...
        contact1 = Contact(username='foobar', first_name='Foo', last_name='Barr')
        db.session.add(contact1)
        db.session.commit()

        # test: update for non-existing username
        response = client.put(path='/drugdev/api/v1.0/contacts/fubarX',
                              data=json.dumps({'username': 'FubarX'}),
                              content_type='application/json')
        response_data = response.json
        assert response.status_code == 404
        assert response_data['error'] == 'Not found'

        # test: payload with invalid data type
        response = client.put(path='/drugdev/api/v1.0/contacts/foobar',
                              data=json.dumps({'username': 1001}),
                              content_type='application/json')
        response_data = response.json
        assert response.status_code == 400
        assert response_data['error'] == 'Bad request'
