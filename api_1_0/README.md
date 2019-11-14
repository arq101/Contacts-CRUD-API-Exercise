# A basic Flask based RESTful API to expose contact information.


## Contacts API:

This API allows you to create, retrieve, update and delete contacts.


## Set up your virtualenv with Python 3.7

Assuming virtualenv is already installed on your system.  
If using a virtualenvwrapper then set up a virtual environment for this project 
eg.
```
mkvirtualenv -p /usr/bin/python3.7 -a <path to project> <virtualenv name>
```

Once your virtualenv is active, from the project root dir install the necessary dependencies

```
pip install -r api_1_0/requirements.txt
```

## Run unittests
eg. Run unittests for the endpoints in the API. From the root directory run ...
```
python -m pytest -v api_1_0/test_app.py 
```


## Running the API
In the project's root directory run the application from a terminal ...
```
python ./api_1_0/app.py
```

## List all contacts
open a terminal and run ...  
(assuming curl is already installed)
```
curl -i localhost:5000/drugdev/api/v1.0/contacts/
```

## View a specific contact
eg. contact with id 2
```
curl -i localhost:5000/drugdev/api/v1.0/contacts/2
```
or contact with username luckylu
```
curl -i localhost:5000/drugdev/api/v1.0/contacts/luckylu
```

## Add a new contact
eg. basic contact user details ...
```
curl -i -H "Content-Type: application/json" -X POST -d '{"username": "jdillinger", "first_name": "John", "last_name": "Dillinger"}' localhost:5000/drugdev/api/v1.0/contacts/
```

## Update a contact
eg. update contact details for username foobar with new username and new email address
```
curl -i -H "Content-Type: application/json" -X PUT -d '{"username":"jgotti", "email":"jon.gotti@example.com"}' localhost:5000/drugdev/api/v1.0/contacts/foobar
```

## Delete a contact
eg. delete contact with username jgotti
```
curl -i -H "Content-Type: application/json" -X DELETE localhost:5000/drugdev/api/v1.0/contacts/jgotti
```
or alternatively delete the contact via its id 1
```
curl -i -H "Content-Type: application/json" -X DELETE localhost:5000/drugdev/api/v1.0/contacts/1
```

## Run Asynchronous functionality
Creates new contacts every 15 seconds and removes contacts that are older than 1 minute.

Ensure the Flask api is running in a terminal. 
   
Assuming Redis is already installed.   
To start Redis run ...
```
sudo systemctl start redis 
```

Check the status of Redis run ...
```
sudo systemctl status redis
```   

From the project root directory, open a new terminal with an activated venv   
and run a celery worker

```
celery -A api_1_0.app.celery worker -l info 
```

in another terminal run celery beat 

```
celery -A api_1_0.app.celery beat -l info
```
  
  
example log snippet of celery beat ... 
```
[2019-09-19 00:16:18,295: INFO/MainProcess] beat: Starting...
[2019-09-19 00:16:33,365: INFO/MainProcess] Scheduler: Sending due task run-every-15-seconds (api_1_0.app.create_random_contact)
[2019-09-19 00:16:48,353: INFO/MainProcess] Scheduler: Sending due task run-every-15-seconds (api_1_0.app.create_random_contact)
[2019-09-19 00:17:03,356: INFO/MainProcess] Scheduler: Sending due task run-every-15-seconds (api_1_0.app.create_random_contact)
[2019-09-19 00:17:18,306: INFO/MainProcess] Scheduler: Sending due task run-every-1-minute (api_1_0.app.remove_old_contacts)
[2019-09-19 00:17:18,356: INFO/MainProcess] Scheduler: Sending due task run-every-15-seconds (api_1_0.app.create_random_contact)
[2019-09-19 00:17:33,358: INFO/MainProcess] Scheduler: Sending due task run-every-15-seconds (api_1_0.app.create_random_contact)
``` 
example log snippet of the celery worker ...
```
[2019-09-19 00:16:33,385: INFO/MainProcess] Received task: api_1_0.app.create_random_contact[70ac6976-7c14-475c-8dd2-224baf9fd826]  
[2019-09-19 00:16:33,432: INFO/ForkPoolWorker-4] Task api_1_0.app.create_random_contact[70ac6976-7c14-475c-8dd2-224baf9fd826] succeeded in 0.04527460600002087s: None
[2019-09-19 00:16:48,362: INFO/MainProcess] Received task: api_1_0.app.create_random_contact[b64c8acc-99f8-4415-99b6-67809b6f63fa]  
[2019-09-19 00:16:48,489: INFO/ForkPoolWorker-3] Task api_1_0.app.create_random_contact[b64c8acc-99f8-4415-99b6-67809b6f63fa] succeeded in 0.12416611700245994s: None
[2019-09-19 00:17:03,364: INFO/MainProcess] Received task: api_1_0.app.create_random_contact[001c8a8e-6a89-478b-9516-33142f168fb1]  
[2019-09-19 00:17:03,395: INFO/ForkPoolWorker-4] Task api_1_0.app.create_random_contact[001c8a8e-6a89-478b-9516-33142f168fb1] succeeded in 0.02803297300124541s: None
[2019-09-19 00:17:18,312: INFO/MainProcess] Received task: api_1_0.app.remove_old_contacts[34110e9a-c2fa-49ae-9cc1-412139854219]  
[2019-09-19 00:17:18,359: INFO/MainProcess] Received task: api_1_0.app.create_random_contact[0d409816-f366-44ec-85e6-9114a298ac5d]  
[2019-09-19 00:17:18,385: INFO/ForkPoolWorker-3] Task api_1_0.app.remove_old_contacts[34110e9a-c2fa-49ae-9cc1-412139854219] succeeded in 0.07038619900049525s: None
[2019-09-19 00:17:18,415: INFO/ForkPoolWorker-4] Task api_1_0.app.create_random_contact[0d409816-f366-44ec-85e6-9114a298ac5d] succeeded in 0.05528545699780807s: None
[2019-09-19 00:17:33,365: INFO/MainProcess] Received task: api_1_0.app.create_random_contact[90ac0021-03d1-4a18-8941-dca995e6f5a3] 
```
