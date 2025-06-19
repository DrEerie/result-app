from flask import Flask, render_template, request, redirect, url_for, flash
from models.models import db, Student, Subject, Result
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'database')
os.makedirs(db_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(db_path, 'result.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

class_options = ['Montessori', 'Nursery'] + [str(i) for i in range(1, 13)]

@app.route('/')
def home():
    return "<h1>Welcome to Result System</h1><a href='/enter'>Enter Results</a>"

@app.route('/enter', methods=['GET', 'POST'])
def enter_result():
    subjects = Subject.query.all()

    if request.method == 'POST':
        name = request.form['student_name']
        roll_no = request.form['roll_no']
        cls = request.form['cls']
        section = request.form['section']
        action = request.form.get('action_type', 'insert')


        existing_student = Student.query.filter_by(roll_no=roll_no).first()

        if existing_student:
            if action == 'insert':
                flash("Roll number already exists. Choose overwrite or delete.", "error")
                return render_template('enter_result.html', subjects=subjects, existing_roll=roll_no, prefill=request.form)
            elif action == 'delete':
                delete_student(existing_student)
            elif action == 'overwrite':
                overwrite_student(existing_student, name, cls, section)
        else:
            student = Student(name=name, roll_no=roll_no, cls=cls, section=section)
            db.session.add(student)
            db.session.commit()

        add_results(student if not existing_student else existing_student, subjects, request.form)
        flash("Result updated successfully!", "success")
        return redirect(url_for('enter_result'))

    return render_template('enter_result.html', subjects=subjects)

def delete_student(student):
    Result.query.filter_by(student_id=student.id).delete()
    db.session.delete(student)
    db.session.commit()

def overwrite_student(student, name, cls, section):
    Result.query.filter_by(student_id=student.id).delete()
    student.name = name
    student.cls = cls
    student.section = section
    db.session.commit()

def add_results(student, subjects, form_data):
    for subject in subjects:
        marks = form_data.get(f"marks_{subject.name}")
        if marks:
            db.session.add(Result(student_id=student.id, subject_id=subject.id, marks=float(marks)))
    db.session.commit()


if __name__ == '__main__':
    app.run(debug=True)
