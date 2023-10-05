import os
from datetime import date
from smtplib import SMTP
from flask import Flask, render_template, redirect, url_for, flash, abort, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy.orm import relationship
from form import RegisterForm, LoginForm, AddForm, EditForm, CommentForm, ContactForm, AdminCheck, DeleteConfirm

MY_EMAIL = os.getenv("my_email")
MY_PASSWORD = os.getenv("my_password")

app = Flask(__name__)
app.secret_key = os.getenv("secret_key")

# bootstrap
Bootstrap5(app)

# ckeditor
ckeditor = CKEditor(app)

# Gravatar
gravatar = Gravatar(app,
                    size=30,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

# database
db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("db_url")
db.init_app(app)

# login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# Create an admin-only decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.id == 1:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)


    # This will act like a list of BlogPost objects attached to each User.
    # The "author" refers to the author property in the BlogPost class.
    posts = relationship("BlogPost", back_populates="author")


    # Parent relationship: "comment_author" refers to the comment_author property in the Comment class.
    comments = relationship("Comment", back_populates="comment_author")

    def to_dict(self):
        # # Method 1.
        # dictionary = {}
        # # Loop through each column in the data record
        # for column in self.__table__.columns:
        #     # Create a new dictionary entry;
        #     # where the key is the name of the column
        #     # and the value is the value of the column
        #     dictionary[column.name] = getattr(self, column.name)
        # return dictionary

        # Method 2. Altenatively use Dictionary Comprehension to do the same thing.
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class BlogPost(db.Model):
    __tablename__ = "blogpost"
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    title = db.Column(db.String, nullable=False)
    subtitle = db.Column(db.String, nullable=False)
    body = db.Column(db.String, nullable=False)
    date = db.Column(db.String, nullable=False)


    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # Create reference to the User object. The "posts" refers to the posts property in the User class.
    author = relationship("User", back_populates="posts")

    def to_dict(self):
        return {column.name : getattr(self, column.name) for column in self.__table__.columns}


    # Parent relationship to the comments
    comments = relationship("Comment", back_populates="parent_blog")


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    body = db.Column(db.String, nullable=False)


    # Child relationship:"users.id" The users refers to the tablename of the User class.
    # "comments" refers to the comments property in the User class.
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")


    # Child Relationship to the BlogPosts
    post_id = db.Column(db.Integer, db.ForeignKey("blogpost.id"))
    parent_blog = relationship("BlogPost", back_populates="comments")


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for("login"))

        hashed_password = generate_password_hash(
            password=form.password.data,
            method='pbkdf2:sha256',
            salt_length=10
        )
        new_user = User(
            name=form.name.data,
            email=form.email.data,
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for("domain", existing_user=False))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, form.password.data):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for("domain", existing_user=True))
    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/blogs")
def show_all_blogs():
    result = db.session.execute(db.select(BlogPost).order_by(desc(BlogPost.date)))
    list_of_blogs = result.scalars().all()
    return render_template("show_all_blogs.html", blogs=list_of_blogs)


@app.route("/show_blog", methods=["GET", "POST"])
def show_blog():
    form = CommentForm()
    id = request.args.get("blog_id")
    required_blog = db.get_or_404(BlogPost, id)

    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))

        new_comment = Comment(
            body=form.body.data,
            comment_author=current_user,
            parent_blog=required_blog
        )
        db.session.add(new_comment)
        db.session.commit()

    return render_template("show_blog.html", blog=required_blog, form=form)


@app.route("/domain")
@login_required
def domain():
    user_status = request.args.get('existing_user')
    return render_template("domain.html", existing_user=user_status)


@app.route("/domain/blogger/<name>")
@login_required
def show_all_user_blogs(name):
    result = db.session.execute(db.select(BlogPost).where(BlogPost.author_id == current_user.id))
    blogs = result.scalars().all()
    return render_template('blogs.html', blogs=blogs)


@app.route("/add_blog", methods=["GET", "POST"])
@login_required
def add_blog():
    form = AddForm(
        author=current_user.name
    )
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            author=current_user,
            date=date.today(),
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("show_all_user_blogs", name=current_user.name))
    return render_template("add_blog.html", form=form)


@app.route("/edit_blog", methods=["GET", "POST"])
def edit_blog():
    id = request.args.get("blog_id")
    required_post = db.get_or_404(BlogPost, id)
    form = EditForm(
        title=required_post.title,
        subtitle=required_post.subtitle,
        body=required_post.body
    )
    if form.validate_on_submit():
        required_post.title = form.title.data
        required_post.subtitle = form.subtitle.data
        required_post.body = form.body.data
        required_post.date = date.today()
        db.session.commit()
        return redirect(url_for("show_all_user_blogs", name=current_user.name))
    return render_template("edit_blog.html", form=form)


@app.route("/delete", methods=["GET","POST"])
def delete():
    form = DeleteConfirm()
    if form.validate_on_submit():
      id = request.args.get("blog_id")
      required_post = db.get_or_404(BlogPost, id)
      db.session.delete(required_post)
      db.session.commit()
          return redirect(url_for("show_all_user_blogs", name=current_user.name))
    return render_template("confirm_delete.html", form=form)


@app.route("/user")
@admin_only
@login_required
def show_user():
      result = db.session.execute(db.select(User).order_by(User.name))
      list_of_users = result.scalars().all()
      return render_template("show_user.html", users=list_of_users)


# @app.route("/delete_user")
# def delete_user():
#     id = request.args.get("user_id")
#     required_user = db.get_or_404(User, id)
#     required_blog = db.session.execute(db.select(BlogPost).where(BlogPost.author.id == id))
#     required_comment = db.session.execute(db.select(Comment).where(Comment.comment_author.id == id))
#     db.session.delete(required_comment)
#     db.session.delete(required_blog)
#     db.session.delete(required_user)
#     db.session.commit()
#     return redirect(url_for("show_user"))


@app.route("/contact", methods=["GET","POST"])
def contact():
    # if not current_user.is_authenticated:
    #     flash("You need to sign in to contact")
    form = ContactForm()
    if form.validate_on_submit():
        with SMTP("smtp.gmail.com") as connection:
            connection.starttls()
            connection.login(user=MY_EMAIL, password=MY_PASSWORD)
            connection.sendmail(
                from_addr=form.email.data,
                to_addrs=MY_EMAIL,
                msg=f"Subject:{form.subject.data}\n\nName: {form.name.data}\n Email: {form.email.data}\n{form.message.data}"
            )
        return redirect(url_for("home"))
    return render_template("contact.html", form=form)


@app.route("/user/data", methods=["GET","POST"])
@login_required
@admin_only
def get_user_data():
    id = request.args.get("user_id")
    form = AdminCheck()
    if form.validate_on_submit():
        if form.admin_key.data == "AdminArea":
            result = db.session.execute(db.select(User).where(User.id == id))
            all_user = result.scalars().all()
            # print(all_cafes)
            # all_cafe_dictionary = {}
            # cafe_dictionary_list = []
            # for i in range(len(all_cafes)):
            #     cafe_dictionary = all_cafes[i].to_dict()
            #     cafe_dictionary_list.append(cafe_dictionary)
            #     all_cafe_dictionary["Cafe"] = cafe_dictionary_list
            return jsonify(users=[user.to_dict() for user in all_user])
        else:
            return abort(403)
    return render_template("show_user_datas.html", form=form)


@app.route("/user/posts", methods=["GET","POST"])
def get_user_posts():
    id = request.args.get("user_id")
    form = AdminCheck()
    if form.validate_on_submit():
        if form.admin_key.data == "AdminArea":
            result = db.session.execute(db.select(BlogPost).where(BlogPost.author_id == id))
            all_posts = result.scalars().all()
            if all_posts:
                return jsonify(posts=[post.to_dict() for post in all_posts])
            else:
                return jsonify(error={"Not Found": "No any post yet."})
        else:
            return abort(403)
    return render_template("show_user_datas.html", form=form)


@app.route("/delete/user and post", methods=["GET","POST"])
def delete_user_and_post():
    id = request.args.get("user_id")
    form = AdminCheck()
    if form.validate_on_submit():
        if form.admin_key.data == "AdminArea":
            result = db.get_or_404(User, id)
            db.session.delete(result)
            db.session.commit()
            return jsonify(result={"success": "Successfully Deleted."})
        else:
            return abort(403)
    return render_template("show_user_datas.html", form=form)


if __name__ == "__main__":
    app.run(debug=False)
