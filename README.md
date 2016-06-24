# GET LIMS

**Please note that this is only the backend API, the frontend for this project is stored in another repository**

GET LIMS is a synthetic biology focused LIMS that allows the tracking of samples, running of workflows and automatic inventory handling.

## Requirements

- Python 3 (Developed with Python 3.5)
- PostgreSQL 9 (Developed with PostgreSQL 9.5)

Tested on Linux and Mac OSX, your mileage on Windows my vary.

## Setting up a development environment

- Download this repository to your system
- Create a virtual environment in the directory: `pyvenv env`
- Install the dependencies: `env/bin/pip install -r requirements.txt`
- Create a database in postgreSQL (called lims for ease)
- Migrate the database tables: `env/bin/python manage.py migrate` 
- Create a superuser `env/bin/python manage.py createsuperuser` so you can log in
- Create a run file that contains the correct environmental variables (an example is provided below)

```
#!/bin/bash

export DB_NAME lims 

export SALESFORCE_USERNAME='<salesforce username>'
export SALESFORCE_PASSWORD='<salesforce password>'
export SALESFORCE_TOKEN='<salesforce token>'

export PROJECT_IDENTIFIER_PREFIX='PROJ'
export PROJECT_IDENTIFIER_START=100 

env/bin/python manage.py runserver
```

# To test

`env/bin/python manage.py runserver`
