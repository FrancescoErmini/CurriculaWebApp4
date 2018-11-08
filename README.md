
Setup Flask, download project files and install required packages:
```shell
mkdir curriculaWebApp && cd curriculaWebApp
pip install virtualenv
virtualenv env
source env/bin/activate
git init
git clone https://github.com/FrancescoErmini/CurriculaWebApp2.git
export FLASK_APP=app.py
pip install Flask
pip install -r requirements.txt
```
Create Postgres DB, user and password:
```shell
CREATE USER my_user WITH PASSWORD 'my_password';
CREATE DATABASE pianodistudio2;
GRANT ALL PRIVILEGES ON DATABASE my_database TO my_user;
```
Change configuration data in app.py:
```shell
POSTGRES = {
    'user': 'my_user',
    'pw': 'my_password',
    'db': 'my_database',
    'host': 'localhost',
    'port': '5432',
}

app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://%(user)s:\
%(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES
```

Within the virtual environment
```shell
python manage.py db init
python manage.py db migrate
python manage.py db upgrade
python manage.py runserver
```

Once the server is running, try to send a 'application/JSON' POST request i.e create a new academic year:
```shell
curl --header "Content-Type: application/json" --anyauth --user admin:admin --request POST --data '{"id":"2019-2020", "start": "Mon, 03 Sep 2019 00:00:00 GMT", "end": "Mon, 02 Sep 2020 00:00:00 GMT"}' \http://localhost:5000/academicyear/
```
Notice 1: all the curl commands for all CRUD operations are listed in:

https://github.com/FrancescoErmini/CurriculaWebApp2/blob/master/utility/curl.txt

Notice 2: A csv parser and it's file are available under the directory `/utility/`
```python
python parser.py
```

Admin GUI open is accessible at: 

https://github.com/FrancescoErmini/CurriculaWebApp2/blob/master/client/index.html

Student GUI is accessible at: 

https://github.com/FrancescoErmini/CurriculaWebApp2/blob/master/client/admin/index.html


Note on TODO

https://stackoverflow.com/questions/26868372/calling-rest-api-from-the-same-server

https://help.parsehub.com/hc/en-us/articles/217751808-API-Tutorial-How-to-get-run-data-using-Python-Flask

