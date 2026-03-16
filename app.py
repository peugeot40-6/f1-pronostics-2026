from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

# PAGE ACCUEIL
@app.route("/")
def index():
    return render_template("index.html")


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
