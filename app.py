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
def connect_sheet():
    try:
        creds_json = os.getenv("GOOGLE_CREDENTIALS")

        if not creds_json:
            print("❌ GOOGLE_CREDENTIALS manquant")
            return None

        creds_dict = json.loads(creds_json)

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        sheet = client.open("pronostic F1").sheet1
        return sheet

    except Exception as e:
        print("❌ ERREUR GOOGLE SHEETS :", e)
        return None
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

    gps = [...]  # ta liste actuelle
    pilotes = [...]  # ta liste actuelle

    if request.method == "POST":
        gp = request.form.get("gp")
        p1 = request.form.get("p1")
        p2 = request.form.get("p2")
        p3 = request.form.get("p3")

        sheet_pronos, _ = connect_sheets()
        data = sheet_pronos.get_all_records()

        # 🔒 Vérifier doublon
        for row in data:
            if row["Joueur"] == session["user"] and row["GP"] == gp:
                return "❌ Tu as déjà fait un pronostic pour ce GP"

        # ✔ Ajouter si OK
        sheet_pronos.append_row([
            session["user"], gp, p1, p2, p3
        ])

        return redirect("/accueil")

    return render_template("pronostic.html", gps=gps, pilotes=pilotes)
    
🏁️⃣  ENCODER LES RÉSULTATS GP
🎯 Objectif

👉 Encoder les résultats du top 10

✅ Nouvelle route /ajouter_resultat
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

        # 🔄 supprimer ancien GP si existe
        data = sheet_resultats.get_all_records()
        for i, row in enumerate(data, start=2):
            if row["GP"] == gp:
                sheet_resultats.delete_rows(i)
                break

        sheet_resultats.append_row([gp] + resultats)

        return redirect("/classement")

    return render_template("ajouter_resultat.html")
    
🧩 HTML ajouter_resultat.html
<h1>Encoder résultats GP</h1>

<form method="post">
    GP: <input name="gp"><br><br>

    {% for i in range(1,11) %}
        Position {{ i }} :
        <input name="pos{{i}}"><br>
    {% endfor %}

    <button type="submit">Valider</button>
</form>

🏆️⃣ CLA SSEMENT AUTOMATIQUE

👉 on reprend TON système exact (F1 + bonus)

✅ Fonction calcul (inchangée)
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

        # 🔄 supprimer ancien GP si existe
        data = sheet_resultats.get_all_records()
        for i, row in enumerate(data, start=2):
            if row["GP"] == gp:
                sheet_resultats.delete_rows(i)
                break

        sheet_resultats.append_row([gp] + resultats)

        return redirect("/classement")

    return render_template("ajouter_resultat.html")
    
✅ Route classement
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
    
🎯 RÉSULTAT FINAL

👉 Ton app fait maintenant :

✔ 1 seul pronostic par joueur / GP 🔒
✔ encodage résultats admin 🏁
✔ calcul automatique 🧠
✔ classement dynamique 🏆

🔥 PROCHAIN NIVEAU (je te conseille)

👉 très utile :

afficher classement du dernier GP

afficher détail des points

empêcher modification après deadline

👉 Dis-moi :

👉 “on ajoute le détail des points”
ou
👉 “on bloque après deadline” 🚦
# CALCUL DES POINTS
def calcul_points_f1(pronos, resultats):
    points_f1 = {
        1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
        6: 8, 7: 6, 8: 4, 9: 2, 10: 1
    }

    points = 0

    # Points position
    for pilote in pronos:
        if pilote in resultats:
            position = resultats.index(pilote) + 1
            points += points_f1.get(position, 0)

    # Bonus podium
    podium_reel = resultats[:3]

    if pronos == podium_reel:
        bonus = 10
    elif set(pronos) == set(podium_reel):
        bonus = 3
    else:
        bonus = 0

    return points, bonus, points + bonus

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
