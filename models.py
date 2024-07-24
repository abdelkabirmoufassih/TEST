from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()  # Define db

class User(db.Model, UserMixin):
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    emp_id = db.Column(db.String, nullable=False)
    cin = db.Column(db.String, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    service = db.Column(db.String, nullable=False)
    site = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)

    def get_id(self):
        return f"user_{self.id}"

class Admin(db.Model, UserMixin):
    __tablename__ = 'Admins'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)

    def get_id(self):
        return f"admin_{self.id}"

    def __repr__(self):
        return f'<Admin {self.username}>'

class Quiz(db.Model):
    __tablename__ = 'Quizzes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    language = db.Column(db.String, nullable=False)
    is_active = db.Column(db.Boolean, default=False)  # Add this field
    questions = db.relationship("Question", back_populates="quiz")

class Question(db.Model):
    __tablename__ = 'Questions'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('Quizzes.id'), nullable=False)
    title = db.Column(db.String, nullable=False)
    quiz = db.relationship("Quiz", back_populates="questions")
    translations = db.relationship("QuestionTranslation", back_populates="question")
    options = db.relationship("Option", back_populates="question")

class QuestionTranslation(db.Model):
    __tablename__ = 'QuestionTrans'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('Questions.id'), nullable=False)
    language = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    question = db.relationship("Question", back_populates="translations")

class Option(db.Model):
    __tablename__ = 'Options'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('Questions.id'), nullable=False)
    text = db.Column(db.String, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    question = db.relationship("Question", back_populates="options")
    translations = db.relationship("OptionTranslation", back_populates="option")

class OptionTranslation(db.Model):
    __tablename__ = 'OptionTrans'
    id = db.Column(db.Integer, primary_key=True)
    option_id = db.Column(db.Integer, db.ForeignKey('Options.id'), nullable=False)
    language = db.Column(db.String, nullable=False)
    text = db.Column(db.String, nullable=False)
    option = db.relationship("Option", back_populates="translations")

class Attempt(db.Model):
    __tablename__ = 'Attempts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('Quizzes.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String, nullable=False)
    time = db.Column(db.DateTime, nullable=False)

    user = db.relationship('User', backref='attempts')
    quiz = db.relationship('Quiz', backref='attempts')

class Answer(db.Model):
    __tablename__ = 'Answers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('Attempts.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('Questions.id'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('Options.id'), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)