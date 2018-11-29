import json
import os
import sys
import string
import pdfkit
from functools import wraps

import click
from flask import Flask, jsonify, render_template, url_for, request, redirect, flash, abort, make_response
from flask_simplelogin import SimpleLogin, login_required
from werkzeug.security import check_password_hash, generate_password_hash

from models import  db, Curricula, Courses, Groups, Admin, Academicyears, Students, Studyplans, OtherCourses
from os import environ

from flask_simplelogin import SimpleLogin, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

'''

SEZIONE CONFIGURAZIONE


Nota: configurare l'app in accordo ai dati del db.

CREATE USER curricula_admin2 WITH PASSWORD 'password';

CREATE DATABASE curricula_db2
GRANT ALL PRIVILEGES ON DATABASE curricula_db2 TO curricula_admin2;

'''

POSTGRES = {
    'user': 'curricula_admin2',
    'pw': 'password',
    'db': 'curricula_db',
    'host': 'localhost',
    'port': '5432',
}

app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://%(user)s:\
%(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES

def validate_login(user):
    #value retrived from simple-login page at /login
    username = user['username']
    password = user['password']
    admin = Admin.query.get(0)
    if  admin.username != username:
        return False
    if check_password_hash(admin.password, password):
        return True
    return False

SimpleLogin(app, login_checker=validate_login)

db.init_app(app)
db.create_all(app=app)



@app.before_request
def init_user_password():
    
    if  Admin.query.get(0) is None:
        
        username = 'admin'
        password = generate_password_hash('admin', method='pbkdf2:sha256')
        admin = Admin(idd=0, username=username, password=password) 
        db.session.add(admin) 
        db.session.commit()     
        print "Warning: change user and password after first boot. default is admin:admin\n" 

    else:
        pass
        '''
        admin = Admin.query.get(0)
        admin.username = 'admin'
        admin.password = generate_password_hash('admin',  method='pbkdf2:sha256')
        db.session.commit()
        '''






##################################  SEZIONE STUDENTE #############################################




@app.route('/', methods=['GET'])
def curricula():   
    curricula = Curricula.query.all()
    validCurricula = []
    for curriculum in curricula:
        if isValidCurriculum(curriculum):
            validCurricula.append(curriculum)
    return render_template('curricula.html', curricula=validCurricula) 

@app.route('/curriculum/<int:curriculum_id>', methods=['GET','POST'])
def curriculum(curriculum_id):
    if request.method == 'GET':
        curriculum = Curricula.query.get(curriculum_id)
        valid_curriculum = isValidCurriculum(curriculum)
        groups = curriculum.groups
        courses = db.session.query(Courses).filter(Courses.cfu==6).all()
        return render_template('curriculum.html', curriculum=curriculum, groups = groups, courses=courses, valid_curriculum=valid_curriculum)
    
    if request.method == 'POST':

        student = createStudent(student_id=request.form['student'], student_firstname = request.form['firstname'], student_lastname = request.form['lastname'] )
        studyplan = createStudyplan(studyplan_id=request.form['student'], curriculum_id=curriculum_id )
        studyplan.student = student
        studyplan.note = request.form['note']

        for course_id in request.form.getlist("course_id[]"):
            course = Courses.query.get(course_id)
            studyplan.courses.append(course)

        if request.form['course1'] == "":
            othercourse1 = createOthercourse(request.form['othercourse1_id'], request.form['othercourse1_name'], request.form['othercourse1_cfu'], request.form['othercourse1_ssd'] )
            othercourse1.note=request.form['othercourse1_note']
        else:
            course1 = Courses.query.get(request.form['course1'])
            othercourse1 = createOthercourse(course1.id, course1.name, course1.cfu, course1.ssd)

        if request.form['course2'] == "":
            othercourse2 = createOthercourse(request.form['othercourse2_id'], request.form['othercourse2_name'], request.form['othercourse2_cfu'], request.form['othercourse2_ssd'] )
            othercourse2.note=request.form['othercourse2_note']
        else:
            course2 = Courses.query.get(request.form['course2'])
            othercourse2 = createOthercourse(course2.id, course2.name, course2.cfu, course2.ssd)

       

        studyplan.othercourses.append(othercourse1)
        studyplan.othercourses.append(othercourse2)
        
        if not isValidStudyplan(studyplan) or not isValidStudent(student):
            return redirect(url_for('curriculum', curriculum_id=curriculum_id))

        db.session.add(student)
        db.session.add(studyplan)
        db.session.commit()
        return redirect('/studyplan/'+str(studyplan.id))
  
@app.route('/studyplan/<string:studyplan_id>', methods=['GET','POST'])
def studyplan(studyplan_id):
    studyplan = Studyplans.query.get(studyplan_id)
    student = Students.query.get(studyplan_id)
    studyplanDoc = render_template('studyplan.html', studyplan=studyplan, student=student)
    pdf = pdfkit.from_string(studyplanDoc, False)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=pianodistudi.pdf' 
    return response



def createStudyplan(studyplan_id, curriculum_id):   
    #Studyplan_id is equals to student_id
    if Studyplans.query.get(studyplan_id) is None:
        studyplan = Studyplans(id=studyplan_id, curriculum_id=curriculum_id)
    else:
        studyplan = Studyplans.query.get(studyplan_id)
    return studyplan


def createStudent(student_id, student_firstname, student_lastname):

    if Students.query.get(student_id) is None:
        student = Students(id=student_id)
        student.firstname = student_firstname
        student.lastname = student_lastname
    else:
        student = Students.query.get(student_id)

    return student

def createOthercourse(othercourse_id, othercourse_name, othercourse_cfu, othercourse_ssd):
    # se il corso e' stato selezionato dalla lista lo si recupera altrimenti lo si crea. 
    if OtherCourses.query.get(othercourse_id) is None:
        othercourse = OtherCourses(id=othercourse_id, name=othercourse_name, cfu=othercourse_cfu, ssd=othercourse_ssd)
    else:
        othercourse = OtherCourses.query.get(othercourse_id)
        othercourse.name = othercourse_name
        othercourse.cfu = othercourse_cfu
        othercourse.ssd = othercourse_ssd
    return othercourse


#########################################   SEZIONE ADMIN  ##################################################



#Home
@app.route('/admin', methods=['GET'] )
def admin():

    check_validation = dict()
    studyplan_counter = dict()

    curricula = Curricula.query.all()
    groups = Groups.query.all()
    studyplans = Studyplans.query.all()

    studyplan_tot = len(studyplans)

    for studyplan in studyplans:
        try:
            studyplan_counter[studyplan.curriculum_id] = studyplan_counter[studyplan.curriculum_id] + 1
        except Exception as e:
            studyplan_counter[studyplan.curriculum_id] = 0

    for curriculum in curricula:
        if not isValidCurriculum(curriculum):
            check_validation[curriculum.title] = False
        else:
            check_validation[curriculum.title] = True

    for group in groups:
        if not isValidGroup(group):
            check_validation[group.name] = False
        else:
            check_validation[group.name] = True
    return render_template('admin/index.html', curricula=curricula, groups = groups, check_validation = check_validation,  studyplan_counter=studyplan_counter, studyplan_tot=studyplan_tot) 
    
#change username and  passord
@app.route('/admin/passwd', methods=['GET','POST'])
@login_required
def change_user_password():
    if request.method == 'GET':
        return render_template('admin/passwd.html')
    elif request.method == 'POST':
        admin = Admin.query.get(0)
        if check_password_hash(admin.password, request.form['oldpassword']):
            admin.username = request.form['newusername']

            if request.form['newpassword'] != request.form['newpassword2']:
                return 'Errore. Le nuove password inserite non coincidono'
            admin.password = generate_password_hash(request.form['newpassword'],  method='pbkdf2:sha256')
            db.session.commit()
            return ' Nuove credenziali settate con Successo'
        else:
            return 'Errore. Vecchia password non corretta'


'''

Academicyear

'''

@app.route('/admin/academicyear/index', methods=['GET'])
def indexAcademicyear():
    academicyears = Academicyears.query.all()
    return render_template('admin/academicyear/index.html', academicyears=academicyears)

@app.route('/admin/academicyear/delete/<string:academicyear_id>', methods=['GET','POST'])
@login_required
def deleteAcademicyear(academicyear_id):
    if request.method == 'GET':
        academicyear = Academicyears.query.get(academicyear_id)
        return render_template('admin/academicyear/delete.html', academicyear=academicyear)
    elif request.method == 'POST':
        if request.form['delete'] == 'delete':
            academicyear = Academicyears.query.get(academicyear_id)
            if academicyear is None:
                return 'academic year not exist'
            db.session.delete(academicyear)
            db.session.commit()
            return redirect(url_for('indexAcademicyear'))

        elif request.form['delete'] == 'undo':
            return redirect(url_for('indexAcademicyear'))
        else:
            return 'error: unknown action'

@app.route('/admin/academicyear/create', methods=['GET','POST'])
@login_required
def createAcademicyear():
    if request.method == 'GET':
        return render_template('admin/academicyear/create.html')
    elif request.method == 'POST':
        academicyear_id = request.form['id']
        if Academicyears.query.get(academicyear_id) is None:
            academicyear = Academicyears(id=academicyear_id)
            if isValidAcademicyear(academicyear):
                db.session.add(academicyear)
                db.session.commit()
        return redirect(url_for('indexAcademicyear'))


'''

Courses

'''
@app.route('/admin/course/index', methods=['GET'])
def indexCourse():
    courses=Courses.query.all()
    return render_template('admin/course/index.html', courses=courses)

@app.route('/admin/course/delete/<string:course_id>', methods=['GET','POST'])
@login_required
def deleteCourse(course_id):
    if request.method == 'GET':
        course = Courses.query.get(course_id)
        return render_template('admin/course/delete.html', course = course)
    elif request.method == 'POST':
        if request.form['delete'] == 'delete':
            course = Courses.query.get(course_id)
            db.session.delete(course)
            db.session.commit()
            return redirect(url_for('indexCourse'))
        elif request.form['delete'] == 'undo':
            return redirect(url_for('indexCourse'))
        else:
            return 'error: unknown action'
@app.route('/admin/course/create', methods=['GET', 'POST'])
@login_required
def createCourse():
    if request.method == 'GET':
        academicyears = Academicyears.query.all()
        return render_template('admin/course/create.html', academicyears=academicyears)
    elif request.method == 'POST':
         #get and validate input params
        course_id = request.form['id']
        course_name = request.form['name']
        course_cfu = request.form['cfu']
        course_ssd = request.form['ssd']
        course_year = request.form['year']
        course_semester = request.form['semester']
        course_url = request.form['url']
        course_ac = request.form['academicyear']
        course = Courses(id=course_id, name=course_name, cfu=course_cfu, ssd=course_ssd)
        course.year = course_year
        course.semester = course_semester
        course.url = course_url
        course.ac = course_ac
        if isValidCourse(course):
            db.session.add(course)
            db.session.commit()
        return redirect(url_for('indexCourse'))

# Parser del csv dei corsi
@app.route('/admin/parser', methods=['GET','POST'])
@login_required
def createCoursesFromCsvParser():
    if request.method == 'GET':
        academicyears = Academicyears.query.all();
        return render_template('admin/course/parser.html', academicyears=academicyears)
    else:
        csvfile = open("csv/corsi.csv", "r") 
        csvfile.readline() 
        print("::::: parsing courses :::::")
        msg = ""
        course_counter = 0

        # column of interest from csv
        # 3 = course code | 4 = name | 5 = ssd | 6  = cfu | 0 = year | 1 = semester
        for line in csvfile:
            row = line.split(";")
            course_counter += 1

            if row[4] != "PROVA FINALE " and row[4] != "LABORATORIO/TIROCINIO ":
                
                #remove last empty char from parsed strings
                id = row[3]
                id = id[:-1]
                ssd = row[5]
                ssd = ssd[:-1]
                name = row[4]
                name = name[:-1]
                semester = int(row[1])
                cfu = int(row[6])
                year = int(row[0])
                url = "#"
                ac = request.form['academicyear']


                if Courses.query.get(id) is None:
                    course = Courses(id=id, name=name, cfu=cfu, ssd=ssd)
                    db.session.add(course)
                else:
                    course = Courses.query.get(id)
                    course.name = name
                    course.cfu = cfu
                    course.ssd = ssd

                course.year = year
                course.semester = semester
                course.url = url
                course.ac = ac

                if OtherCourses.query.get(id) is None:
                    othercourse = OtherCourses(id=id, name=name, cfu=cfu, ssd=ssd)
                    db.session.add(othercourse)
                else:
                    othercourse = OtherCourses.query.get(id)
                    othercourse.name = name
                    othercourse.cfu = cfu
                    othercourse.ssd = ssd

                db.session.commit()
        return redirect(url_for('indexCourse'))  

'''

Groups

'''

@app.route('/admin/group/index', methods=['GET'])
def indexGroup():
    groups = Groups.query.all()
    return render_template('admin/group/index.html', groups = groups)

@app.route('/admin/group/read/<int:group_id>', methods=['GET'])
def readGroup(group_id):
    group = Groups.query.get(group_id)
    return render_template('admin/group/read.html', group=group)

@app.route('/admin/group/delete/<int:group_id>', methods=['GET','POST'])
@login_required
def deleteGroup(group_id):
    if request.method == 'GET':
        group = Groups.query.get(group_id)
        return render_template('admin/group/delete.html',group=group )
    elif request.method == 'POST':
        if request.form['delete'] == 'delete':
            group = Groups.query.get(group_id)
            db.session.delete(group)
            db.session.commit()
            return redirect(url_for('indexGroup'))
        elif request.form['delete'] == 'undo':
            return redirect(url_for('indexGroup'))
        else:
            return 'error: unknown action'

@app.route('/admin/group/create', methods=['GET','POST'] )
@login_required
def createGroup():
    if request.method == 'GET':
        courses = Courses.query.all()
        return render_template('admin/group/create.html', courses = courses)
    else:
        #get and validate input params
        group_name = request.form['name']
        group_n = request.form['n']
        #group_cfu = request.form['cfu']
        group_courses_id = request.form.getlist("course_id[]")
        #create Group obj and append courses objs
        group = Groups(name=group_name)
        group.n = int(group_n)
        # group.cfu = group_cfu
        for course_id in group_courses_id:
            course = Courses.query.get(course_id)
            group.courses.append(course)

        if isValidGroup(group):
            db.session.add(group)
            db.session.commit()
        return redirect(url_for('indexGroup'))


'''


Curricula


'''

@app.route('/admin/curriculum/index', methods=['GET'])
def indexCurriculum():
    curricula = Curricula.query.all()
    return render_template('admin/curriculum/index.html', curricula=curricula)

@app.route('/admin/curriculum/read/<int:curriculum_id>', methods=['GET'])
def readCurriculum(curriculum_id):
    curriculum = Curricula.query.get(curriculum_id)
    return render_template('admin/curriculum/read.html', curriculum=curriculum)

@app.route('/admin/curriculum/delete/<int:curriculum_id>', methods=['GET','POST'])
@login_required
def deleteCurriculum(curriculum_id):
    if request.method == 'GET':
        curriculum = Curricula.query.get(curriculum_id)
        return render_template('admin/curriculum/delete.html', curriculum=curriculum)
    elif request.method == 'POST':
        if request.form['delete'] == 'delete':
            curriculum = Curricula.query.get(curriculum_id)
            try:
                db.session.delete(curriculum)
                db.session.commit()
                #db.session.flush()
            except IntegrityError as e:
                db.session.rollback()
                flash("Errore. Non puoi cancellare il curriculum. E' ancora presente in qualche piano di studi")
            return redirect(url_for('indexCurriculum'))
        elif request.form['delete'] == 'undo':
            return redirect(url_for('indexCurriculum'))
        else:
            return 'error: unknown action'

@app.route('/admin/curriculum/create', methods=['GET','POST'])
@login_required
def createCurriculum():
    if request.method == 'GET':
        groups = Groups.query.all()
        academicyears = Academicyears.query.all()
        return render_template('admin/curriculum/create.html', groups=groups, academicyears=academicyears)
    else:
        curriculum_title = request.form['title']
        curriculum_ac = request.form['academicyear']
        curriculum_desc = request.form['desc']
        curriculum_groups_id = request.form.getlist("group_id[]")
        curriculum = Curricula(title=curriculum_title, ac=curriculum_ac, desc=curriculum_desc)
        for group_id in curriculum_groups_id:
            group = Groups.query.get(group_id)
            curriculum.groups.append(group)
        #validate obj
        if isValidCurriculum(curriculum):
            db.session.add(curriculum)
            db.session.commit()    
        return redirect(url_for('indexCurriculum')) 

@app.route('/admin/studyplan/index', methods=['GET'])
@login_required
def indexStudyplan():
    studyplans = Studyplans.query.all()
    return render_template('admin/studyplan/index.html', studyplans=studyplans)


@app.route('/admin/studyplan/read/<string:studyplan_id>', methods=['GET'])
@login_required
def readStudyplan(studyplan_id):
    studyplan = Studyplans.query.get(studyplan_id)
    return render_template('admin/studyplan/read.html', studyplan=studyplan)


@app.route('/admin/studyplans/delete', methods=['GET','POST'])
@login_required
def deleteStudyplans():
    if request.method == 'GET':
        academicyears = Academicyears.query.all()
        return render_template('/admin/studyplan/delete.html', academicyears=academicyears)
    elif request.method == 'POST':
        if request.form['delete'] == 'delete':
            curriculum_ac = request.form['academicyear']
            q = db.session.query(Studyplans).join(Curricula, Curricula.id == Studyplans.curriculum_id).filter(Curricula.ac == curriculum_ac).all()

            studyplans_to_delete = q
       
            for studyplan in studyplans_to_delete:
                db.session.delete(studyplan)
            db.session.commit()
            db.session.flush()
            return redirect(url_for('indexStudyplan'))
           
        elif request.form['delete'] == 'undo':
            return redirect(url_for('indexStudyplan'))
        else:
            return 'error: unknown action'


def isValidAcademicyear(academicyear):
    res = True    
    if academicyear.id == "":
        flash("Hai inserito un anno accademico vuoto")
        return False
    years = string.split(academicyear.id, '-')
    if len(years) < 2:
        flash("Attenzione formato errato. usa il segno meno per separare gli anni solari")
        return False
    if int(years[0]) < 2018 or int(years[0]) > 2023:
        flash("Attenzione, forse hai inserito un anno accademico errato. L'anno deve essere compreso tra 2018-2019 e 2023-2024")
        res = False
    if (int(years[0]) + 1) != int(years[1]):
        flash("Attenzione, l'anno accademico deve essere nella forma <year> - <year+1>")
        res = False
    return res




def isValidCourse(course):
    res = True
    if len(course.id) != 7:
        res = False
        flash("Errore. Il codice del corso deve essere di 7 caratteri")
    if course.name == "":
        res = False
        flash("Errore. Il nome del corso non deve essere vuoto")
    if course.cfu != 6 or course.cfu != 9:
        res = False
        flash("Attenzione hai inserito un numero di cfu non valido. Inserisci 6 o 9.")
    if course.ssd == "":
        res = False
        flash("Errore il campo ssd non deve essere vuoto")
    return res

def isValidGroup(group):
    res = True
    if group.name == "":
        flash("Errore. Il nome del gruppo non deve essere vuoto")
        res = False
    if group.courses is None:
        flash("Errore. Il gruppo " + group.name + " ha zero corsi")
        return False #previene errori nelle funzioni successive dovuti al fatto che groups sia null
    if len(group.courses) < 2:
        res = False
        flash("Errore. Un gruppo deve contenere almeno 2 corsi")
    if group.n < 1:
        res = False
        flash("Errore. Il numero n di corsi sceglibili deve essere almeno 1")
    if len(group.courses) <= group.n:
        res = False
        flash("Errore. Il numero di corsi appartenti al gruppo deve essere maggiore del vincolo")
    return res


def isValidCurriculum(curriculum):
    res = True

    if curriculum.title == "":
        flash("Errore. Il titolo del curriculum non deve essere vuoto")
        res = False

    if curriculum.groups is None:      
        flash("Errore. Il curriculum " + curriculum.title + " ha zero gruppi. Contatta l'amministratore.")
        return False #previene errori nelle funzioni successive dovuti al fatto che groups sia null

    for group in curriculum.groups:
        if not isValidGroup(group):
            res = False

    cfu_tot = 0
    for g in curriculum.groups:
        cfu_tot = cfu_tot + g.n * g.courses[0].cfu
    if cfu_tot < 84:
        flash("Errore. Il curriculum " + curriculum.title + " ha un numero di corsi sceglibili insufficenti al raggiungimento di 84 cfu.")
        res = False
    
    uniqueCourses = []
    for g in curriculum.groups:
        for c in g.courses:
            if c.name not in uniqueCourses:
                uniqueCourses.append(c.name)
            else:
                flash("Attenzione il corso " + c.id + " " + c.name + " nel gruppo " + g.name + " e' duplicato per il curriculum " + curriculum.title )
                res = False
    return res

def isValidStudent(student):
    res = True
    if len(student.id) != 7:
        flash("La matricola inserita non e' valida, deve essere lunga 7 caratteri")
        res = False
    if student.firstname == "" or student.lastname == "":
        flash("Nome e cognome non validi")
        res = False
    return res

#curriculum_id  e' sempre giusto. In caso fosse sbagliato si avrebbe un errore di pagina non trovata.

def isValidStudyplan(studyplan):
    res = True
    # Controllo vincoli su corsi a scelta vincolata
    if studyplan.courses is None:
        flash("Errore. Nessun corso a scelta vincolata specificato.")
        return False

    curriculum = Curricula.query.get(studyplan.curriculum_id)

    for group in curriculum.groups:
            count=0
            for course in studyplan.courses:
                if( course.id in [c.id for c in group.courses]):
                    count+=1
            if count < group.n:
                flash("Errore. Nel gruppo " + str(group.name) +" hai inserito " +str(count)+" corsi. Devi inserirene almeno " + str(group.n) )
                res = False

    if studyplan.othercourses is None:
        flash("Errore. Nessun corso a scelta libera specificato")
        return False
    if len(studyplan.othercourses) < 2:
        flash("Errore. Devi inserire almeno 2 corsi a scelta libera")
        res = False
    if len(studyplan.othercourses[0].id) != 7 and len(studyplan.othercourses[1].id) != 7:
        flash("Errore. Il codice esame ha una lunghezza di 7 caratteri")
        res = False
            
    for course in studyplan.courses:
        if course.id == studyplan.othercourses[0].id or course.id == studyplan.othercourses[1].id:
            flash("Errore. Il corso a scelta libera con codice " + course.id + " e' duplicato nel piano di studi." )
            res = False
        if course.name == studyplan.othercourses[0].name or course.name == studyplan.othercourses[1].name:
            flash("Errore. Il corso a scelta libera con nome " + course.name + " e' gia presente nel piano di studi con cfu=" + course.cfu)
            res = False
    '''
    cfu_tot = 0
    for course in studyplan.courses:
        cfu_tot = cfu_tot + course.cfu
    if cfu_tot < 84:
        flash("Errore. Il numero di cfu totali dei corsi a scelta vincolata deve essere almeno 84")
        res = False
    '''
    if (studyplan.othercourses[0].cfu + studyplan.othercourses[1].cfu) < 12:
        flash("Errore. Il numero di cfu per i corsi a scelta libera deve essere almeno 12")
        res = False

    return res    
'''
@app.errorhandler(AssertionError)
def handle_sqlalchemy_assertion_error(err):
    return make_response(standard_response(None, 400, err.message), 400)
'''
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == "__main__":
    app.run(debug=True)


  