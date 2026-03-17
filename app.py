import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, render_template, request, redirect, session, url_for
from functools import wraps

app = Flask(__name__)
app.secret_key = "supersecretkey"

# UTILISATEURS
users = {
    "Padre": "padre123",
    "Amandine": "amandine123",
    "Sacha": "sacha123"
}
# GOOGLE SHEET
def connect_sheet():
return None
    
# DECORATEUR LOGIN
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect("/")
        return f(*args, **kwargs)
    return wrapper


# PAGE LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    erreur = None

    if request.method == "POST":
        nom = request.form.get("nom")
        mdp = request.form.get("mdp")

        if nom:
            nom = nom.title()

        if nom in users and users[nom] == mdp:
            session["user"] = nom
            return redirect("/accueil")
        else:
            erreur = "Identifiants incorrects"

    return render_template("index.html", erreur=erreur)

# PAGE ACCUEIL
@app.route("/accueil")
@login_required
def accueil():
    return render_template("accueil.html", user=session["user"])

# PAGE PRONOSTICS
@app.route("/pronostic", methods=["GET", "POST"])
@login_required
def pronostic():

    if request.method == "POST":
        gp = request.form.get("gp")
        p1 = request.form.get("p1")
        p2 = request.form.get("p2")
        p3 = request.form.get("p3")

        sheet = connect_sheet()

        sheet.append_row([
            gp,
            session["user"],
            p1,
            p2,
            p3
        ])

        return "Pronostic enregistré ✅"

    return render_template("pronostic.html")
# PAGE CLASSEMENT
@app.route("/classement")
@login_required
def classement():
    return render_template("classement_general.html")


# PAGE HISTORIQUE
@app.route("/historique")
@login_required
def historique():
    return render_template("historique.html")


# ADMIN
@app.route("/admin")
@login_required
def admin():
    if session["user"] != "Padre":
        return "Accès refusé"
    return "Page admin"


# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
