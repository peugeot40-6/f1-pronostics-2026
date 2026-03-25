gps =[
    "Australie", "Chine", "Japon",
    "Miami", "Canada", "Monaco",
    "Barcelone", "Autriche", "Royaume-Uni",
    "Belgique", "Hongrie", "Pays-Bas", "Italie", "Espagne",
    "Azerbaïdjan", "Singapour", "États-Unis", "Mexique",
    "Brésil", "Las Vegas", "Qatar", "Abu Dhabi"
]
pilotes = [
    "Verstappen", "Hadjar", "Leclerc", "Hamilton", "Russell",
    "Antonelli", "Alonso", "Stroll", "Norris", "Piastri",
    "Gasly", "Colapinto", "Bearman", "Ocon", "Lawson", "Lindblad",
    "Albon", "Sainz", "Bottas", "Perez",
    "Hulkenberg", "Bortoleto"
]

from flask import Flask, render_template, request, redirect, session
from functools import wraps
import gspread
import os
import json
from google.oauth2.service_account import Credentials

def connecter_feuilles():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")

    if not creds_json:
        print("❌ Pas de credentials Google")
        return None, None

    creds_dict = json.loads(creds_json)

    scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)

    sheet = client.open("pronostic F1")

    feuille_pronos = sheet.worksheet("pronostic")
    feuille_resultats = sheet.worksheet("resultats")

    return feuille_pronos, feuille_resultats
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
app.secret_key = "cle-ultra-securisee-123"

# USERS
users = {
    "Padre": "padre123",
    "Amandine": "amandine123",
    "Sacha": "sacha123"
}

# GOOGLE SHEETS CONNECTION
def connect_sheets():
    try:
        creds_json = os.getenv("GOOGLE_CREDENTIALS")

        if not creds_json:
            print("❌ GOOGLE_CREDENTIALS manquant")
            return None, None

        creds_dict = json.loads(creds_json)

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        sheet = client.open("pronostic F1")

        feuille_pronos = sheet.worksheet("pronostic")
        feuille_resultats = sheet.worksheet("resultats")

        return feuille_pronos, feuille_resultats

    except Exception as e:
        print("❌ ERREUR GOOGLE SHEETS :", e)
        return None, None

# LOGIN REQUIRED
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect("/")
        return f(*args, **kwargs)
    return wrapper


# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    erreur = None

    if request.method == "POST":
        nom = request.form.get("nom", "").title()
        mdp = request.form.get("mdp", "")

        if nom in users and users[nom] == mdp:
            session["user"] = nom
            return redirect("/accueil")
        else:
            erreur = "Identifiants incorrects"

    return render_template("index.html", erreur=erreur)


# ACCUEIL
@app.route("/accueil")
@login_required
def accueil():
    return render_template("accueil.html", user=session["user"])


# PRONOSTIC
@app.route("/pronostic", methods=["GET", "POST"])
@login_required
def pronostic():

    if request.method == "POST":
        gp = request.form.get("gp")
        p1 = request.form.get("p1")
        p2 = request.form.get("p2")
        p3 = request.form.get("p3")

        sheet_pronos, _ = connect_sheets()
        data = sheet_pronos.get_all_records()
        
       
        #  Vérifier doublon
        for row in data:
            if row["Joueur"] == session["user"] and row["GP"] == gp:
                return "❌ Tu as déjà fait un pronostic pour ce GP"

        # ✔ Ajouter si OK
        sheet_pronos.append_row([
            session["user"], gp, p1, p2, p3
        ])

        return redirect("/accueil")

    return render_template("pronostic.html", gps=gps, pilotes=pilotes)
    
# ENCODER LES RÉSULTATS GP

@app.route("/resultats", methods=["GET", "POST"])
@login_required
def resultats():
    if session["user"] != "Padre":
        return "Accès refusé"

    feuille_pronos, feuille_resultats = connecter_feuilles()

    if request.method == "POST":
        gp = request.form.get("gp")
        p1 = request.form.get("p1")
        p2 = request.form.get("p2")
        p3 = request.form.get("p3")
        p4 = request.form.get("p4")
        p5 = request.form.get("p5")
        p6 = request.form.get("p6")
        p7 = request.form.get("p7")
        p8 = request.form.get("p8")
        p9 = request.form.get("p9")
        p10 = request.form.get("p10")
        
        # Enregistrer les résultats
        feuille_resultats.append_row([gp, p1, p2, p3, p4, p5, p6, p7, p8, p9, p10 ])

    return render_template("resultats.html", gps=gps, pilotes=pilotes)

# HISTORIQUE

@app.route("/historique")
def historique():
    feuille_pronos, feuille_resultats = connecter_feuilles()

    pronos = feuille_pronos.get_all_records()
    resultats = feuille_resultats.get_all_records()

    historique = {}

    for res in resultats:
        gp = res["GP"]
        classement_reel = [res["P1"], res["P2"], res["P3"]]

        historique[gp] = []

        for prono in pronos:
            if prono["GP"] != gp:
                continue

            joueur = prono["Joueur"]
            prediction = [prono["P1"], prono["P2"], prono["P3"]]

            score = calcul_points(prediction, classement_reel)

            historique[gp].append({
                "joueur": joueur,
                "score": score
            })

        # tri du meilleur au pire
        historique[gp].sort(key=lambda x: x["score"], reverse=True)

    return render_template("historique.html", historique=historique)
    

# CLASSEMENT AUTOMATIQUE
def calcul_points_f1(pronos, resultats):
    points_f1 = {
        1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
        6: 8, 7: 6, 8: 4, 9: 2, 10: 1
    }

    points = 0

    for pilote in pronos:
        if pilote in resultats:
            position = resultats.index(pilote) + 1
            points += points_f1.get(position, 0)

    podium = resultats[:3]

    if pronos == podium:
        bonus = 10
    elif set(pronos) == set(podium):
        bonus = 3
    else:
        bonus = 0

    return points + bonus

# CLASSEMENT

@app.route("/classement")
@login_required
def classement():

    sheet_pronos, sheet_resultats = connect_sheets()

    pronos = sheet_pronos.get_all_records()
    resultats = sheet_resultats.get_all_records()

    scores = {}

    for prono in pronos:
        joueur = prono["Joueur"]
        gp = prono["GP"]

        pr = [prono["1er"], prono["2e"], prono["3e"]]

        res_gp = next((r for r in resultats if r["GP"] == gp), None)

        if not res_gp:
            continue

        res = [res_gp[f"P{i}"] for i in range(1, 11) if res_gp.get(f"P{i}")]

        points = calcul_points_f1(pr, res)

        if joueur not in scores:
            scores[joueur] = 0

        scores[joueur] += points

    classement = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    return render_template("classement_general.html", classement=classement)
    
# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
