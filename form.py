from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, Length
from flask_ckeditor import CKEditorField


class RegisterForm(FlaskForm):
    name = StringField(label="User Name", validators=[DataRequired()])
    email = StringField(label="User Email", validators=[DataRequired(), Email()])
    password = PasswordField(label="User Password", validators=[DataRequired(),  Length(min=8)])
    button = SubmitField(label="Add Me as User")


class LoginForm(FlaskForm):
    email = StringField(label="User Email", validators=[DataRequired()])
    password = PasswordField(label="User Password", validators=[DataRequired()])
    button = SubmitField(label="Let Me In")


class AddForm(FlaskForm):
    title = StringField(label="Blog Title", validators=[DataRequired()])
    subtitle = StringField(label="Blog Subtitle", validators=[DataRequired()])
    author = StringField(label="Blog Author", validators=[DataRequired()])
    body = CKEditorField(label="Blog Content", validators=[DataRequired()])
    button = SubmitField(label="Add My Blog")


class EditForm(FlaskForm):
    title = StringField(label="Blog New Title", validators=[DataRequired()])
    subtitle = StringField(label="Blog New Subtitle", validators=[DataRequired()])
    body = CKEditorField(label="Blog New Content", validators=[DataRequired()])
    button = SubmitField(label="Add My Edited Blog")


class CommentForm(FlaskForm):
    body = CKEditorField(label="Enter your Comment", validators=[DataRequired()])
    button = SubmitField(label="Add My Comment")


class ContactForm(FlaskForm):
    name = StringField(label="Sender Name", validators=[DataRequired()])
    email = StringField(label="Sender Email", validators=[DataRequired(), Email()])
    subject = StringField(label="Email Subject", validators=[DataRequired()])
    message = StringField(label="Email Message", validators=[DataRequired()])
    button = SubmitField(label="Send My Message")


class DeleteConfirm(FlaskForm):
    user_decision = StringField(label="Are you sur e you want to delete this post. (Yes/NO)")
    button = SubmitField(label="Confirm by decision.")


class AdminCheck(FlaskForm):
    admin_key = PasswordField(label="Enter Admin's Special Key", validators=[DataRequired()])
    button = SubmitField(label="Go")
