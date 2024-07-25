from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response, flash
from flask_login import login_user as user_login_user, logout_user as user_logout_user, login_required as user_login_required, current_user as user_current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Quiz, Question, QuestionTranslation, Option, OptionTranslation, Attempt, Answer
from datetime import datetime
import pytz 
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        emp_id = request.form.get('emp_id')
        cin = request.form.get('cin')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        service = request.form.get('service')
        site = request.form.get('site')
        password = request.form.get('password')

        # Check if all fields are provided
        if not emp_id or not cin or not first_name or not last_name or not service or not site or not password:
            flash('All fields are required!', 'error')
            return redirect(url_for('auth.register'))

        # Check if a user with the same emp_id or cin already exists
        existing_user = User.query.filter((User.emp_id == emp_id) | (User.cin == cin)).first()
        if existing_user:
            if existing_user.emp_id == emp_id:
                flash('A user with this employee ID already exists.', 'error')
            if existing_user.cin == cin:
                flash('A user with this CIN already exists.', 'error')
            return redirect(url_for('auth.login'))

        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(emp_id=emp_id, cin=cin, first_name=first_name, last_name=last_name,
                        service=service, site=site, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully!', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()  # Rollback if there's an error
            print(f"Error: {e}")
            flash('An error occurred while creating your account. Please try again.', 'error')

    if request.method == 'GET' and user_current_user.is_authenticated:
        return redirect(url_for('auth.explanation'))  
    language = session.get('language', 'fr')
    return render_template(f'register_{language}.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    language = session.get('language', 'fr')

    if user_current_user.is_authenticated:
        return redirect(url_for('auth.explanation'))
    
    if request.method == 'POST':
        emp_id = request.form.get('emp_id')
        password = request.form.get('password')

        user = User.query.filter_by(emp_id=emp_id).first()

        if user and check_password_hash(user.password, password):
            user_login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('auth.explanation'))
        else:
            flash('Login failed. Check your emp_id and/or password.', 'error')
            return redirect(url_for('auth.login'))

    
    return render_template(f'login_{language}.html')


@auth_bp.route('/logout')
@user_login_required
def logout():
    user_logout_user()
    flash('Logged out successfully!', 'success')
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/explanation')
@user_login_required
def explanation():
    # Check if the user has already attempted this quiz
    active_quiz = Quiz.query.filter_by(is_active=True).first()
    attempt = Attempt.query.filter_by(user_id=user_current_user.id, quiz_id=active_quiz.id).first()
    if attempt:
        return redirect(url_for('auth.show_result', status=attempt.status))
    language = session.get('language', 'fr')
    return render_template(f'explanation_{language}.html')

@auth_bp.route('/quiz')
@user_login_required
def quiz():
    if not user_current_user.is_authenticated:
        return redirect(url_for('auth.login'))  # Redirect to login if not authenticated

    try:
        # Fetch the active quiz
        active_quiz = Quiz.query.filter_by(is_active=True).first()

        if not active_quiz:
            return "No active quiz found.", 404

        # Check if the user has already attempted this quiz
        attempt = Attempt.query.filter_by(user_id=user_current_user.id, quiz_id=active_quiz.id).first()
        if attempt:
            return redirect(url_for('auth.show_result', status=attempt.status))

        # Initialize start_time in the session if it does not exist
        if 'start_time' not in session:
            session['start_time'] = datetime.now(pytz.utc).isoformat()

        # Generate CSRF token
        csrf_token = str(uuid.uuid4())
        session['csrf_token'] = csrf_token

        # Fetch quiz with related questions and options
        quiz = Quiz.query.options(
            db.joinedload(Quiz.questions).joinedload(Question.options)
        ).get_or_404(active_quiz.id)

        # Fetch translations for questions and options
        language = session.get('language', 'fr')  
        print(session.get('language'))
        print(language)
        questions_translations = (
            QuestionTranslation.query.filter(QuestionTranslation.language == language)
            .all()
        )
        options_translations = (
            OptionTranslation.query.filter(OptionTranslation.language == language)
            .all()
        )

        # Convert translations to dictionaries for easy lookup
        questions_translations_dict = {qt.question_id: qt.title for qt in questions_translations}
        options_translations_dict = {ot.option_id: ot.text for ot in options_translations}

        # Prepare data for rendering
        quiz_data = {
            'id': quiz.id,
            'title': quiz.title,
            'questions': [
                {
                    'id': question.id,
                    'title': questions_translations_dict.get(question.id, question.title),
                    'options': [
                        {
                            'id': option.id,
                            'text': options_translations_dict.get(option.id, option.text),
                            'is_correct': option.is_correct
                        }
                        for option in question.options
                    ]
                }
                for question in quiz.questions
            ]
        }

        # Debugging: Print session and quiz details
        print(f"Session Start Time: {session['start_time']}")
        print(f"User ID: {user_current_user.id}")

        #template_name = f'quiz_{language}.html'
        template_name = f'quiz_{language}.html'
        response = make_response(render_template(template_name, quiz=quiz_data, start_time=session['start_time'], csrf_token=csrf_token))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    except Exception as e:
        print(f"Error occurred: {e}")
        return "An error occurred while fetching the quiz", 500

@auth_bp.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
@user_login_required
def submit_quiz(quiz_id):
    if not user_current_user.is_authenticated:
        return redirect(url_for('auth.login'))  # Redirect if the user is not authenticated

    user_id = user_current_user.id  # Use current_user.id instead of session['user_id']
    start_time_str = session.get('start_time')  # Get start_time from session
    end_time = datetime.utcnow()

    # Check if start_time is present and is a string
    if start_time_str:
        try:
            start_time = datetime.fromisoformat(start_time_str)
        except ValueError:
            return "Invalid start time format", 400
    else:
        return "Start time not found in session", 400

    # Check for the CSRF token
    submitted_token = request.form.get('csrf_token')
    session_token = session.pop('csrf_token', None)  # Remove the token from session

    if not session_token or session_token != submitted_token:
        flash('Invalid or missing CSRF token. Please try submitting the quiz again.', 'error')
        return redirect(url_for('auth.quiz', quiz_id=quiz_id))  # Adjust URL if needed

    # Define the passing score threshold (as a percentage)
    PASSING_SCORE_PERCENTAGE = 75  # Example: 25% passing score

    final_score = 0
    question_scores = {}

    try:
        # Fetch the quiz and its related data
        quiz = Quiz.query.get_or_404(quiz_id)

        for key, value in request.form.items():
            if key.startswith('question_'):
                parts = key.split('_')
                if len(parts) != 2 or not parts[1].isdigit():
                    continue

                try:
                    question_id = int(parts[1])
                except ValueError:
                    continue  # Skip invalid keys

                selected_options = request.form.getlist(key)
                question_scores[question_id] = {'correct': 0, 'incorrect': 0}

                question = Question.query.get_or_404(question_id)
                total_options = Option.query.filter_by(question_id=question_id).count()
                correct_options_count = Option.query.filter_by(question_id=question_id, is_correct=True).count()

                for option_id in selected_options:
                    try:
                        option_id = int(option_id)
                    except ValueError:
                        continue  # Skip invalid option IDs

                    option = Option.query.get_or_404(option_id)

                    if option.is_correct:
                        question_scores[question_id]['correct'] += 1
                    else:
                        question_scores[question_id]['incorrect'] += 1

                correct_count = question_scores[question_id]['correct']
                incorrect_count = question_scores[question_id]['incorrect']

                if incorrect_count == 0:
                    if correct_count == correct_options_count:
                        final_score += 4
                    else:
                        final_score += correct_count
                else:
                    if correct_count == 0:
                        final_score -= incorrect_count
                    else:
                        final_score += correct_count - incorrect_count

        total_questions = len(question_scores)
        max_score = total_questions * 4

        percentage_score = (final_score / max_score) * 100 if max_score > 0 else 0
        status = 'Passed' if percentage_score >= PASSING_SCORE_PERCENTAGE else 'Failed'

        attempt = Attempt(
            user_id=user_id,
            quiz_id=quiz_id,
            score=final_score,
            status=status,
            time=end_time
        )
        db.session.add(attempt)
        db.session.commit()

        attempt_id = attempt.id

        for question_id in question_scores.keys():
            selected_options = request.form.getlist(f'question_{question_id}')
            for option_id in selected_options:
                try:
                    option_id = int(option_id)
                except ValueError:
                    continue  # Skip invalid option IDs

                option = Option.query.get_or_404(option_id)
                answer = Answer(
                    attempt_id=attempt_id,
                    question_id=question_id,
                    option_id=option_id,
                    is_correct=option.is_correct
                )
                db.session.add(answer)

        db.session.commit()

        session.pop('start_time', None)  # Clear the start_time from session after submission

        # Create a response to prevent caching
        response = make_response(redirect(url_for('auth.show_result', status=attempt.status)))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        return response
    except Exception as e:
        db.session.rollback()  # Rollback the transaction in case of error
        print(f"Error occurred: {e}")
        return "An error occurred while processing your submission", 500

@auth_bp.route('/result', methods=['GET'])
@user_login_required
def show_result():
    status = request.args.get('status', 'unknown')
    language = session.get("language", "fr")
    return render_template(f'finish_{language}.html', status=status)
























#CODE FOR LATER

"""
@auth_bp.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    quizzes = Quiz.query.all()
    questions = Question.query.all()
    options = Option.query.all()
    users = User.query.all()  # Assuming there's a User model

    users = db.session.query(User).all()
    user_attempts = db.session.query(User, Attempt, Quiz).join(Attempt, User.id == Attempt.user_id).join(Quiz, Attempt.quiz_id == Quiz.id).all()

    quiz_data = {
        'total_quizzes': len(quizzes),
        'total_questions': len(questions),
        'total_options': len(options),
        'total_users': len(users)
    }

    return render_template('admin_dashboard.html', users=users, user_attempts=user_attempts)

@auth_bp.route('/admin/users')
def manage_users():
    users = User.query.all()
    return render_template('admin_manage_users.html', users=users)

@auth_bp.route('/admin/view_user/<int:user_id>')
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    # Fetch the user's attempts with explicit table aliases
    attempts = db.session.query(
        Quiz.title.label('quiz_title'),
        Attempt.score.label('score'),
        Attempt.status.label('status'),
        Attempt.time.label('time'))
    .join(Quiz, Attempt.quiz_id == Quiz.id) \
    .filter(Attempt.user_id == user_id) \
    .all()
    return render_template('admin_view_user.html', user=user, attempts=attempts)

@auth_bp.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.service = request.form['service']
        db.session.commit()
        return redirect(url_for('auth.manage_users'))
    return render_template('admin_edit_user.html', user=user)

@auth_bp.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('manage_users'))


@auth_bp.route('/admin/quizzes')
def manage_quizzes():
    quizzes = Quiz.query.all()
    return render_template('admin_manage_quizzes.html', quizzes=quizzes)

@auth_bp.route('/quizzes/set_active/<int:quiz_id>', methods=['POST'])
def set_active_quiz(quiz_id):
    # Deactivate all quizzes
    Quiz.query.update({'is_active': False})
    db.session.commit()
    
    # Activate the selected quiz
    quiz = Quiz.query.get(quiz_id)
    if quiz is None:
        abort(404, description="Quiz not found")
    quiz.is_active = True
    db.session.commit()
    
    return redirect(url_for('auth.manage_quizzes'))

@auth_bp.route('/admin/quizzes/view/<int:quiz_id>')
def view_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if quiz is None:
        abort(404, description="Quiz not found")

    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    return render_template('admin_view_quiz.html', quiz=quiz, questions=questions)


@auth_bp.route('/admin/quizzes/edit/<int:quiz_id>', methods=['GET', 'POST'])
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    if request.method == 'POST':
        title = request.form['title']
        language = request.form['language']

        # Validate input as needed
        if not title or not language:
            flash('Title and Language are required!', 'warning')
            return redirect(url_for('auth.edit_quiz', quiz_id=quiz_id))

        # Update quiz details
        quiz.title = title
        quiz.language = language
        db.session.commit()
        flash('Quiz updated successfully!', 'success')
        return redirect(url_for('auth.manage_quizzes'))

    return render_template('edit_quiz.html', quiz=quiz)

@auth_bp.route('/admin')
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

@auth_bp.route('/admin/create_quiz', methods=['GET', 'POST'])
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


@auth_bp.route('/admin/delete_quiz/<int:quiz_id>')
def delete_quiz(quiz_id):
    Quiz.query.filter_by(id=quiz_id).delete()
    db.session.commit()
    return redirect(url_for('auth.manage_quizzes'))
"""













