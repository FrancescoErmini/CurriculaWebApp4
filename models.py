#!/usr/bin/env python
from flask_sqlalchemy import SQLAlchemy
import datetime

#reference tutorial:
#https://danidee10.github.io/2016/09/19/flask-by-example-2.html

db = SQLAlchemy()

#why use a Base class: https://medium.com/@lsussan/base-classes-one-to-many-relationships-in-flask-sqlalchemy-fba0d47374ad
class Base(db.Model):
    __abstract__ = True
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())


class Admin(Base):
    __tablename__ = 'admin'
    idd = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=True)
    password = db.Column(db.String(300), nullable=False)

    def __init__(self, idd, username, password):
        self.idd = idd
        self.username = username
        self.password = password


class Groups(Base):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    n = db.Column(db.Integer, nullable=False)
    #cfu = db.Column(db.Integer, nullable=True)

    courses = db.relationship('Courses', secondary='groups_courses_association')
    curricula = db.relationship('Curricula', secondary='curricula_groups_association')

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

class Courses(Base):
    __tablename__ = 'courses'
    id = db.Column(db.String(7), primary_key=True) # id = B000001
    name = db.Column(db.String(200), nullable=False)               # name = Analisi Matematica
    cfu = db.Column(db.Integer, nullable=False)
    ssd = db.Column(db.String(10), nullable=False)
    year = db.Column(db.Integer,  nullable=True)
    semester = db.Column(db.Integer, nullable=True)
    url = db.Column(db.String(100), nullable=True)
    ac = db.Column(db.String(9), db.ForeignKey('academicyears.id'))

    def __init__(self, id, name, cfu, ssd):
    	self.id=id
        self.name = name
        self.cfu = cfu
        self.ssd = ssd

class OtherCourses(Base):
    __tablename__ = 'othercourses'
    id = db.Column(db.String(7), primary_key=True) # id = B000001
    name = db.Column(db.String(200), nullable=False)               # name = Analisi Matematica
    cfu = db.Column(db.Integer, nullable=False)
    ssd = db.Column(db.String(10), nullable=False)

    def __init__(self, id, name, cfu, ssd):
        self.id=id
        self.name = name
        self.cfu = cfu
        self.ssd = ssd

class Curricula(Base):
    __tablename__ = 'curricula'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(500), nullable=False)
    ac = db.Column(db.String(9), db.ForeignKey('academicyears.id'))
    desc = db.Column(db.String(2000))

    groups = db.relationship('Groups', secondary='curricula_groups_association')

    def __init__(self, title, ac, desc):
        self.title = title
        self.ac = ac
        self.desc = desc

    def __repr__(self):
        return self.title

class Students(Base):
    __tablename__ = 'students'
    id = db.Column(db.String(7), primary_key=True)
    firstname = db.Column(db.String(20))
    lastname = db.Column(db.String(20))

    #studyplan = db.relationship('Studyplans', backref=db.backref('students', uselist=False))
    studyplan = db.relationship('Studyplans', backref=db.backref('students', uselist=False))

    def __init__(self, id):
        self.id = id
    def __repr__(self):
        return self.id


class Studyplans(Base):
    __tablename__ = 'studyplans'
    id = db.Column(db.String(7), db.ForeignKey('students.id'), primary_key=True)
    curriculum_id = db.Column(db.Integer, db.ForeignKey('curricula.id'))
    
    courses = db.relationship('Courses', secondary='studyplan_courses_association')
    othercourses = db.relationship('OtherCourses', secondary='studyplan_othercourses_association')
    note = db.Column(db.String(2000))

    #backref serve a fare il delete di curriculum senza avere errore di violazione integrita per via della foreign key.
    curriculum = db.relationship('Curricula', backref=db.backref('studyplans', uselist=False))

    def __init__(self, id, curriculum_id):
        self.id = id
        self.curriculum_id = curriculum_id
    def __repr__(self):
        return self.id

class Academicyears(Base):
    __tablename__ = 'academicyears'
    id = db.Column(db.String(9), primary_key=True, nullable=False )
    #start = db.Column(db.DateTime, n)
    #end = db.Column(db.DateTime)

    def __init__(self, id):
    	self.id=id
    def __repr__(self):
        return self.id

#http://docs.sqlalchemy.org/en/latest/orm/basic_relationships.html#many-to-many
groups_courses_association = db.Table('groups_courses_association', Base.metadata,
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id')),
    db.Column('course_id', db.String(7), db.ForeignKey('courses.id',  ondelete='cascade'), nullable=True))

curricula_groups_association = db.Table('curricula_groups_association', Base.metadata,
    db.Column('curriculum_id', db.Integer, db.ForeignKey('curricula.id')),
    db.Column('group_id',  db.Integer, db.ForeignKey('groups.id')))
# ondelete='cascade' allow to delete course_id - studyplan rows when course_id is deleted.
studyplan_courses_association = db.Table('studyplan_courses_association', Base.metadata,
    db.Column('studyplan_id', db.String(7), db.ForeignKey('studyplans.id')),
    db.Column('course_id', db.String(7), db.ForeignKey('courses.id',  ondelete='cascade'), nullable=True))


studyplan_courses_association = db.Table('studyplan_othercourses_association', Base.metadata,
    db.Column('studyplan_id', db.String(7), db.ForeignKey('studyplans.id')),
    db.Column('othercourse_id', db.String(7), db.ForeignKey('othercourses.id',  ondelete='cascade'), nullable=True))