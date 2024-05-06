from flask import Flask, render_template, redirect, url_for,jsonify, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, PasswordField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
import datetime as dt


now = dt.datetime.now()
year = now.year
db = SQLAlchemy()

app = Flask(__name__)
Bootstrap(app)
app.config['SECRET_KEY'] = 'dfigsiougpsodufpsiufgodhobjvdnfoigue98r4t533453453'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///cafes.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()


class Cafes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    zipcode = db.Column(db.String(10), unique=False, nullable=False)
    city = db.Column(db.String(30), unique=False, nullable=False)
    has_sockets = db.Column(db.String(1))
    has_toilet = db.Column(db.String(1))
    has_wifi = db.Column(db.String(1))
    coffee_price = db.Column(db.String(250), unique=False, nullable=False)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


with app.app_context():
    db.create_all()


class SearchForm(FlaskForm):
    location = StringField("", validators=[DataRequired()], render_kw={"placeholder": "City or Zip:"})
    submit = SubmitField('Find Place')


class AddCafeForm(FlaskForm):
    name = StringField("Has Sockets?", validators=[DataRequired()], render_kw={"placeholder": "Cafe Name:"})
    map_url = StringField("", validators=[DataRequired()], render_kw={"placeholder": "Location:"})
    zipcode = StringField("", validators=[DataRequired()], render_kw={"placeholder": "Zip:"})
    city = StringField("", validators=[DataRequired()], render_kw={"placeholder": "City:"})
    has_sockets = SelectField('Sockets Available?', choices=[(True, "YES"), (False, "NO")], validators=[DataRequired()])
    has_toilet = SelectField('Bathroom Access?', choices=[(1, "YES"), (0, "NO")], validators=[DataRequired()])
    has_wifi = SelectField('Has WiFi?', choices=[(1, "YES"), (0, "NO")], validators=[DataRequired()])
    coffee_price = SelectField('Coffee Price Range', choices=["$1-$2", "$3-$4", "$5-$6", "$7-$8", "$9 and up"], validators=[DataRequired()], render_kw={"placeholder": "Coffee Price"})
    submit = SubmitField('Add Place')


class UpdateCafeForm(FlaskForm):
    has_sockets = SelectField('Has Sockets?', choices=[(1, "YES"), (0, "NO")], validators=[DataRequired()])
    has_toilet = SelectField('Has Bathroom?', choices=[(1, "YES"), (0, "NO")], validators=[DataRequired()])
    has_wifi = SelectField('Has WiFi?', choices=[(1, "YES"), (0, "NO")], validators=[DataRequired()])
    coffee_price = SelectField('Coffee Price', choices=["", "$1-$2", "$3-$4", "$5-$6", "$7-$8", "$9 and up"],
                               validators=[DataRequired()], render_kw={"placeholder": "Coffee Price"})
    submit = SubmitField('Submit Update')


class EnterPassword(FlaskForm):
    password = PasswordField("To Remove a Place: ", validators=[DataRequired()], render_kw={"placeholder": "Enter Password"})
    submit = SubmitField('Submit')


class AnotherCafe(FlaskForm):
    submit = SubmitField('Add another place')


@app.route("/", methods=["GET", "POST"])
def home():
    form = SearchForm()
    if form.validate_on_submit():
        location = form.location.data

        return redirect(url_for('search', location=location))
    return render_template("index.html", year=year, form=form)


@app.route("/add_place", methods=["GET", "POST"])
def add_place():
    form = AddCafeForm()
    if form.validate_on_submit():
        name = form.name.data
        map_url = form.map_url.data
        zipcode = form.zipcode.data
        city = form.city.data
        if form.has_sockets.data == "YES":
            has_sockets = True
        else:
            has_sockets = False

        if form.has_toilet.data == "YES":
            has_toilet = True
        else:
            has_toilet = False

        if form.has_wifi.data == "YES":
            has_wifi = True
        else:
            has_wifi = False
        coffee_price = form.coffee_price.data

        new_cafe = Cafes(name=name, map_url=map_url, zipcode=zipcode, city=city, has_sockets=has_sockets, has_toilet=has_toilet,
                         has_wifi=has_wifi, coffee_price=coffee_price)
        db.session.add(new_cafe)
        db.session.commit()
        message = 'New place added. Thank you!'
        return redirect(url_for('message', message=message))
    title = 'Add a cafe'
    subtitle = 'Submit a new cafe you recommend for remote work'

    return render_template("add_cafe.html", year=year, form=form, message=title, second_message=subtitle)


@app.route("/delete/<int:id>", methods=["GET", "POST", "DELETE"])
def delete(id):
    place_to_delete = Cafes.query.get(id)
    if place_to_delete:
        db.session.delete(place_to_delete)
        db.session.commit()
    return redirect(url_for('places'))


@app.route("/update/<int:id>", methods=["GET", "POST"])
def edit(id):
    place = Cafes.query.filter_by(id=id).first()
    form = UpdateCafeForm(obj=place)
    if place:
        msg = f'Update info for "{place.name}"'
    else:
        msg = "Sorry, the place wasn't found."
        form = False

    if form.validate_on_submit():
        form.populate_obj(place)
        db.session.add(place)
        db.session.commit()
        print("updated")
        return redirect(url_for('places'))
    return render_template("places.html", year=year, place=place, message=msg, form=form)


@app.route("/places", methods=["GET", "POST"])
def places():
    delete = False
    password_form = EnterPassword()
    results = db.session.query(Cafes).order_by(Cafes.name)
    all_places = [place.to_dict() for place in results]
    jsonify(all_places)
    if password_form.validate_on_submit():
        if password_form.password.data == "12345":
            delete = True
        else:
            password_form.password.errors = ("ERROR:",)
            password_form.password.render_kw = {"placeholder": "Enter Correct Password"}
            msg = 'Click "Delete" to remove a place'
            return render_template("places.html", year=year, cafes=all_places, table=True, message=msg,
                                   delete=delete)
    return render_template("places.html",year=year, cafes=all_places, table=True, password_form=password_form,
                           delete=delete)


@app.route("/<message>", methods=["GET", "POST"])
def message(message):
    form = AnotherCafe()
    if form.validate_on_submit():
        return redirect(url_for('add_cafe'))
    return render_template("add_cafe.html", form=form, message=message, second_message="")


@app.route("/places/<location>")
def search(location):
    in_city = Cafes.query.filter(Cafes.city.like(location)).order_by(Cafes.name)
    in_zip = Cafes.query.filter(Cafes.zipcode.like(location)).order_by(Cafes.name)

    if in_city or in_zip:
        cafes = [cafe.to_dict() for cafe in in_city] + [cafe.to_dict() for cafe in in_zip]
        jsonify(cafes)

        if not cafes:
            error = f"Sorry, nothing found near {location}"
            return render_template("places.html", year=year, cafes=cafes, message=error,), 404
        else:
            title = f"Cafes near {location}"
        return render_template("places.html", year=year, cafes=cafes, message=title, table=True, search=True ), 200




if __name__ == '__main__':
    app.run(debug=True, port=9000)
