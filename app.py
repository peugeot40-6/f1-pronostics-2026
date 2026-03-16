
from flask import Flask, render_template, request, redirect, session, url_for
import pandas as pd
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ======================
# UTILISATEURS
# ======================

users = {
    "Padre": "padre123",
    "Amandine": "amandine123",
    "Sacha": "sacha123"
}

points_f1 = {1:25,2:18,3:15,4:12,5:10,6:8,7:6,8:4,9:2,10:1}

grands_prix = [
"Australie","Japon","Chine","Miami","Monaco",
"Canada","Belgique","Italie","Las Vegas","Abu Dhabi"
]

pilotes = [
"Verstappen","Hamilton","Leclerc","Russell","Norris",
"Piastri","Alonso","Gasly","Ocon","Perez","Stroll","Albon"
]

# ======================
# OUTILS
# ======================

def read_csv(name):
    if os.path.exists(name):
        return pd.read_csv(name)
    return pd.DataFrame()

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect("/")
        return f(*args, **kwargs)
    return wrapper

# ======================
# LOGIN
# ======================

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        nom = request.form["nom"].title()
        mdp = request.form["mdp"]
        if nom in users and users[nom] == mdp:
            session["user"] = nom
            return redirect("/accueil")
        return render_template("login.html", erreur="Login incorrect")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ======================
# ACCUEIL
# ======================

@app.route("/accueil")
@login_required
def accueil():
    return render_template("index.html", user=session["user"])

# ======================
# AJOUT PRONOSTIC
# ======================

@app.route("/ajouter_pronostic", methods=["GET","POST"])
@login_required
def ajouter_pronostic():

    df = read_csv("pronostics.csv")

    if request.method == "POST":

        gp = request.form["gp"]
        p1 = request.form["p1"]
        p2 = request.form["p2"]
        p3 = request.form["p3"]
        joueur = session["user"]

        if len({p1,p2,p3}) < 3:
            return render_template("ajouter_pronostic.html",
                gps=grands_prix,pilotes=pilotes,
                erreur="Choisir 3 pilotes différents")

        deja = df[(df["Grand Prix"]==gp) & (df["Participant"]==joueur)]
        if not deja.empty:
            return render_template("ajouter_pronostic.html",
                gps=grands_prix,pilotes=pilotes,
                erreur="Pronostic déjà enregistré")

        new = {"Grand Prix":gp,"Participant":joueur,"1er":p1,"2e":p2,"3e":p3}

        df = pd.concat([df,pd.DataFrame([new])])
        df.to_csv("pronostics.csv",index=False)

        return redirect("/voir_pronostics")

    return render_template("ajouter_pronostic.html", gps=grands_prix, pilotes=pilotes)

# ======================
# VOIR PRONOSTICS
# ======================

@app.route("/voir_pronostics")
@login_required
def voir_pronostics():

    df = read_csv("pronostics.csv")
    joueur = session["user"]

    if joueur != "Padre":
        df = df[df["Participant"]==joueur]

    pronos = df.to_dict("records")

    return render_template("voir_pronostics.html", pronos=pronos)

# ======================
# RESULTATS
# ======================

@app.route("/ajouter_resultat", methods=["GET","POST"])
@login_required
def ajouter_resultat():

    if session["user"] != "Padre":
        return redirect("/accueil")

    df = read_csv("resultats.csv")

    if request.method == "POST":

        gp = request.form["gp"]
        positions = [request.form[f"pos{i}"] for i in range(1,11)]

        new = {"Grand Prix":gp}
        for i,p in enumerate(positions):
            new[f"pos{i+1}"] = p

        df = pd.concat([df,pd.DataFrame([new])])
        df.to_csv("resultats.csv",index=False)

        calculer_points()

        return redirect("/classement")

    return render_template("ajouter_resultat.html", gps=grands_prix, pilotes=pilotes)

# ======================
# CALCUL CLASSEMENT
# ======================

def calculer_points():

    pronos = read_csv("pronostics.csv")
    res = read_csv("resultats.csv")

    lignes = []

    for _,row in pronos.iterrows():

        gp = row["Grand Prix"]
        joueur = row["Participant"]
        picks = [row["1er"],row["2e"],row["3e"]]

        r = res[res["Grand Prix"]==gp]

        if r.empty:
            continue

        r = r.iloc[0]
        classement = [r[f"pos{i}"] for i in range(1,11)]

        pts = 0

        for p in picks:
            if p in classement:
                pos = classement.index(p)+1
                pts += points_f1.get(pos,0)

        podium = classement[:3]

        bonus = 10 if picks==podium else (3 if set(picks)==set(podium) else 0)

        lignes.append({
            "Grand Prix":gp,
            "Participant":joueur,
            "Total":pts+bonus
        })

    df = pd.DataFrame(lignes)
    df.to_csv("classement.csv",index=False)

    if not df.empty:
        gen = df.groupby("Participant")["Total"].sum().reset_index().sort_values(by="Total",ascending=False)
        gen.to_csv("classement_general.csv",index=False)

# ======================
# CLASSEMENT
# ======================

@app.route("/classement")
@login_required
def classement():

    df = read_csv("classement_general.csv")
    data = df.to_dict("records")

    return render_template("classement_general.html", classement=data)

# ======================
# INITIALISATION
# ======================

def init_files():

    if not os.path.exists("pronostics.csv"):
        pd.DataFrame(columns=["Grand Prix","Participant","1er","2e","3e"]).to_csv("pronostics.csv",index=False)

    if not os.path.exists("resultats.csv"):
        pd.DataFrame(columns=["Grand Prix"]+[f"pos{i}" for i in range(1,11)]).to_csv("resultats.csv",index=False)

    if not os.path.exists("classement_general.csv"):
        pd.DataFrame(columns=["Participant","Total"]).to_csv("classement_general.csv",index=False)

if __name__ == "__main__":
    init_files()
    app.run(debug=True)
