from datetime import datetime, timezone

CALENDRIER_2026 = {
    "Australie":   datetime(2026, 3, 15, 6, 0, tzinfo=timezone.utc),
    "Chine":       datetime(2026, 3, 22, 7, 0, tzinfo=timezone.utc),
    "Japon":       datetime(2026, 4, 5, 5, 0, tzinfo=timezone.utc),
    "Miami":       datetime(2026, 5, 10, 19, 0, tzinfo=timezone.utc),
    "Monaco":      datetime(2026, 5, 24, 13, 0, tzinfo=timezone.utc),
    "Canada":      datetime(2026, 6, 14, 18, 0, tzinfo=timezone.utc),
    "Barcelone":   datetime(2026, 6, 1, 13, 0, tzinfo=timezone.utc),
    "Autriche":    datetime(2026, 6, 28, 13, 0, tzinfo=timezone.utc),
    "Royaume-Uni": datetime(2026, 7, 5, 14, 0, tzinfo=timezone.utc),
    "Belgique":    datetime(2026, 7, 26, 13, 0, tzinfo=timezone.utc),
    "Hongrie":     datetime(2026, 8, 2, 13, 0, tzinfo=timezone.utc),
    "Pays-Bas":    datetime(2026, 8, 30, 13, 0, tzinfo=timezone.utc),
    "Italie":      datetime(2026, 9, 6, 13, 0, tzinfo=timezone.utc),
    "Espagne":     datetime(2026, 9, 20, 13, 0, tzinfo=timezone.utc),
    "Azerbaïdjan": datetime(2026, 9, 27, 11, 0, tzinfo=timezone.utc),
    "Singapour":   datetime(2026, 10, 4, 8, 0, tzinfo=timezone.utc),
    "États-Unis":  datetime(2026, 10, 18, 19, 0, tzinfo=timezone.utc),
    "Mexique":     datetime(2026, 10, 25, 20, 0, tzinfo=timezone.utc),
    "Brésil":      datetime(2026, 11, 15, 17, 0, tzinfo=timezone.utc),
    "Las Vegas":   datetime(2026, 11, 21, 6, 0, tzinfo=timezone.utc),
    "Qatar":       datetime(2026, 11, 29, 14, 0, tzinfo=timezone.utc),
    "Abu Dhabi":   datetime(2026, 12, 6, 13, 0, tzinfo=timezone.utc),
}

def get_prochain_gp():
    """Retourne le prochain GP pas encore couru."""
    now = datetime.now(timezone.utc)
    for gp in gps:
        date = CALENDRIER_2026.get(gp)
        if date and date > now:
            return {
                "nom": gp,
                "date": date,
                "verrouille": gp in COURSES_VERROUILLEES
            }
    # Si tous les GP sont passés, retourner le dernier
    return {"nom": gps[-1], "date": None, "verrouille": True}

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
    prochain_gp = get_prochain_gp()
    return render_template("accueil.html", user=session["user"], prochain_gp=prochain_gp)

@app.route("/mes_pronostics")
@login_required
def mes_pronostics():
    feuille_pronos, feuille_resultats = connecter_feuilles()

    joueur = session["user"]
    tous_pronos = feuille_pronos.get_all_records()
    tous_resultats = feuille_resultats.get_all_records()

    # GP avec résultats connus
    gps_avec_resultats = {r["GP"]: r for r in tous_resultats}

    # Pronostics du joueur
    mes_pronos = {p["GP"]: p for p in tous_pronos if p["Joueur"] == joueur}

    gps_termines   = []
    gps_en_attente = []
    gps_a_faire    = []

    total_points  = 0
    meilleur      = 0
    nb_pronos     = 0
    compteur_pilotes = {}

    for gp in gps:
        if gp in gps_avec_resultats:
            # GP terminé (résultat encodé)
            res = gps_avec_resultats[gp]
            classement_reel = [res[f"P{i}"] for i in range(1, 11)]

            if gp in mes_pronos:
                p = mes_pronos[gp]
                prediction = [p["p1"], p["p2"], p["p3"]]
                score = calcul_points(prediction, classement_reel)
                total_points += score
                nb_pronos += 1
                if score > meilleur:
                    meilleur = score
                for pilote in prediction:
                    compteur_pilotes[pilote] = compteur_pilotes.get(pilote, 0) + 1
                gps_termines.append({
                    "gp": gp, "p1": p["p1"], "p2": p["p2"], "p3": p["p3"],
                    "points": score
                })
            else:
                gps_termines.append({
                    "gp": gp, "p1": None, "p2": None, "p3": None, "points": None
                })

        elif gp in mes_pronos:
            # GP pas encore couru, mais pronostic fait
            p = mes_pronos[gp]
            gps_en_attente.append({
                "gp": gp, "p1": p["p1"], "p2": p["p2"], "p3": p["p3"]
            })

        elif gp not in COURSES_VERROUILLEES:
            # GP futur, pas encore pronostiqué
            gps_a_faire.append(gp)

    # Pilote fétiche
    pilote_favori = max(compteur_pilotes, key=compteur_pilotes.get) if compteur_pilotes else None
    moyenne = round(total_points / nb_pronos, 1) if nb_pronos > 0 else 0

    stats = {
        "total_points":  total_points,
        "nb_pronos":     nb_pronos,
        "meilleur_score": meilleur,
        "moyenne":       moyenne,
        "pilote_favori": pilote_favori,
    }

    return render_template(
        "mes_pronostics.html",
        stats=stats,
        gps_termines=gps_termines,
        gps_en_attente=gps_en_attente,
        gps_a_faire=gps_a_faire
    )


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
