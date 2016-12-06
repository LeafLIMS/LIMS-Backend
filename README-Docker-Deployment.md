# Deploying Backend with Docker

- First time create the data container (`db_data`): 
   - `docker create -v /var/lib/postgresql/data --name db_data postgres:latest /bin/echo "Data only container for DB"`

- Mount the data container on the postgresql container (`db`): 
   - `docker run -d --name db --volumes-from db_data postgres:latest`

- Build the Backend image (`getlims/lims:v<version>`) from a Dockerfile in the current working directory
   - NB. Edit the Dockerfile first to specify key environment variables e.g. server and port to listen on
   - `docker build --no-cache -t getlims/lims:v<version> .`
   
- Migrate (update) the database and create initial revisions:
   - `docker run -t -i --link db:db getlims/lims:v<version> python manage.py migrate`
   - `docker run -t -i --link db:db getlims/lims:v<version> python manage.py createinitialrevisions`

- First time only, add superuser:
   - `docker run -t -i --link db:db getlims/lims:v<version> python manage.py createsuperuser`

- Run the Backend container (`app`): (NB. Update 8000 to the port number you specified in the Dockerfile ENV settings)
   - `docker run -p 8000:8000 --link db:db --name app -d getlims/lims:v<version>`

- Package Backend image, bundling in GetLIMS-Backend, with references to db image but not including it:
   - `docker save getlims/lims:v<version> > lims.tar`
   
- Load Backend image into Docker production 
   - `docker load -i lims.tar`

- Clean and remove old Backend before deploying new one:
   - `docker stop app`
   - `docker rm app`
   - `docker rmi getlims/lims:v<oldversion>`
