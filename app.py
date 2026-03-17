from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

# PAGE ACCUEIL
@app.route("/", methods=["GET", "POST"])
def login():
    erreur = None

    if request.method == "POST":
        nom = request.form["nom"]
        mdp = request.form["mdp"]

        if nom != "Padre" or mdp != "padre123":
            erreur = "Identifiants incorrects"
        else:
            return "Connexion réussie 🎉"

    return render_template("index.html", erreur=erreur)


# PAGE HISTORIQUE
@app.route("/historique")
def historique():
    df = pd.read_csv("classement_general.csv")
    records = df.to_dict("records")
    return render_template("historique.html", records=records)


# PAGE CLASSEMENT
@app.route("/classement")
def classement():
    df = pd.read_csv("classement_general.csv")
    classement = df.to_dict("records")
    return render_template("classement_general.html", classement=classement)


if __name__ == "__main__":
    app.run(debug=True)
