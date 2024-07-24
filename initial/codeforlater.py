def calculate_passing_grade(quiz_id):
    conn = sqlite3.connect('quiz_results.db')
    c = conn.cursor()

    # Fetch the total number of questions for the quiz
    c.execute('SELECT COUNT(*) FROM Questions WHERE quiz_id = ?', (quiz_id,))
    total_questions = c.fetchone()[0]

    # Assuming each question can yield a maximum of 4 points
    max_points = total_questions * 4

    # Calculate the passing grade (e.g., 60% of max points)
    passing_grade = int(max_points * 0.6)

    # Update the passing grade in the Quizzes table
    c.execute('UPDATE Quizzes SET passing_grade = ? WHERE id = ?', (passing_grade, quiz_id))

    conn.commit()
    conn.close()

# Call this function when creating or updating a quiz
calculate_passing_grade(quiz_id)









@app.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
def submit_quiz(quiz_id):
    user_id = session.get('user_id')  # Ensure user is logged in
    start_time = datetime.fromisoformat(session.get('start_time'))
    end_time = datetime.utcnow()
    if not user_id:
        return "User not logged in", 401

    conn = sqlite3.connect('quiz_results.db')
    c = conn.cursor()

    # Print the entire form data
    print("Form Data:", request.form)

    # Start a transaction
    conn.execute('BEGIN TRANSACTION')

    try:
        # Insert a new attempt record
        c.execute('''
        INSERT INTO Attempts (user_id, quiz_id, score, status, time)
        VALUES (?, ?, 0, 'completed', ?)
        ''', (user_id, quiz_id, datetime.now()))
        attempt_id = c.lastrowid

        score = 0

        # Process each question's answers
        for question_key in request.form:
            if question_key.startswith('question_'):
                question_id = int(question_key.replace('question_', ''))
                selected_option_ids = request.form.getlist(question_key)  # Get all selected options

                print(f"Processing Question ID: {question_id}, Selected Option IDs: {selected_option_ids}")

                for selected_option_id in selected_option_ids:
                    c.execute('''
                    SELECT is_correct FROM Options WHERE id = ?
                    ''', (selected_option_id,))
                    option = c.fetchone()
                    print(f"Retrieved Option: {option}")

                    if option:
                        # Ensure that option contains exactly one value
                        is_correct = option[0]
                    else:
                        # Handle case where no option is found
                        is_correct = False

                    # Insert answer record
                    c.execute('''
                    INSERT INTO Answers (attempt_id, question_id, option_id, is_correct)
                    VALUES (?, ?, ?, ?)
                    ''', (attempt_id, question_id, selected_option_id, is_correct))

                    # Update score
                    if is_correct:
                        score += 1

        # Update attempt record with the final score
        c.execute('''
        UPDATE Attempts
        SET score = ?
        WHERE id = ?
        ''', (score, attempt_id))

        conn.commit()
        return redirect(url_for('results', attempt_id=attempt_id))

    except Exception as e:
        conn.rollback()
        print(f"Error occurred: {e}")
        return "An error occurred while processing the quiz", 500
    finally:
        conn.close()