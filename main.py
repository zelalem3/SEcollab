import random
from sqlalchemy import desc
import smtplib
from werkzeug.utils import secure_filename
from datetime import timedelta
import datetime
import os
from sqlalchemy.sql.expression import func
from flask_login import login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import bleach
from models import User,Blog,Collabration,LikedBlog,Follower,Message,Interest,Userscomment,app,db
from datetime import timedelta
from flask import abort, jsonify
from flask import render_template, request, redirect, url_for, flash
current_year = datetime.datetime.now().year

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/login'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
PERMANENT_SESSION_LIFETIME = timedelta(seconds=28800)


@app.route("/addoremovelike/<int:id>", methods=["POST"])
@login_required
def addoremovelike(id):
    user_id = current_user.id
    try:
        blog = Blog.query.filter_by(id=id).first()
        liked_blog = LikedBlog.query.filter_by(user_id=current_user.id, blog_id=id).first()
        if blog:
            if blog.user_id != user_id:

                if current_user not in blog.liking_users:
                    blog.like += 1
                    blog.liking_users.append(current_user)
                    db.session.commit()
                    response = {"message": "like added"}
                    return jsonify(response), 200

                else:
                    db.session.delete(liked_blog)
                    blog.like -= 1
                    db.session.commit()
                    response = {"message": "Like Removed"}
                    return jsonify(response), 200

            else:
                response = {"message": "You can't like your own blog"}
                return jsonify(response), 403
        else:
            response = {"message": "Blog is not found"}
            return jsonify(response), 404
    except Exception as e:
        response = {"message": f"Internal server error: {str(e)}"}
        print(e)  # Print the exception for debugging purposes
        return jsonify(response), 500


@app.route("/topblogs", methods=["GET"])
def TopBlogs():
    user = User.query.filter_by(id=current_user.id).first()
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    blogs = Blog.query.filter(Blog.user_id != current_user.id).order_by(Blog.like.desc()).offset(offset).limit(per_page).all()


    total_pages = 3

    return render_template("topblogs.html", blogs=blogs, page=page, user=user, total_pages=total_pages)



@app.route("/accept/<int:id>/<int:userid>", methods=["POST"])
@login_required
def accept(id, userid):
    project = Collabration.query.get(id)
    if project:
        if current_user.id == project.user_id:
            user = User.query.get(userid)
            if user:
                project.members.append(user)
                interest = Interest.query.filter_by(user_id=userid).first()
                db.session.delete(interest)
                db.session.commit()
                response = {"message": "User added to the team successfully"}
                return jsonify(response), 200
            else:
                response = {"message": "User not found"}
                return jsonify(response), 404
        else:
            response = {"message": "Current user is not the project owner"}
            return jsonify(response), 403
    else:
        response = {"message": "Project not found"}
        return jsonify(response), 404

@app.route("/followedprojects", methods=["GET", "POST"])
def followedprojects():
    id = current_user.id

@app.route("/follow/<int:id>", methods=["POST"])
@login_required
def follow(id):
    try:
        user_id = current_user.id
        if id == user_id:
            response = {"message": "You can't follow yourself"}
            return jsonify(response), 400

        user = User.query.filter_by(id=current_user.id).first()
        if id in [following.id for following in user.following]:

            for following in user.following:
                print(following.id)
            flash("you already follow that user")
            response = {"message": "You are already following this user"}
            return jsonify(response), 400

        new_follower = Follower(user_id=id, follower_id=user_id)
        db.session.add(new_follower)
        db.session.commit()

        response = {"message": "Follower added successfully."}
        return jsonify(response), 200


    except Exception as e:
        # Log the error and return an error response
        app.logger.error(f"An error occurred: {str(e)}")
        response = {"message": "An error occurred"}
        return jsonify(response), 500


@app.route("/interestinmyproject/<int:id>", methods=["GET"])
@login_required
def specficinterestinmyproject(id):
    project = Collabration.query.filter_by(id=id).first()
    user = User.query.filter_by(id=current_user.id).first()
    Team = Collabration.query.filter_by(id=id).first()
    team = Team.members
    if project:
        if project.user_id == current_user.id:
            all_interest = project.interests
            return render_template("interestinmyproject.html", interests=all_interest, project=project, user=user, team=team)
    else:
         return jsonify("NO project was found!!")


@app.route("/myfollowers", methods=["GET", "POST"])
@login_required
def myfollowers():
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    followers = Follower.query.filter_by(user_id=current_user.id).offset(offset).limit(per_page).all()
    followers = [follower.follower for follower in followers]

    user = User.query.filter_by(id=current_user.id).first()

    total_records = User.query.count()

    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    return render_template("myfollowers.html", user=user, page=page, total_pages=total_pages, followers=followers)



@app.route("/myfollowing", methods=["GET", "POST"])
@login_required
def myfollowing():
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    user = User.query.get(current_user.id)
    following = Follower.query.filter_by(follower_id=current_user.id).offset(offset).limit(per_page).all()


    total_records = User.query.count()

    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)


    return render_template("myfollowing.html", allfollowing=following, user=user, page=page, total_pages=total_pages)




@app.route("/", methods=["GET", "POST"])
def home():

    allcollaboration = Collabration.query.all()
    checkdue_date(allcollaboration)

    if current_user.is_authenticated:
        random_users = User.query.filter(User.id != current_user.id).order_by(func.random()).limit(5).all()
        user = User.query.filter_by(id=current_user.id).first()
        collabs = Collabration.query.filter(Collabration.user_id != current_user.id).order_by(Collabration.id.desc()).limit(5)
        blog = Blog.query.filter(Blog.user_id != current_user.id).order_by(Blog.id.desc()).limit(5)

        is_logged_in = current_user.is_authenticated
        return render_template("index.html", is_logged_in=is_logged_in, user=user, collabs=collabs, blogs=blog, random_users=random_users)
    else:
        return render_template("index.html")




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

@app.route("/forgotpasswordloggedin", methods=["GET", "POST"])
@login_required
def forgetpassword():
    user = User.query.filter_by(id=current_user.id).first()
    user_email = user.email
    if request.method == "POST":
        mailuser = 'zgetnet24@gmail.com'
        mailpasswd = 'Scooponset1'
        fromaddr = 'zgetnet24@gmail.com'
        toaddrs = "zelalem328@gmail.com"
        msg = 'Subject: Test Email\n\nThis is a test email from Python.'
        if user:
            try:
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.login(mailuser, mailpasswd)
                server.sendmail(fromaddr, toaddrs, msg)
                print("Email sent successfully!")
            except Exception as e:
                print(f"An error occurred: {e}")
            finally:
                server.quit()
        return redirect(url_for('home'))
    else:
        return render_template("forgetpassword.html", email=user_email, user=user)





@app.route("/forgotpasswordloggedout", methods=["GET", "POST"])
def forgetpasswordloggedout():
    user = []
    if request.method == "POST":
        email = request.form["email"]
        user = User.query.filter_by(email=email).first()
        mailuser = 'zgetnet24@gmail.com'
        mailpasswd = 'Scooponset1'
        fromaddr = 'zgetnet24@gmail.com'
        toaddrs = "zelalem328@gmail.com"
        msg = 'Subject: Test Email\n\nThis is a test email from Python.'
        if user:
            try:
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.login(mailuser, mailpasswd)
                server.sendmail(fromaddr, toaddrs, msg)
                print("Email sent successfully!")
            except Exception as e:
                print(f"An error occurred: {e}")
            finally:
                server.quit()
        return redirect(url_for('home'))
    else:
        return render_template("forgetpasswordloggedout.html",  user=user)


@app.route("/emailsent", methods=["GET"])
def emailsent():
    return render_template("emailsent.html")


@app.route("/followingblogs", methods=["POST", "GET"])
@login_required
def followingblogs():
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    user = User.query.filter_by(id=current_user.id).first()
    # Get the current user
    user = db.session.get(User, int(current_user.id))

    # Get the IDs of the users the current user follows
    following_users = [follower.followed_user for follower in user.following]

    # Get the blogs of the following users
    following_blogs = (
        Blog.query.filter(Blog.user_id.in_([following_user.id for following_user in following_users]))
        .order_by(desc(Blog.date))
        .offset(offset)
        .limit(per_page)
        .all()
    )
    for blog in following_blogs:
        print(blog.title)
    total_records = Blog.query.filter(
        Blog.user_id.in_([following_user.id for following_user in following_users])).count()
    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    return render_template(
        "following_blogs.html", blogs=following_blogs, page=page, total_pages=total_pages, user=user
    )



@app.route("/allcollabration", methods=["GET", "POST"])
@login_required
def allcollbration():
    user = User.query.filter_by(id=current_user.id).first()
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    #query all the results excluding all the projects which the owner is the current user
    collabrations = Collabration.query.filter(Collabration.user_id != current_user.id).offset(offset).limit(per_page).all()

    #Get the number of pages
    total_records = Collabration.query.count()

    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    return render_template("collabration.html", collabrations=collabrations, page=page, total_pages=total_pages,
                          user=user)











@app.route("/otherfollowing/<int:id>", methods=["GET","POST"])
def otherfollowing(id):
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    user = User.query.get(current_user.id)
    following = Follower.query.filter_by(follower_id=id).offset(offset).limit(per_page).all()
    total_records = User.query.count()

    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    return render_template("otherfollowing.html", allfollowing=following, user=user, page=page, total_pages=total_pages)




@app.route("/otherfollowers/<int:id>", methods=["GET", "POST"])
def otherfollowers(id):
    #query the user
    user = User.query.filter_by(id=id).first()
    #query from from the follower table
    followers = Follower.query.filter_by(user_id=id).all()
    #query all the followers of that user
    followers = [follower.follower for follower in followers]
    #render the page
    return render_template("otherfollowers.html", allfollowers=followers, user=user)


@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():
    #query the current user
    user = User.query.filter_by(id=current_user.id).first()
    if request.method == "POST":
        #Get the current password from form
        old_password = request.form.get("password")
        #check if it is correct
        if not check_password_hash(user.password, old_password):
            flash('Incorrect password, please try again.')
            return redirect(url_for('changepassword'))
        #get the new password from the form
        new_password = request.form["newpassword"]
        #get the confirmation passsword from the form
        confirm_password = request.form["confirm-password"]
        #check if new_password and confirm_password are not the same
        if new_password != confirm_password:
            flash("Confirmation password is not the same as the password you entered.")
            return redirect(url_for('changepassword'))
        #hash the new password
        hash_and_salted_password = generate_password_hash(
            new_password,
            method='pbkdf2:sha256',
            salt_length=8
        )
        #change the old password with the new one
        user.password = hash_and_salted_password
        #commit the changes to the database
        db.session.commit()

        flash("Password changed successfully.")
        return redirect(url_for('home'))

    return render_template("changepassword.html", user=user)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))







@app.route("/login", methods=["GET", "POST"])
def login():

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

    return render_template("login.html")


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
        status = bleach.clean(request.form['about_me'])
        phone_number = bleach.clean(request.form['phone_number'])
        about_me = bleach.clean(request.form["about_me"])
        portfolio = bleach.clean(request.form["previous"])
        username = bleach.clean(request.form["username"])
        employment_status = request.form['employment-status']
        education_level = request.form['education-level']





        image_path = "static/images/noprofile.jpg"
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
            portfolio=portfolio,
            username=username,
            employment_status=employment_status,
            education_status=education_level,
             password=hash_and_salted_password,
        )


        db.session.add(new_user)
        db.session.commit()


        login_user(new_user)

        return redirect(url_for("home"))

    return render_template("signup.html", is_logged_in=is_logged_in)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    user = User.query.filter_by(id=current_user.id).first()
    if request.method == "POST":
        name = bleach.clean(request.form["name"])
        email = bleach.clean(request.form["email"])
        phone = bleach.clean(request.form["phone"])
        message = bleach.clean(request.form["message"])
        new_message = Message(
            name=name,
            phone=phone,
            email=email,
            message=message,
        )

        db.session.add(new_message)
        db.session.commit()
        flash("your message has been Recieved")
        return redirect(url_for('contact'))

    else:
        is_logged_in = current_user.is_authenticated
        return render_template("contact.html", is_logged_in=is_logged_in, user=user)


@app.route("/about", methods=["GET", "POST"])
def about():
    is_logged_in = current_user.is_authenticated
    user = User.query.filter_by(id=current_user.id).first()
    return render_template("about.html", is_logged_in=is_logged_in, year=current_year, user=user)


@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/allblogs")
@login_required
def allblogs():

    user = User.query.filter_by(id=current_user.id).first()
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    blogs = Blog.query.order_by(Blog.date.desc(), Blog.like.desc()).offset(offset).limit(per_page).all()

    total_records = Blog.query.count()

    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    return render_template("allblog.html", blogs=blogs, page=page, user=user,total_pages=total_pages)


@app.route("/blogs/<id>")
@login_required
def Specficblog(id):

    blog = Blog.query.filter_by(id=id).first()
    user = User.query.filter_by(id=blog.user_id).first()
    return render_template("specficblog.html", blog=blog, user=user)


@app.route("/myblogs", methods=["GET", "POST"])
@login_required
def myblogs():

    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    blogs = Blog.query.filter_by(user_id=current_user.id).offset(offset).limit(per_page).all()
    user = User.query.filter_by(id=current_user.id).first()

    total_records = Blog.query.count()

    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    return render_template("myblogs.html", user=user, page=page, total_pages=total_pages, blogs=blogs)




#
@app.route("/editblog/<id>", methods=["GET", "POST"])
@login_required
def editblog(id):
    user = User.query.filter_by(id=current_user.id).first()
    if request.method == "POST":
        title = bleach.clean(request.form['title'])
        subititle = bleach.clean(request.form['subtitle'])
        content = bleach.clean(request.form["content"])
        blog = Blog.query.filter_by(id=id)
        blog.title = title
        blog.subtitle = subititle
        blog.content = content
        db.session.commit()
        return redirect(url_for('myblogs'))
    else:
        blog = Blog.query.filter_by(id=id).first()
        return render_template("editblog.html", blog=blog, user=user)


@app.route("/myblogs/delete/<int:id>", methods=["POST"])
@login_required
def deleteblog(id):
    user = User.query.filter_by(id=current_user.id).first()
    blogs = Blog.query.filter_by(user_id=current_user.id).all()
    if blogs:
        for blog in blogs:
            if blog.id == id:
                db.session.delete(blog)
                db.session.commit()
        return redirect(url_for('myblogs'))

    else:
        return render_template("myblogs.html", user=user)


@app.route("/editprofile", methods=["POST", "GET"])
@login_required
def editprofile():
    user = User.query.filter_by(id=current_user.id).first()
    if request.method == "POST":


            email = bleach.clean(request.form['email'])

            first_name = bleach.clean(request.form['first_name'])
            last_name = bleach.clean(request.form['last_name'])
            twitter = bleach.clean(request.form['twitter'])
            github = bleach.clean(request.form['github'])
            country = bleach.clean(request.form['country'])
            city = bleach.clean(request.form['City'])
            usersage = bleach.clean(request.form['age'])
            skills = bleach.clean(request.form['skills'])
            status = bleach.clean(request.form['about_me'])
            phone_number = bleach.clean(request.form['phone_number'])
            about_me = bleach.clean(request.form["about_me"])
            portfolio = bleach.clean(request.form["previous"])

            image_path = None
            if 'image' in request.files and request.files['image'].filename != '':
                image = request.files['image']
                if image is not None:
                    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
                    if image.filename.split('.')[-1].lower() in ALLOWED_EXTENSIONS:
                        destination_folder = os.path.join('static', 'images')

                        image_path = os.path.join('static', 'images', secure_filename(image.filename))

                        image.save(image_path)

            user.fname = first_name
            user.lname = last_name
            user.email = email

            user.phone_number = phone_number
            user.twitter = twitter
            user.github = github
            user.country = country
            user.City = city
            user.age = usersage
            user.skills = skills
            user.status = status
            user.profile_photo = image_path
            user.about_me = about_me
            user.portfolio = portfolio

            db.session.commit()

            return redirect(url_for('myprofile'))

    else:

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
    user = User.query.filter_by(id=current_user.id).first()
    if request.method == "POST":

        user_id = current_user.id
        new_blog = Blog(
            title=request.form.get("title"),
            content=request.form.get("content"),
            subtitle=request.form.get("subtitle"),
            user_id=user_id,
        )
        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for('myblogs'))
    else:
        return render_template("newblog.html", user=user)

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
    user = User.query.filter_by(id=current_user.id).first()
    collab=Collabration.query.filter_by(id=id).first()
    return render_template("specficcollab.html", collab=collab, user=user)





@app.route("/addcollabration" ,methods=["GET", "POST"])
@login_required
def addcollab():
    user = User.query.filter_by(id=current_user.id).first()
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
        return render_template("addcollabration.html", user=user)




@app.route("/myproject", methods=["GET", "POST"])
@login_required
def myprojects():
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    user = User.query.filter_by(id=current_user.id).first()
    user_id = current_user.id

    projects = Collabration.query.filter_by(user_id=user_id).offset(offset).limit(per_page).all()
    total_records = Collabration.query.count()
    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)



    return render_template("myproject.html", user=user, page=page, total_pages=total_pages, projects=projects)











@app.route("/otherprojects/<int:id>", methods=["GET"])
@login_required
def otherprojects(id):
    user = User.query.filter_by(id=current_user.id).first()
    projects = Collabration.query.filter_by(user_id=id)
    return render_template("otherprojects.html", projects=projects, user=user)


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


@app.route("/searchproject/<namepattern>", methods=["GET", "POST"])
@login_required
def searchproject(namepattern):
    user = User.query.filter_by(id=current_user.id).first()
    results = Collabration.query.filter(Collabration.name.like(f'%{namepattern}%'), User.id != current_user.id).all()
    return render_template("searchprofile.html", results=results, pattern=namepattern, user=user)




@app.route("/searchprofile/<namepattern>", methods=["GET", "POST"])
@login_required
def searchprofile(namepattern):
    user = User.query.filter_by(id=current_user.id).first()
    results =result = User.query.filter(User.fname.like(f'%{namepattern}%'), User.id != current_user.id).all()
    return render_template("searchprofile.html", results=results, pattern=namepattern, user=user)


@app.route("/searchblog/<titleofblog>", methods=['GET', "POST"])
@login_required
def searchblog(titleofblog):
    user = User.query.filter_by(id=current_user.id).first()
    results = Blog.query.filter(Blog.title.like(f'%{titleofblog}%')).all()
    return render_template("searchblog.html", results=results, titleofblog=titleofblog, user=user)





@app.route("/otherusers")
@login_required
def otherusers():
    user = User.query.filter_by(id=current_user.id).first()
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    users = User.query.filter(User.id != current_user.id).offset(offset).limit(per_page).all()
    random.shuffle(users)

    total_records = User.query.count()

    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    return render_template("otherusers.html", users=users, page=page, total_pages=total_pages,user=user)





@app.route("/allfollowers/<int:id>", methods=["GET", "POST"])
@login_required
def allfollowers(id):
    user = User.query.filter_by(id=current_user.id).first()
    followers = Follower.query.filter_by(user_id=id).all()
    followers = followers.followers
    return render_template("allfollowers.html", followers=followers, user=user)




@app.route("/allfollwing", methods=["GET", "POST"])
@login_required
def allfollowing():
    user = User.query.filter_by(id=current_user.id).first()
    followers = Follower.query.filter_by(user_id=current_user.id)
    page = request.args.get("page", default=1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    follwoing = followers.query.offset(offset).limit(per_page).all()

    users = random.shuffle(followers)

    total_records = User.query.count()

    total_pages = (total_records // per_page) + (1 if total_records % per_page > 0 else 0)

    return render_template("otherusers.html", users=users, page=page, total_pages=total_pages,
                           user=user)



@app.route("/deleteaccount", methods=["GET", "POST"])
@login_required
def deleteaccount():
    user = User.query.filter_by(id=current_user.id).first()
    if request.method == "POST":
        user = User.query.filter_by(id=current_user.id).first()
        collabrations = Collabration.query.filter_by(user_id=current_user.id).all()
        current_dir = os.getcwd()


        if user.profile_photo is not None:
            full_path = os.path.join(current_dir, user.profile_photo)

            os.remove(full_path)
        logout_user()
        db.session.delete(user)
        db.session.commit()
        return redirect(url_for('home'))
    else:
        return render_template("deleteaccount.html", user=user)


@app.route("/unfollow/<int:follower_id>", methods=["POST"])
@login_required
def unfollow(follower_id):
    user_id = current_user.id

    following = Follower.query.filter_by(follower_id=user_id).first()

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

        return render_template("interestinmyproject.html", projects=projects, user=user)







@app.route("/explore", methods=["GET"])
def explore():
    is_logged_in = current_user.is_authenticated
    user = User.query.filter_by(id=current_user.id).first()
    return render_template("explore.html", user=user, is_logged_in=is_logged_in)



# @app.route("/registeredinterest", methods=["GET"])
# @login_required
# def registeredInterest():
#     user = User.query.filter_by(id=current_user.id).first()
#     interests = user.interests
#     all_interest = Interest.query.filter_by(user_id=current_user.id).all()
#
#     return render_template('Registeredinterest.html', interests=interests, all_interest=all_interest)


@app.route("/userblogs/<int:id>", methods=["GET", "POST"])
def userblogs(id):
    blogs = Blog.query.filter_by(users_id=id).all()
    user = User.query.filter_by(id=current_user.id).first()
    return render_template("userblog.html", blogs=blogs, user=user)


@app.route("/fetchusername/<username>", methods=["POST"])
def fetchusername(username):
    user = User.query.filter_by(username=username).first()
    if user is not None:
        response = {"message": "Username already taken"}
        return jsonify(response), 400
    else:
        response = {"message": "Username is available."}
        return jsonify(response), 200


@app.route("/deleteprofile", methods=["POST"])
def deleteprofile():
    user = User.query.filter_by(id=current_user.id).first()
    current_dir = os.getcwd()
    full_path = os.path.join(current_dir, user.profile_photo)

    os.remove(full_path)
    return redirect(url_for('editprofile'))

@app.route("/removelike/<int:id>", methods=["POST"])
def removelike(id):
    blog = Blog.query.filter_by(id=id).first()
    user = User.query.filter_by(id=current_user.id)
    user = user.liked_blogs
    if blog:
        if blog.user_id != current_user.id:

            if user in blog.liking_users:

                response = {"message": "can't be unliked since you haven't liked it"}
                return jsonify(response), 500


        else:
            response = {"message": "You can't like your own blog"}
            return jsonify(response), 404
    else:
        response = {"message": "Blog is not found"}
        return jsonify(response), 404


def checkdue_date(allcollaboration):
    for collabration in allcollaboration:
        due_date = datetime.strptime(collabration.due_date, "%B %d, %Y").date()
        if due_date > datetime.date.today():
            db.session.delete(collabration)
    db.session.commit()





if __name__ == '__main__':

    app.run(debug=True, port=5000)
