from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import bleach
import datetime
from datetime import timedelta
from flask import abort, jsonify
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
import random
from sqlalchemy import desc
from sqlalchemy import or_
import smtplib
from werkzeug.utils import secure_filename

import os
from sqlalchemy.sql.expression import func

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



class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), unique=True)
    fname = Column(String, nullable=False)
    lname = Column(String, nullable=False)
    profile_photo = Column(String)
    about_me = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    age = Column(String, nullable=False)
    status = Column(String, nullable=False)
    skills = Column(String, nullable=False)
    portfolio = Column(String)
    password = Column(String(100))
    date = Column(String, nullable=False, default=datetime.date.today().strftime("%B %d, %Y"))
    is_active = db.Column(db.Boolean, default=True)
    country = Column(String, nullable=False)
    City = Column(String, nullable=False)
    twitter = Column(String)
    github = Column(String)
    blogs = relationship("Blog", back_populates="author")
    comments = relationship("Userscomment", back_populates="user")

    collabration = relationship("Collabration", back_populates="user")
    followers = relationship("Follower", foreign_keys="[Follower.user_id]", back_populates="followed_user")
    following = relationship("Follower", foreign_keys="[Follower.follower_id]", back_populates="follower")
    interests = relationship("Interest", back_populates="user")



class Blog(db.Model):
    __tablename__ = "blogs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    users_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String, nullable=False)
    subtitle = Column(String, nullable=False)
    content = Column(String, nullable=False)
    date = Column(String, default=datetime.date.today().strftime("%B %d, %Y"))
    author = relationship("User", back_populates="blogs")

class Follower(db.Model):
    __tablename__ = "followers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    follower_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    followed_user = relationship("User", foreign_keys=[user_id], back_populates="followers")
    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")


class Interest(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    project_id = Column(Integer, ForeignKey('collabration.id'), nullable=False)

    user = relationship("User", back_populates="interests")
    collabration = relationship("Collabration", back_populates="interests")

class Userscomment(db.Model):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    comment = Column(String, nullable=False)
    user = relationship("User", back_populates="comments")

class Collabration(db.Model):
    __tablename__ = "collabration"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    uploaded_date = Column(String, nullable=False, default=datetime.date.today().strftime("%B %d, %Y"))
    requirment = Column(String, nullable=False)
    Looking_for = Column(String, nullable=False)
    due_date = Column(String)
    user = relationship("User", back_populates="collabration")
    interests = relationship("Interest", back_populates="collabration")



with app.app_context():
    db.create_all()




@app.route("/myfollowers", methods=["GET", "POST"])
@login_required
def myfollowers():
    followers = Follower.query.filter_by(user_id=current_user.id).all()
    followers = [follower.follower for follower in followers]
    return render_template("myfollowers.html", followers=followers)


def checkdue_date(allcollaboration):
    for collabration in allcollaboration:
        due_date = datetime.strptime(collabration.due_date, "%B %d, %Y").date()
        if due_date > datetime.date.today():
            db.session.delete(collabration)
    db.session.commit()
@app.route("/myfollwoing", methods=["GET", "POST"])
@login_required
def myfollowing():

    user = User.query.get(current_user.id)


    following = user.following

    return render_template("myfollowing.html", allfollowing=following)




@app.route("/", methods=["GET", "POST"])
def home():

    random_user = User.query.order_by(func.random()).limit(5).all()
    # if random_user.id == current_user.id:
    #     random_user = User.query.order_by(func.random()).limit(5)
    user = {}
    if current_user.is_authenticated:
        user = User.query.filter_by(id=current_user.id).first()
    collabs = Collabration.query.order_by(Collabration.id.desc()).limit(5)
    blog = Blog.query.order_by(Blog.id.desc()).limit(5)

    is_logged_in = current_user.is_authenticated
    return render_template("index.html", is_logged_in=is_logged_in, user=user, collabs=collabs,blogs=blog, random_users=random_user)





@app.route("/deleteinterest/<int:id>", methods=["POST"])
def deleteinterest(id):
    project = Collabration.query.filter_by(id=id).first()
    interests = project.interests
    if not project:
        return jsonify({"message": "Project not found"}), 404

    for interest in interests:

        if interest.user_id == current_user.id:
            db.session.delete(interest)
            db.session.commit()
            response = {"message": "Interest has been deleted successfully."}
            return jsonify(response), 200

        else:
            response = {"message": "Interest has not been deleted try again!"}
            return jsonify(response), 400

    response = {"message": "Interest has not been deleted try again!"}
    return jsonify(response), 400






@app.route("/forgotpassword", methods=["GET", "POST"])
def forgotpassword():
    if request.method == "POST":
        user = User.query.filter_by(id=current_user.id).first()


        smtp_server = "smtp.gmail.com"
        port = 587  # For starttls
        sender_email = "zgetnet24@gmail.com"
        receiver_email = "fikadugetnet428@gmail.com"
        password = "Scooponset1"
        subject = "Test Email"
        body = "This is a plain text email sent from Python using smtplib."
        message = f"Subject: {subject}\n\n{body}"

        try:
            server = smtplib.SMTP(smtp_server, port)
            server.ehlo()  # Can be omitted
            server.starttls()  # Secure the connection
            server.ehlo()  # Can be omitted
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)
            return jsonify("Email sent successfully!")
        except Exception as e:
            print(f"An error occurred: {e}")
            return jsonify("Email sent successfully!")
        finally:
            server.quit()

        referrer = request.referrer
        if referrer:
            return redirect(referrer)


    else:
        return render_template("forgetpassword.html")



@app.route("/followingblogs", methods=["POST", "GET"])
@login_required
def followingblogs():
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    # Get the current user
    user = db.session.get(User, int(current_user.id))

    # Get the IDs of the users the current user follows
    following_users = [follower.followed_user for follower in user.following]

    # Get the blogs of the following users
    following_blogs = (
        Blog.query.filter(Blog.users_id.in_([following_user.id for following_user in following_users]))
        .order_by(desc(Blog.date))
        .offset(offset)
        .limit(per_page)
        .all()
    )
    for blog in following_blogs:
        print(blog.title)
    total_records = Blog.query.filter(
        Blog.users_id.in_([following_user.id for following_user in following_users])).count()
    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    return render_template(
        "following_blogs.html", blogs=following_blogs, page=page, total_pages=total_pages
    )



@app.route("/allcollabration", methods=["GET", "POST"])
@login_required
def allcollbration():
    is_logged_in = current_user.is_authenticated
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    collabrations = Collabration.query.offset(offset).limit(per_page).all()


    total_records = Collabration.query.count()

    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    return render_template("collabration.html", collabrations=collabrations, page=page, total_pages=total_pages,
                           is_logged_in=is_logged_in)











@app.route("/otherfollowing/<int:id>", methods=["GET","POST"])
def otherfollowing(id):
    user = User.query.filter_by(id=id).first()
    followers = Follower.query.filter_by(user_id=id).all()
    followers = [follower.following for follower in followers]
    return render_template("otherfollowing.html", allfollowing=followers, user=user)


@app.route("/otherfollowers/<int:id>", methods=["GET", "POST"])
def otherfollowers(id):
    user = User.query.filter_by(id=id).first()
    followers = Follower.query.filter_by(user_id=id).all()
    followers = [follower.follower for follower in followers]

    return render_template("otherfollowers.html", allfollowers=followers, user=user)



@app.route("/changepassword", methods=["GET"])
@login_required
def changepassword():
    return render_template("changepassword.html")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))







@app.route("/login", methods=["GET", "POST"])
def login():
    is_logged_in = current_user.is_authenticated
    if request.method == "POST":
        email = bleach.clean(request.form['email'])
        password = bleach.clean(request.form['password'])
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("That email does not exist, please try again.")

            return redirect(url_for('login'))

        if not check_password_hash(user.password, password):
            flash('Incorrect password, please try again.')

            return redirect(url_for('login'))
        login_user(user)


        return redirect(url_for('home'))

    return render_template("login.html",  is_logged_in=is_logged_in)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    is_logged_in = current_user.is_authenticated
    if request.method == "POST":

        email = bleach.clean(request.form['email'])
        password = bleach.clean(request.form['password'])
        confirm_password = bleach.clean(request.form['confirm-password'])
        first_name = bleach.clean(request.form['first_name'])
        last_name = bleach.clean(request.form['last_name'])
        twitter = bleach.clean(request.form['twitter'])
        github = bleach.clean(request.form['github'])
        country = bleach.clean(request.form['country'])
        city = bleach.clean(request.form['City'])
        usersage = bleach.clean(request.form['age'])
        skills = bleach.clean(request.form['skills'])
        status = bleach.clean(request.form['status'])
        phone_number = bleach.clean(request.form['phone_number'])
        about_me = bleach.clean(request.form["about_me"])
        image_path = None
        if 'image' in request.files and request.files['image'].filename != '':
            image = request.files['image']
            ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
            if image.filename.split('.')[-1].lower() in ALLOWED_EXTENSIONS:
                destination_folder = os.path.join('static', 'images')
                image_path = os.path.join('static', 'images', secure_filename(image.filename))
                image.save(image_path)

        if confirm_password != password:
            flash("yout confirmation password does not match the password")
            return redirect(url_for('signup'))

        if User.query.filter_by(email=request.form.get('email')).first() is not None:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        if not email or not password or not first_name or not last_name or not phone_number:
            flash("Please fill in all the required fields.")
            return redirect(url_for('signup'))

        if len(password) < 5:
            flash("Password should be at least 5 characters long.")
            return redirect(url_for('signup'))

        hash_and_salted_password = generate_password_hash(
            password,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            fname=first_name,
            lname=last_name,
            phone_number=phone_number,
            email=email,
            twitter=twitter,
            github=github,
            status=status,
            skills=skills,
            age=usersage,
            country=country,
            City=city,
            about_me=about_me,
            profile_photo=image_path,
             password=hash_and_salted_password
        )

        db.session.add(new_user)
        db.session.commit()


        login_user(new_user)

        return redirect(url_for("home"))

    return render_template("signup.html", is_logged_in=is_logged_in)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    is_logged_in = current_user.is_authenticated
    return render_template("contact.html", is_logged_in=is_logged_in, year=current_year)


@app.route("/about", methods=["GET", "POST"])
def about():
    is_logged_in = current_user.is_authenticated
    return render_template("about.html", is_logged_in=is_logged_in, year=current_year)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/allblogs")
@login_required
def allblogs():
    is_logged_in = current_user.is_authenticated
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    blogs = Blog.query.order_by(Blog.id.desc()).offset(offset).limit(per_page).all()

    total_records = Blog.query.count()

    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    return render_template("allblog.html", blogs=blogs, page=page, total_pages=total_pages, is_logged_in=is_logged_in)


@app.route("/blogs/<id>")
@login_required
def Specficblog(id):
    blog = Blog.query.filter_by(id=id).first()
    user = User.query.filter_by(id=blog.users_id).first()
    return render_template("specficblog.html", blog=blog, user=user)


@app.route("/myblogs", methods=["GET", "POST"])
@login_required
def myblogs():
    blogs = Blog.query.filter_by(users_id=current_user.id).all()
    return render_template("myblogs.html", blogs=blogs)

#
@app.route("/editblog/<id>", methods=["GET", "POST"])
@login_required
def editblog(id):
    if request.method == "POST":
        title = bleach.clean(request.form['title'])
        subititle = bleach.clean(request.form['subtitle'])
        content = bleach.clean(request.form["content"])
        blog = Blog.query.filter_by(id=id)
        blog.title = title
        blog.subtitle = subititle
        blog.content = content
        db.session.commit()
        return redirect(url_for('myblog'))
    else:
        blog = Blog.query.filter_by(id=id).first()
        return render_template("editblog.html", blog=blog)


@app.route("/myblogs/delete/<int:id>")
@login_required
def deleteblog(id):
    blogs = Blog.query.filter_by(users_id=current_user.id).all()
    if blogs:
        for blog in blogs:
            if blog.id == id:
                db.session.delete(blog)
                db.session.commit()
        return redirect(url_for('myblogs'))

    else:
        return render_template("myblogs.html")


@app.route("/editprofile", methods=["POST", "GET"])
@login_required
def editprofile():
    if request.method == "POST":

            user = User.query.filter_by(id=current_user.id).first()
            email = bleach.clean(request.form['email'])
            first_name = bleach.clean(request.form['first_name'])
            last_name = bleach.clean(request.form['last_name'])
            twitter = bleach.clean(request.form['twitter'])
            github = bleach.clean(request.form['github'])
            country = bleach.clean(request.form['country'])
            city = bleach.clean(request.form['City'])
            usersage = bleach.clean(request.form['age'])
            skills = bleach.clean(request.form['skills'])
            status = bleach.clean(request.form['status'])
            about_me = bleach.clean(request.form["about_me"])
            image_path = None
            if 'image' in request.files and request.files['image'].filename != '':
                image = request.files['image']
                if image is not None:
                    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
                    if image.filename.split('.')[-1].lower() in ALLOWED_EXTENSIONS:
                        destination_folder = os.path.join('static', 'images')

                        image_path = os.path.join('static', 'images', secure_filename(image.filename))

                        image.save(image_path)


            user.email = email
            user.first_name = first_name
            user.twitter = twitter
            user.github = github
            user.country = country
            user.City = city
            user.age = usersage
            user.skills = skills
            user.status = status
            user.profile_photo = image_path
            user.about_me = about_me
            db.session.commit()
            return redirect(url_for('myprofile'))

    else:
            user = User.query.filter_by(id=current_user.id).first()
            return render_template("editprofile.html", user=user)






@app.route("/myprofile", methods=['GET' , "POST"])
@login_required
def myprofile():
    userid = current_user.id
    user = User.query.filter_by(id=userid).first()
    return render_template("myprofile.html", user=user)





@app.route("/newblog",methods=['GET', "POST"])
@login_required
def newblog():
    if request.method == "POST":

        user_id = current_user.id
        new_blog = Blog(
            title=request.form.get("title"),
            content=request.form.get("content"),
            subtitle=request.form.get("subtitle"),
            users_id=user_id,
        )
        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for('myblogs'))
    else:
        return render_template("newblog.html")

@app.route("/header", methods=['GET', "POST"])
def header():
    is_logged_in = current_user.is_authenticated
    return render_template("header.html", is_logged_in=is_logged_in)


@app.route("/interest/<int:id>", methods=["POST"])
@login_required
def interest(id):
    new_interest = Interest(
        user_id= current_user.id,
        project_id=id,

    )
    db.session.add(new_interest)
    db.session.commit()
    response = {"message": "Follower added successfully."}
    return jsonify(response), 200






@app.route("/collab/<int:id>", methods={"GET"})
@login_required
def specficcollabration(id):
    collab=Collabration.query.filter_by(id=id).first()
    return render_template("specficcollab.html", collab=collab)


@app.route("/message", methods=["GET", "POST"])
@login_required
def message():
    return render_template("message.html")




@app.route("/addcollabration" ,methods=["GET", "POST"])
@login_required
def addcollab():
    if request.method == "POST":
        current_date = datetime.date.today().isoformat()
        name = bleach.clean(request.form["name"])
        requirments = bleach.clean(request.form["requirment"])
        description = bleach.clean(request.form["description"])
        looking_for = bleach.clean(request.form["lookingfor"])
        user_id = current_user.id
        due_date = bleach.clean(request.form["Date"])

        if due_date <= current_date:
            flash("You did not enter a valid date.")
            return redirect(url_for('addcollab'))


        new_collabration = Collabration(
            user_id= user_id,
            name=name,
            description=description,
            requirment=requirments,
            Looking_for=looking_for,
            due_date=due_date,
        )
        db.session.add(new_collabration)
        db.session.commit()
        return redirect(url_for('myprojects'))
    else:
        return render_template("addcollabration.html")




@app.route("/myproject", methods=["GET", "POST"])
@login_required
def myprojects():
    user_id = current_user.id
    projects = Collabration.query.filter_by(user_id=user_id)
    return render_template("myproject.html", projects=projects)

@app.route("/otherprojects/<int:id>", methods=["GET"])
@login_required
def otherprojects(id):
    projects = Collabration.query.filter_by(user_id=id, )
    return render_template("otherprojects.html", projects=projects)

@app.route("/deleteproject/<id>", methods=["POST", "GET"])
@login_required
def deleteproject(id):
    if request.method == "POST":
        users_id = current_user.id
        project = Collabration.query.filter_by(id=id).first()
        if project:
            if project.user_id == users_id:
                db.session.delete(project)
                db.session.commit()
                return redirect(url_for('myprojects'))

        else:
            return abort(404)






@app.route("/searchprofile/<namepattern>", methods=["GET", "POST"])
@login_required
def searchprofile(namepattern):
    results =result = User.query.filter(User.fname.like(f'%{namepattern}%'), User.id != current_user.id).all()
    return render_template("searchprofile.html", results=results, pattern=namepattern)


@app.route("/searchblog/<titleofblog>", methods=['GET', "POST"])
@login_required
def searchblog(titleofblog):
    results = Blog.query.filter(Blog.title.like(f'%{titleofblog}%')).all()
    return render_template("searchblog.html", results=results, titleofblog=titleofblog)





@app.route("/otherusers")
@login_required
def otherusers():
    is_logged_in = current_user.is_authenticated
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    users = User.query.filter(User.id != current_user.id).offset(offset).limit(per_page).all()
    random.shuffle(users)

    total_records = User.query.count()

    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    return render_template("otherusers.html", users=users, page=page, total_pages=total_pages, is_logged_in=is_logged_in)



@app.route("/follow/<int:id>", methods=["POST"])
@login_required
def follow(id):
    user_id = current_user.id
    if id == user_id:
        response = {"Message": "Follower not added already followed"}
        flash("You can follow yourself")
        return jsonify(response), 200

    followers = Follower.query.filter_by(user_id=user_id).all()
    for follower in followers:
        if follower.follower_id == user_id:
            response = {"Message": "Follower not added already followed"}
            flash("already follows that user")
            return jsonify(response), 200
    new_follower = Follower(user_id=id, follower_id=user_id)

    db.session.add(new_follower)
    db.session.commit()

    # Return a JSON response indicating the success of the request
    response = {"message": "Follower added successfully."}
    return jsonify(response), 200



@app.route("/allfollowers/<int:id>", methods=["GET", "POST"])
@login_required
def allfollowers(id):
    followers = Follower.query.filter_by(user_id=id).all()
    followers = followers.followers
    return render_template("allfollowers.html", followers=followers)




@app.route("/allfollwing", methods=["GET", "POST"])
@login_required
def allfollowing():
    is_logged_in = current_user.is_authenticated
    followers = Follower.query.filter_by(user_id=current_user.id)
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    follwoing = followers.query.offset(offset).limit(per_page).all()

    users = random.shuffle(followers)

    total_records = User.query.count()

    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    return render_template("otherusers.html", users=users, page=page, total_pages=total_pages,
                           is_logged_in=is_logged_in)



@app.route("/deleteaccount", methods=["GET", "POST"])
@login_required
def deleteaccount():
    if request.method == "POST":
        user = User.query.filter_by(id=current_user.id).first()
        logout_user()
        db.session.delete(user)
        db.session.commit()
        return redirect(url_for('home'))
    else:
        return render_template("deleteaccount.html")


from flask import jsonify


@app.route("/unfollow/<int:follower_id>", methods=["POST"])
@login_required
def unfollow(follower_id):
    user_id = current_user.id

    following = Follower.query.filter_by(follower_id=user_id, id=follower_id).first()

    if following:

        db.session.delete(following)
        db.session.commit()
        response = {"message": "Follower unfollowed successfully."}
        return jsonify(response), 200
    else:
        response = {"message": "No such follower found to unfollow."}
        return jsonify(response), 404


@app.route("/profile/<int:id>", methods=["GET", "POST"])
@login_required
def profile(id):
    user = User.query.filter_by(id=id).first()
    return render_template("otherprofile.html", user=user)



@app.route("/interestinmyproject", methods=["GET"])
@login_required
def interestinmyproject():
    user = User.query.filter_by(id=current_user.id).first()
    projects = Collabration.query.filter_by(user_id=current_user.id).all()
    if projects:

        return render_template("interestinmyproject.html", projects=projects)





@app.route("/interestinmyproject/<int:id>", methods=["GET"])
@login_required
def specficinterestinmyproject(id):
    return render_template("specficinterestinmyproject.html")



@app.route("/explore", methods=["GET"])
def explore():
    return render_template("explore.html")



@app.route("/registeredinterest", methods=["GET"])
@login_required
def registeredInterest():
    user = User.query.filter_by(id=current_user.id).first()
    interests = user.interests
    all_interest = Interest.query.filter_by(user_id=current_user.id).all()

    return render_template('Registeredinterest.html', interests=interests, all_interest=all_interest)




# allcollaboration = Collabration.query.all()
# checkdue_date(allcollaboration)
if __name__ == '__main__':

    app.run(debug=True, port=5000)
