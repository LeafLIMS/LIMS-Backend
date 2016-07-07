# Deploying Backend with Docker

- First time create the data container (`db_data`):
   - `docker create -v /var/lib/postgresql/data --name db_data postgres:latest /bin/echo "Data only container for DB"`

- Mount the data container on the postgresql container (`db`): 
   - `docker run -d --name db --volumes-from db_data postgres:latest`

- Build the Backend image (`getlims/lims:v<version>``) from a Dockerfile in the current working directory
- NB. Edit the Dockerfile first to specify key environment variables
   - `docker build --no-cache -t getlims/lims:v<version> .`
- Run the Backend container (`app`)
   - `docker run -p 8000:8000 --link db:db --name app -d getlims/lims:v<version>``

- First time add superuser:
   - `docker run -t -i --link db:db getlims/lims:v<version> python manage.py createsuperuser`

- Package Backend image, bundling in GetLIMS-Backend, with references to db image but not including it:
   - `docker save app > lims.tar`
   - `docker save getlims/lims:v<version> > lims.tar`
   - `docker load -i lims.tar`

- Clean and remove old Backend before deploying new one:
   - `docker stop app`
   - `docker rm app`
   - `docker rmi getlims/lims:v<oldversion>``
