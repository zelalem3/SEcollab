from flask import Flask, render_template, request, redirect, url_for, flash,session
from sqlalchemy import Column, String, Integer
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
import datetime
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
import os
import bleach



current_year = datetime.datetime.now().year
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "your_secret_key_here"
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/login'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
PERMANENT_SESSION_LIFETIME = timedelta(seconds=28800)



class Users(UserMixin, db.Model):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), unique=True)
    fname = Column(String, nullable=False)
    lname = Column(String, nullable=False)
    age = Column(String, nullable=False)
    status = Column(String, nullable=False)
    skill1 = Column(String, nullable=False)
    password = Column(String(100))
    date = Column(String, nullable=False)
    country = Column(String, nullable=False)
    City = Column(String, nullable=False)
    blogs = relationship("Blog", back_populates="author")
    comments = relationship("Userscomment", back_populates="user")
    chat = relationship("Chat", back_populates="user")
    followers = relationship("Follower", back_populates="user", foreign_keys="[Follower.following_id]")
    following = relationship("Follower", back_populates="following", foreign_keys="[Follower.follower_id]")

class Chat(db.Model):
    __tablename__ = "chat"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sender_id = Column(Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = Column(Integer, db.ForeignKey('users.id'), nullable=False)
    content = Column(String, nullable=False)
    timestamp = Column(Integer, default=datetime.date.today())
    user = relationship("Users", back_populates="chat")

class Follower(db.Model):
    __tablename__ = "followers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    follower_id = Column(Integer, db.ForeignKey('users.id'))
    following_id = Column(Integer, db.ForeignKey('users.id'))
    user = relationship("Users", back_populates="followers")
    following = relationship("Users", back_populates="following")

class Blog(db.Model):
    __tablename__ = "blogs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    users_id = Column(Integer, db.ForeignKey('users.id'))
    title = Column(String)
    content = Column(String)
    date = Column(String, default=datetime.date.today().strftime("%B %d, %Y"))
    author = relationship("Users", back_populates="blogs")

class Userscomment(db.Model):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, db.ForeignKey('users.id'), nullable=False)
    comment = Column(String, nullable=False)
    user = relationship("Users", back_populates="comments")

with app.app_context():
    db.create_all()



@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))



@app.route("/newpost", methods=["POST", "GET"])
@login_required
def new_post():
    if request.method == "POST":
        title = request.form["title"]
        subtitle = request.form["subtitle"]
        content = request.form["content"]
        authorid = current_user.id

        id = current_user.id
        new_blog = Blog(
            userid= authorid,
            title=title,
            content=content,
        )
        db.session.add(new_blog)
        db.session.commit()

    else:
        return render_template("newpost.html")


@app.route("/edit", methods=["POST", "GET"])
@login_required
def edit():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        github = request.form.get("github")
        pnumber = request.form.get("pnumber")
        adress = request.form.get("adress")
        twitter = request.form.get("twitter")
        aboutme = request.form.get("aboutme")
        project = request.form.get("cv")
        return redirect(url_for('home'))

    else:
        profile_detail = Users.query.filter_by(id=current_user.id)
        return render_template("edit.html", profile=profile_detail)


@app.route("/profile", methods=['GET' , "POST"])
def profile():
    return render_template("myprofile.html")









@app.route("/chat", methods=["GET", "POST"])
def chat():
    return render_template("chat.html")




@app.route("/blogs", methods=["GET", "POST"])

def blogs():
    # page_num = request.args.get('page', 1, type=int)
    items_per_page = 10
    # all_posts= blogs.query.paginate(page=page_num, per_page=items_per_page)
    post = Blog.query.all()
    return render_template("blog.html", all_posts=post)

@app.route("/specficblog/<id>", methods=["GET","POST"])
def showpost(id):
    if request.method == "GET":
        specfic_blog = Blog.query.filter_by(id=id)
        return render_template("specficblog.html", post=specfic_blog)



@app.route("/myblogs", methods=["GET"])
@login_required
def myblogs():
    current_user_id = current_user.id
    myblog = Blog.query.filter_by(user_id=current_user_id)
    return render_template("myblogs.html", all_posts=myblog)



@app.route("/myblogs/<id>", methods=["GET"])
def delete():
    blog = Blog.query.filter_by(id=id)
    db.session.delete(blog)
    db.session.commit()


@app.route("/new-post", methods=["GET", "POST"])
@login_required
def add_new_post():
            if request.method == "post":
                title = bleach.clean(request.get["title"])
                body = bleach.clean(request.get["body"])
                subtitle = bleach.clean(request.get["subtitle"])
                new_blog = Blog(
                    title = title,
                    content = body,
                    users_id = current_user.id,
                )
                db.session.add(new_blog)
                db.session.commit()
                return redirect(url_for('myblogs'))
            else:
                return render_template("newpost.html")
@app.route("/deleteblog/<id>")
@login_required
def deleteblog(id):
    blogs = Blog.query.filter_by(users_id=current_user.id).all()
    if blogs:
        for blog in blogs:
            if blog.id==id:


                db.session.delete(blog)
                db.session.commit()
        return redirect(url_for('myblogs'))
    else:
        return redirect(url_for('myblogs'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        user = Users.query.filter_by(email=email).first()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
        return redirect(url_for('home'))

    else:
        return render_template("login.html")



@app.route('/logout', methods=["GET"])
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))




@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":

        if Users.query.filter_by(email=request.form.get('email')).first():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        if password != confirm_password:
            flash("The password does not match")
            return redirect(url_for('signup'))
        hash_and_salted_password = generate_password_hash(
            password,
            method='pbkdf2:sha256',
            salt_length=8
        )

        new_user = Users(
            email=bleach.clean(request.form['email']),
            Fname=bleach.clean(request.form['Fname']),
            Lname=bleach.clean(request.form['Lname']),
            age=bleach.clean(request.form["age"]),
            twitter=bleach.clean(request.form["twitter"]),
            github=bleach.clean(request.form["github"]),
            status=bleach.clean(request.form["previous"]),



            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("home"))

    else:
        return render_template("signup.html")




@app.route("/about", methods=["GET"])
def about():
    logged_in = current_user.is_authenticated
    return render_template("about.html", logged_in=logged_in)




@app.route("/contact", methods=["GET"])
def contact():
    logged_in = current_user.is_authenticated
    return render_template("contact.html", logged_in=logged_in)




@app.route("/", methods=["GET"])
def home():
    logged_in = current_user.is_authenticated
    return render_template("index.html", logged_in=logged_in)






if __name__ == "__main__":
    app.run(host='0.0.0.0',port=8000, debug=True)

