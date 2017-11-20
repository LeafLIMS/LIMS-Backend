# Leaf LIMS: Frontend UI

![Leaf LIMS logo](https://leaflims.github.io/img/logo.svg)

_Leaf LIMS is a laboratory information management system (LIMS) designed to make managing projects
in a laboratory much easier. By using Leaf LIMS you can keep track of almost everything in the
laboratory including samples, results data and even consumable levels._

Leaf LIMS uses [Docker](https://docker.com) to easily bundle all the necessary components into a single package. Setting it up is as simple as downloading the latest release, editing a few configuration files and then running a single command!

**Please note: This is only the backend API for Leaf LIMS. Please see the [Leaf LIMS](https://github.com/LeafLIMS/LeafLIMS) repository for the full system**

## About the backend

The Leaf LIMS backend provides REST API endpoints forwarding with data in the LIMS. Anything that the UI shows comes from this API and all tasks can be formed by sending the correct information to an endpoint. The system is written in Python 3.5 and uses a PostgreSQL 9.5 database for storing data. The endpoints are generated using the [Django Rest Framework](https://http://www.django-rest-framework.org).

## Prerequisites for development

- Python 3 (Developed with Python 3.5)
- PostgreSQL 9 (Developed with PostgreSQL 9.5)

Tested on Linux and Mac OSX, your mileage on Windows my vary.

## Setting up a development environment

- Download this repository to your system
- Create a virtual environment in the directory: `python3 -m venv env`
- Install the dependencies: `env/bin/pip install -r requirements.txt`
- Create a database in postgreSQL. By default this is called "lims", if you may need to change this if you call it something different in the run server file.
- Migrate the database tables: `env/bin/python manage.py migrate` 
- Set up the audit trail tables: `env/bin/python manage.py createinitialrevisions` 
- Create a superuser `env/bin/python manage.py createsuperuser` so you can log in
- Create a run file that contains the correct environmental variables (an example is provided below, this will be referred to by the name "runserver")

```
#!/bin/bash

export DB_NAME lims 

export SALESFORCE_USERNAME='<salesforce username>'
export SALESFORCE_PASSWORD='<salesforce password>'
export SALESFORCE_TOKEN='<salesforce token>'

export PROJECT_IDENTIFIER_PREFIX='P'
export PROJECT_IDENTIFIER_START=100 

export LISTEN_HOST=0.0.0.0
export LISTEN_PORT=8000

env/bin/python manage.py runserver $LISTEN_HOST:$LISTEN_PORT
```

- You will then need to set the executable bit on the file. (e.g. `chmod +x runserver`)
- You can now run `./runserver` (or whatever you called the file) to start the system for development
