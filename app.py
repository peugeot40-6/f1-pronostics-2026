gps = [
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
from oauth2client.service_account import ServiceAccountCredentials

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

app = Flask(__name__)
app.secret_key = "cle-ultra-securisee-123"

# USERS
users = {
    "Padre": "padre2608",
    "Amandine": "amandine2401",
    "Sacha": "sacha0612"
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
COURSES_VERROUILLEES = ["Australie", "Chine"]

@app.route("/pronostic", methods=["GET", "POST"])
@login_required
def pronostic():
    if request.method == "POST":
        gp = request.form.get("gp")

        if gp in COURSES_VERROUILLEES:
            return "❌ Les pronostics sont fermés pour ce Grand Prix."

        p1 = request.form.get("p1")
        p2 = request.form.get("p2")
        p3 = request.form.get("p3")

        if len({p1, p2, p3}) < 3:
            return "❌ Tu ne peux pas choisir le même pilote plusieurs fois !"

        sheet_pronos, _ = connect_sheets()
        data = sheet_pronos.get_all_records()

        for row in data:
            if row["Joueur"] == session["user"] and row["GP"] == gp:
                return "❌ Tu as déjà fait un pronostic pour ce GP"

        sheet_pronos.append_row([session["user"], gp, p1, p2, p3])
        return redirect("/accueil")

    # GET : masquer les GP verrouillés
    gps_disponibles = [gp for gp in gps if gp not in COURSES_VERROUILLEES]
    return render_template("pronostic.html", gps=gps_disponibles, pilotes=pilotes)


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
        # ✅ Vérifier les doublons parmi le top 10
        top10 = [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10]
        if len(set(top10)) < 10:
            return "❌ Tu ne peux pas mettre le même pilote deux fois dans le top 10 !"

        feuille_resultats.append_row([gp, p1, p2, p3, p4, p5, p6, p7, p8, p9, p10])

    # ✅ Récupérer les GP déjà encodés et les masquer
    resultats_existants = feuille_resultats.get_all_records()
    gps_termines = {r["GP"] for r in resultats_existants}
    gps_disponibles = [gp for gp in gps if gp not in gps_termines]

    return render_template("resultats.html", gps=gps_disponibles, pilotes=pilotes)


# HISTORIQUE
@app.route("/historique")
@login_required
def historique():
    feuille_pronos, feuille_resultats = connecter_feuilles()

    pronos = feuille_pronos.get_all_records()
    resultats = feuille_resultats.get_all_records()

    historique = {}

    for res in resultats:
        gp = res["GP"]
        classement_reel = [
            res["P1"], res["P2"], res["P3"], res["P4"], res["P5"],
            res["P6"], res["P7"], res["P8"], res["P9"], res["P10"]
        ]
        historique[gp] = []

        for prono in pronos:
            if prono["GP"] != gp:
                continue
            joueur = prono["Joueur"]
            prediction = [prono["p1"], prono["p2"], prono["p3"]]
            score = calcul_points(prediction, classement_reel)
            historique[gp].append({
                "joueur": joueur,
                "points": score
            })

        historique[gp].sort(key=lambda x: x["points"], reverse=True)

    return render_template("historique.html", historique=historique)


# CLASSEMENT AUTOMATIQUE
def normaliser(nom):
    return nom.lower().strip().split()[-1]


def calcul_points(prediction, reel):
    points_f1 = {
        1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
        6: 8, 7: 6, 8: 4, 9: 2, 10: 1
    }
    score = 0
    prediction = [normaliser(p) for p in prediction]
    reel = [normaliser(r) for r in reel]

    for pilote in prediction:
        if pilote in reel:
            position = reel.index(pilote) + 1
            score += points_f1.get(position, 0)

    podium_reel = reel[:3]
    if prediction == podium_reel:
        score += 10
    elif set(prediction) == set(podium_reel):
        score += 3

    return score


# CLASSEMENT
@app.route("/classement")
@login_required
def classement():
    feuille_pronos, feuille_resultats = connecter_feuilles()

    pronos = feuille_pronos.get_all_records()
    resultats = feuille_resultats.get_all_records()

    scores = {}

    for prono in pronos:
        joueur = prono["Joueur"]
        gp = prono["GP"]
        prediction = [
            prono.get("p1"),
            prono.get("p2"),
            prono.get("p3")
        ]
        res_gp = next((r for r in resultats if r["GP"] == gp), None)
        if not res_gp:
            continue
        classement_reel = [res_gp[f"P{i}"] for i in range(1, 11)]
        points = calcul_points(prediction, classement_reel)
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
