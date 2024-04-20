from flask import Flask,Blueprints, render_template

main = Blueprints("main",__name__)
def create_app():
    app = Flask(__name__)
    app.config["DEBUG"] = True
    app.config["SECRET_KEY"] = "secret"

    app.register_blueprint(main)
    return app
@main.route("/")
def page():
    return render_template("chat.html")