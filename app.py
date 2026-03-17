from flask import Flask, render_template, request, redirect, session, url_for

app = Flask(__name__)
app.secret_key = "supersecretkey"

# UTILISATEURS
users = {
    "Padre": "padre123",
    "Amandine": "amandine123",
    "Sacha": "sacha123"
}

# PAGE LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    erreur = None

    if request.method == "POST":
        nom = request.form["nom"].title()
        mdp = request.form["mdp"]

        if nom in users and users[nom] == mdp:
            session["user"] = nom
            return redirect("/accueil")
        else:
            erreur = "Identifiants incorrects"

    return render_template("index.html", erreur=erreur)


# PAGE ACCUEIL
@app.route("/accueil")
def accueil():
    from functools import wraps

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect("/")
        return f(*args, **kwargs)
    return wrapper
    return render_template("accueil.html", user=session["user"])


# PAGE CLASSEMENT
@app.route("/classement")
@login_required
def classement():
    if "user" not in session:
        return redirect("/")
    return render_template("classement_general.html")


# PAGE HISTORIQUE
@app.route("/historique")
def historique():
    if "user" not in session:
        return redirect("/")
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
    app.run(debug=True)_ == "__main__":
    app.run(debug=True)
