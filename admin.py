from flask import Blueprint, render_template, redirect, url_for, request, flash, flash, send_file
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from models import Admin, User, db, Quiz, Question, QuestionTranslation, Option, OptionTranslation, Attempt, Answer  # Import db from models
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend
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
            return redirect(url_for('admin.dashboard'))
        flash('Invalid username or password')
    return render_template('admin/admin_login.html')

@admin_bp.route('/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin.admin_login'))

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

@admin_bp.route('/create_quiz', methods=['GET'])
@login_required
def create_quiz():
    return render_template('admin/create_quiz.html')

@admin_bp.route('/submit_quiz', methods=['POST'])
@login_required
def submit_quiz():
    data = request.form
    title = data.get('title')
    language = data.get('language')
    
    # Debug statements for quiz title and language
    print(f"Quiz Title: {title}, Language: {language}")
    
    # Create new Quiz
    quiz = Quiz(title=title, language=language, is_active=True)  #CHANGE THIS
    db.session.add(quiz)
    db.session.commit()  # Commit to get the quiz ID
    
    # Debug statement for quiz ID
    print(f"Created Quiz with ID: {quiz.id}")

    questions = [key for key in data if key.startswith('questions')]
    print(f"Form Keys: {questions}")

    question_indices = sorted(set(int(key.split('[')[1].split(']')[0]) for key in questions if 'title' in key))
    print(f"Question Indices: {question_indices}")

    for q_idx in question_indices:
        question_title = data.get(f'questions[{q_idx}][title]')
        
        # Debug statement for question title
        print(f"Question {q_idx + 1} Title: {question_title}")
        
        # Create new Question
        question_entry = Question(title=question_title, quiz_id=quiz.id)
        db.session.add(question_entry)
        db.session.commit()  # Commit to get the question ID

        # Debug statement for question ID
        print(f"Created Question with ID: {question_entry.id}")

        # Handle question translations
        for lang in ['fr', 'ar']:
            translation_title = data.get(f'translations[{q_idx}][{lang}]')
            print(f"Question {q_idx + 1} Translation [{lang}]: {translation_title}")

            translation_entry = QuestionTranslation(
                question_id=question_entry.id,
                language=lang,
                title=translation_title
            )
            db.session.add(translation_entry)

        option_keys = [key for key in data if key.startswith(f'questions[{q_idx}][options]')]
        option_indices = sorted(set(int(key.split('[')[3].split(']')[0]) for key in option_keys if 'text' in key))
        print(f"Option Indices for Question {q_idx + 1}: {option_indices}")

        for o_idx in option_indices:
            option_text = data.get(f'questions[{q_idx}][options][{o_idx}][text]')
            is_correct = data.get(f'questions[{q_idx}][options][{o_idx}][is_correct]') == 'true'
            
            # Debug statement for option text and is_correct flag
            print(f"Option {o_idx + 1} Text: {option_text}, Is Correct: {is_correct}")
            
            # Create new Option
            option_entry = Option(
                question_id=question_entry.id,
                text=option_text,
                is_correct=is_correct
            )
            db.session.add(option_entry)
            db.session.commit()  # Commit to get the option ID

            # Debug statement for option ID
            print(f"Created Option with ID: {option_entry.id}")

            # Handle option translations
            for lang in ['fr', 'ar']:
                option_translation_text = data.get(f'translations[{q_idx}][options][{o_idx}][{lang}]')
                print(f"Option {o_idx + 1} Translation [{lang}]: {option_translation_text}")

                option_translation_entry = OptionTranslation(
                    option_id=option_entry.id,
                    language=lang,
                    text=option_translation_text
                )
                db.session.add(option_translation_entry)

    db.session.commit()
    return redirect(url_for('admin.view_quiz', quiz_id=quiz.id))

@admin_bp.route('/view_quiz/<int:quiz_id>')
@login_required
def view_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    return render_template('admin/view_quiz.html', quiz=quiz)

@admin_bp.route('/quizzes')
@login_required
def quizzes():
    quizzes = Quiz.query.all()
    return render_template('admin/quizzes.html', quizzes=quizzes)

@admin_bp.route('/set_active_quiz/<int:quiz_id>', methods=['POST'])
@login_required
def set_active_quiz(quiz_id):
    try:
        # Deactivate all quizzes
        Quiz.query.update({'is_active': False})
        
        # Activate the selected quiz
        quiz = Quiz.query.get_or_404(quiz_id)
        quiz.is_active = True
        db.session.commit()

        return redirect(url_for('admin.view_all_quizzes'))
    except Exception as e:
        db.session.rollback()
        flash('Error occurred while updating quiz status: ' + str(e), 'danger')
        return redirect(url_for('admin.quizzes'))

@admin_bp.route('/deactivate_quiz/<int:quiz_id>', methods=['POST'])
def deactivate_quiz(quiz_id):
    # Deactivate the selected quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    quiz.is_active = False
    db.session.commit()
    
    return redirect(url_for('admin.quizzes'))

@admin_bp.route('/users')
def view_users():
    # Fetch all users
    users = User.query.all()
    return render_template('admin/view_users.html', users=users)

@admin_bp.route('/attempts')
def view_attempts():
    # Fetch all attempts and join with related quiz and user data
    attempts = db.session.query(Attempt, User, Quiz).join(User).join(Quiz).all()
    return render_template('admin/view_attempts.html', attempts=attempts)

@admin_bp.route('/dashboard')
def dashboard():
    # Fetch data from the database
    total_users = User.query.count()
    total_quizzes = Quiz.query.count()
    total_attempts = Attempt.query.count()

    attempts_per_quiz = (
        db.session.query(Quiz.title, db.func.count(Attempt.id).label('attempt_count'))
        .outerjoin(Attempt, Quiz.id == Attempt.quiz_id)
        .group_by(Quiz.id)
        .all()
    )

    score_distribution = (
        db.session.query(
            db.func.avg(Attempt.score).label('avg_score'),
            db.func.min(Attempt.score).label('min_score'),
            db.func.max(Attempt.score).label('max_score')
        ).one()
    )

    metrics_data = {
        "total_users": total_users,
        "total_quizzes": total_quizzes,
        "total_attempts": total_attempts,
        "attempts_per_quiz": [{'title': item[0], 'attempt_count': item[1]} for item in attempts_per_quiz],
        "score_distribution": {
            "avg_score": score_distribution.avg_score,
            "min_score": score_distribution.min_score,
            "max_score": score_distribution.max_score,
        }
    }

    # Generate charts
    attempts_per_quiz_img = generate_attempts_per_quiz_chart(metrics_data["attempts_per_quiz"])
    score_distribution_img = generate_score_distribution_chart(metrics_data["score_distribution"])

    return render_template('admin/metrics.html',
                           metrics=metrics_data,
                           attempts_per_quiz_img=attempts_per_quiz_img,
                           score_distribution_img=score_distribution_img)

def generate_attempts_per_quiz_chart(attempts_per_quiz):
    fig, ax = plt.subplots()
    quizzes = [item["title"] for item in attempts_per_quiz]
    attempts = [item["attempt_count"] for item in attempts_per_quiz]
    
    # Create the bar chart
    ax.bar(quizzes, attempts, color='teal')
    ax.set_xlabel('Quizzes')
    ax.set_ylabel('Number of Attempts')
    ax.set_title('Attempts per Quiz')
    
    # Rotate x-axis labels to vertical
    ax.set_xticks(range(len(quizzes)))
    ax.set_xticklabels(quizzes, rotation=90, ha='center')

    # Improve layout
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close(fig)
    return img_base64

def generate_score_distribution_chart(score_distribution):
    fig, ax = plt.subplots()
    categories = ['Average Score', 'Minimum Score', 'Maximum Score']
    
    # Ensure all values are non-negative; replace negative values with zero
    scores = [
        max(score_distribution["avg_score"], 0),
        max(score_distribution["min_score"], 0),
        max(score_distribution["max_score"], 0)
    ]
    
    # Check if all scores are zero, which would lead to an invalid pie chart
    if all(score == 0 for score in scores):
        scores = [1, 1, 1]  # Fallback values to ensure at least some data in the pie chart

    ax.pie(scores, labels=categories, autopct='%1.1f%%', colors=['purple', 'orange', 'red'])
    ax.set_title('Score Distribution')

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close(fig)
    return img_base64
