from flask import Flask, render_template, request, redirect, session
from functools import wraps
import os
import json
import gspread
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

        feuille_pronos = sheet.worksheet("pronostic F1")
        feuille_resultats = sheet.worksheet("résultats")

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

@app.route("/ajouter_resultat", methods=["GET", "POST"])
@login_required
def ajouter_resultat():

    if session["user"] != "Padre":
        return "Accès refusé"

    _, sheet_resultats = connect_sheets()

    if request.method == "POST":
        gp = request.form.get("gp")

        resultats = [
            request.form.get(f"pos{i}")
            for i in range(1, 11)
        ]

        # supprimer ancien GP si existe
        data = sheet_resultats.get_all_records()
        for i, row in enumerate(data, start=2):
            if row["GP"] == gp:
                sheet_resultats.delete_rows(i)
                break

        sheet_resultats.append_row([gp] + resultats)

        return redirect("/classement")

    return render_template("ajouter_resultat.html")
    
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

        pr = [prono["P1"], prono["P2"], prono["P3"]]

        res_gp = next((r for r in resultats if r["GP"] == gp), None)

        if not res_gp:
            continue

        res = [res_gp[f"pos{i}"] for i in range(1, 11) if res_gp.get(f"pos{i}")]

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
