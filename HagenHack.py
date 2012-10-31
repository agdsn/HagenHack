from flask import Flask, render_template, redirect, url_for, request, flash
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext import wtf
from flask.ext.login import LoginManager, login_required, UserMixin, login_user, logout_user
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['PASSWD'] = 'test'
app.config["USER"] = "admin"

app.secret_key = r'Ma5Jeiquaix6EGhuo7chei1aeNaiLuor6ahfug3iehoh1aes'


db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = "login"
login_manager.login_message = u"Sie m&uuml;ssen eingeloggt sein um die Fragen einzusehen."


class User(UserMixin):
    id = 0
    pw = app.config["PASSWD"]
    name = app.config["USER"]

    @staticmethod
    def verify_and_get(username, passwd):
        user = User()
        if username == user.name and passwd == user.pw:
            return user
        return None


@login_manager.user_loader
def load_user(userid):
    return User()


class LoginForm(wtf.Form):
    username = wtf.TextField(label="Benutzename")
    password = wtf.PasswordField(label="Passwort")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(csrf_enabled=False)
    if form.validate_on_submit():
        user = User.verify_and_get(form.username.data,
                                   form.password.data)

        if user is not None:
            login_user(user)
            flash(u"Erfolgreich eingeloggt.")
            return redirect(request.args.get("next") or url_for("answers"))
        else:
            print "WURST"
            flash(u"Falscher Benutzername und/oder Passwort")
            return redirect(url_for("login"))
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("question"))


class Referent(db.Model):
    __tablename__ = "referent"
    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return self.name

class Comment(db.Model):
    __tablename__ = "comment"
    id = Column(Integer, primary_key=True)
    to_id = Column(Integer, ForeignKey("referent.id"), nullable=True)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    date = Column(DateTime, default=datetime.now)

    to = db.relationship(Referent, backref=db.backref("comments", order_by=lambda:Comment.date))

    def formatted_date(self):
        return self.date.strftime("%d.%m %H:%M")


def get_referents():
    return db.session.query(Referent).all()


class CommentForm(wtf.Form):
    subject = wtf.TextField(label="Thema")
    referent = wtf.QuerySelectField(query_factory=get_referents, label="Referent")
    body = wtf.TextAreaField(label="Frage")


@app.route('/', methods=["GET", "POST"])
def question():
    form = CommentForm(csrf_enabled=False)
    if form.validate_on_submit():
        new_question = Comment(to=form.referent.data,
                               subject=form.subject.data,
                               body=form.body.data)
        db.session.add(new_question)
        db.session.commit()
        return redirect(url_for("thanks"))
    return render_template("form.html", form=form)


@app.route("/thanks")
def thanks():
    return render_template("thanks.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/answers", defaults={"referent_id": None})
@app.route("/answers/<int:referent_id>")
@login_required
def answers(referent_id):
    answers_qry = db.session.query(Referent)
    if referent_id is not None:
        answers_qry = answers_qry.filter_by(id=referent_id)
        answers_refernts = answers_qry.all()
    else:
        answers_refernts = []
        for answer in answers_qry:
            if len(answer.comments):
                answers_refernts.append(answer)

    if request.is_xhr:
        return render_template("answer_list.html", answers=answers_refernts)

    return render_template("answers.html", referents=get_referents(), answers=answers_refernts)


@app.route("/referents")
@login_required
def referents():
    all_referents = db.session.query(Referent).all()
    return render_template("referents.html", referents=all_referents)


class ReferentForm(wtf.Form):
    name = wtf.TextField(label="Name")


@app.route("/referents/add", methods=["GET", "POST"])
@login_required
def referent_add():
    form = ReferentForm(csrf_enabled=False)

    if form.validate_on_submit():
        new_referent = Referent(name=form.name.data)
        db.session.add(new_referent)
        db.session.commit()
        return redirect(url_for("referents"))

    return render_template("referent_add.html", form=form)


if __name__ == '__main__':
    app.debug=True
    app.run(host="0.0.0.0")
