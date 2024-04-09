from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient

app = Flask(__name__,template_folder='templates')

# Configuration de MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['Routes']
collection = db['routes']


@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/recherche-de-pays')
def researchCountries():
    return render_template('researchHighway/researchHighway.html')

@app.route('/graphique')
def graphicsCountries():
    return render_template('graphics/graphics.html')

@app.route('/highway')
def highwayConcessionaire():
    return render_template('highway/highway.html')

@app.route('/api/highway/<type>/<year>')
def longueur_route(type, year):
    strYear = str(year)
    if type == 'nationale':

        match_filter = {
            "dateReferentiel": {'$regex': strYear},
            "$or": [
                {"route": {"$regex": "^N"}},
                {"route": {"$regex": "^\d{3}N"}}
            ],
            "cote": {"$ne": "G"}
        }

        pipeline = [
            {"$match": match_filter},
            {"$group": {
                "_id": {
                    "route": "$route"
                },
                "metres": {"$sum": "$longueur"}
            }}
        ]

    else:
        match_filter = {
            "dateReferentiel": {'$regex': strYear},
            "$or": [
                {"route": {"$regex": "^A"}}
            ],
            "cote": {"$ne": "G"}
        }

        pipeline = [
            {"$match": match_filter},
            {"$group": {
                "_id": {
                    "route": "$route"
                },
                "metres": {"$sum": "$longueur"}
            }}
        ]

    result = list(collection.aggregate(pipeline))

    return jsonify(result)

@app.route('/api/concessionaire/<year>/<route>')
def concessionaire(year, route):
    strYear = str(year)

    match_filter = {
        "dateReferentiel": {'$regex': strYear},
        "route": route,
        "cote": {"$ne": "G"}
    }

    pipeline = [
        {"$match": match_filter},
        {"$group": {
            "_id": {
                "concessionaire": "$Gestionnaire"
            },
            "metres": {"$sum": "$longueur"}
        }}
    ]

    result = list(collection.aggregate(pipeline))

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
