from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response,abort, flash, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from models import Admin, User, db, Quiz, Question, QuestionTranslation, Option, OptionTranslation, Attempt, Answer  # Import db from models

from datetime import datetime
import pytz 

import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

admin_bp = Blueprint('admin', __name__)


#flask create-admin adminuser adminpassword
@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            login_user(admin)  # Using Flask-Login's login_user function
            return redirect(url_for('admin.admin_dashboard'))
        flash('Invalid username or password')
    return render_template('admin_login.html')

@admin_bp.route('/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin.admin_login'))

@admin_bp.route('/dashboard')
@login_required
def admin_dashboard():
    # Query to get all attempts with user and quiz information
    attempts = Attempt.query.join(User, Attempt.user_id == User.id).join(
        Quiz, Attempt.quiz_id == Quiz.id).add_columns(
        Attempt.id,
        Attempt.user_id,
        Attempt.quiz_id,
        Attempt.score,
        Attempt.status,
        Attempt.time,
        User.emp_id,
        User.cin,
        User.first_name,
        User.last_name,
        User.service,
        User.site,
        Quiz.title.label('quiz_title')
    ).all()

    print(f"Found {len(attempts)} attempts")  # Debug print

    for attempt in attempts:
        print(f"Attempt: User ID={attempt.user_id}, Quiz ID={attempt.quiz_id}, Quiz Title={attempt.quiz_title}, Score={attempt.score}, Status={attempt.status}, Time={attempt.time}, User Name={attempt.first_name} {attempt.last_name}, Employee ID={attempt.emp_id}")

    return render_template('admin_dashboard.html', attempts=attempts)

@admin_bp.route('/export')
@login_required
def export():
    attempts = Attempt.query.all()
    data = [{
        
        "Nom": attempt.user.last_name,
        "Prénom": attempt.user.first_name,
        "CIN": attempt.user.cin,
        "Service": attempt.user.service,
        "Site": attempt.user.site,
        "Formation": attempt.quiz.title,
        "Points": attempt.score,
        "Resultat": attempt.status,
        "Date": attempt.time
    } for attempt in attempts]
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Evalution Formation')
    writer.close()
    output.seek(0)
    
    return send_file(output, as_attachment=True, download_name='evaluation.xlsx')



"""
@admin_bp.route('/admin')
def admin_quiz_attempts():
    # Query to get all attempts with user and quiz information
    attempts = Attempt.query.join(User, Attempt.user_id == User.id).join(
        Quiz, Attempt.quiz_id == Quiz.id).add_columns(
        Attempt.id,
        Attempt.user_id,
        Attempt.quiz_id,
        Attempt.score,
        Attempt.status,
        Attempt.time,
        User.emp_id,
        User.cin,
        User.first_name,
        User.last_name,
        User.service,
        User.site,
        Quiz.title.label('quiz_title')
    ).all()

    print(f"Found {len(attempts)} attempts")  # Debug print

    for attempt in attempts:
        print(f"Attempt: User ID={attempt.user_id}, Quiz ID={attempt.quiz_id}, Quiz Title={attempt.quiz_title}, Score={attempt.score}, Status={attempt.status}, Time={attempt.time}, User Name={attempt.first_name} {attempt.last_name}, Employee ID={attempt.emp_id}")

    return render_template('admin_dashboard.html', attempts=attempts)

@admin_bp.route('/admin/export')
def admin_export():
    attempts = Attempt.query.all()
    data = [{
        "User": attempt.user.first_name,
        "Quiz": attempt.quiz.title,
        "Score": attempt.score,
        "Passed": attempt.passed,
        "Timestamp": attempt.timestamp
    } for attempt in attempts]
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Quiz Attempts')
    writer.close()
    output.seek(0)
    
    return send_file(output, as_attachment=True, download_name='quiz_attempts.xlsx')


@admin_bp.route('/admin/metrics')
def admin_metrics():
    attempts = Attempt.query.all()
    scores = [attempt.score for attempt in attempts]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    # Generate plot
    plt.figure(figsize=(10, 6))
    plt.hist(scores, bins=10, edgecolor='black')
    plt.title('Distribution of Scores')
    plt.xlabel('Score')
    plt.ylabel('Frequency')
    
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()

    return render_template('admin_metrics.html', avg_score=avg_score, plot_url=plot_url)







#for later 


@admin_bp.route('/admin/create_quiz', methods=['GET', 'POST'])
def create_quiz():
    if request.method == 'POST':
        title = request.form['title']
        default_language = request.form['language']

        # Insert the quiz title
        new_quiz = Quiz(title=title, language=default_language)
        db.session.add(new_quiz)
        db.session.commit()
        quiz_id = new_quiz.id

        question_index = 1
        while f'question_text_{question_index}' in request.form:
            question_text = request.form[f'question_text_{question_index}']
            
            # Insert the question
            new_question = Question(quiz_id=quiz_id, title=question_text)
            db.session.add(new_question)
            db.session.commit()
            question_id = new_question.id
            
            # Insert translations for the question
            for lang in ['es', 'fr', 'ar']:
                trans_text = request.form.get(f'question_text_{question_index}_{lang}', '')
                if trans_text:
                    new_question_trans = QuestionTranslation(question_id=question_id, language=lang, title=trans_text)
                    db.session.add(new_question_trans)

            option_index = 1
            while f'option_text_{question_index}_{option_index}' in request.form:
                option_text = request.form[f'option_text_{question_index}_{option_index}']
                
                # Insert the option
                new_option = Option(question_id=question_id, text=option_text)
                db.session.add(new_option)
                db.session.commit()
                option_id = new_option.id

                # Insert translations for the option
                for lang in ['es', 'fr', 'ar']:
                    trans_text = request.form.get(f'option_text_{question_index}_{option_index}_{lang}', '')
                    if trans_text:
                        new_option_trans = OptionTranslation(option_id=option_id, language=lang, text=trans_text)
                        db.session.add(new_option_trans)

                # Insert correct option status
                is_correct = f'correct_{question_index}_{option_index}' in request.form
                new_option.is_correct = is_correct

                option_index += 1

            db.session.commit()
            question_index += 1

    return render_template('admin_create_quiz.html')


@admin_bp.route('/admin/delete_quiz/<int:quiz_id>')
def delete_quiz(quiz_id):
    Quiz.query.filter_by(id=quiz_id).delete()
    db.session.commit()
    return redirect(url_for('auth.manage_quizzes'))

"""












