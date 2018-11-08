
Setup Flask, download project files and install required packages:
```shell
mkdir curriculaWebApp4 && cd curriculaWebApp4
pip install virtualenv
virtualenv env
source env/bin/activate
git init
git clone https://github.com/FrancescoErmini/CurriculaWebApp4.git
export FLASK_APP=app.py
pip install Flask
pip install -r requirements.txt
```
Create Postgres DB, user and password:
```shell
CREATE USER curricula_admin2 WITH PASSWORD 'password';
CREATE DATABASE curricula_db
GRANT ALL PRIVILEGES ON DATABASE curricula_db TO curricula_admin2;
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

Visit the admin page
```shell
http://localhost:5000/admin
```

From the menu, go to 'Admin' and login with 
```shell
username : admin
password : admin

```
Change username and password


