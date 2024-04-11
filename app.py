from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from pyproj import Transformer
import re

app = Flask(__name__, template_folder='templates')

# Configuration de MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['Routes']
collection = db['routes']


@app.route('/')
def dashboard():
    return render_template('index.html')


# Fonction pour convertir les coordonnées Lambert93 en latitude et longitude
def lambert93_to_latlng(x, y):
    transformer = Transformer.from_crs("EPSG:2154", "EPSG:4326")
    lat, lon = transformer.transform(x, y)
    return lat, lon


@app.route('/RA')
def indexHighway():
    data_dates = collection.distinct("dateReferentiel")
    gestionnaires = collection.distinct("Gestionnaire")

    seen_years = set()
    years = []

    for entry in data_dates:
        # Utiliser une expression régulière pour extraire l'année de manière flexible
        match = re.search(r'\b(\d{4})\b', entry)
        if match:
            year = match.group(1)

            # Vérifier si l'année a déjà été vue
            if year not in seen_years:
                # Ajouter l'année à la liste et à l'ensemble des années déjà vues
                years.append(year)
                seen_years.add(year)

    return render_template('researchHighway/researchHighway.html', annees=years, gestionnaires=gestionnaires)


@app.route('/api/dataRA', methods=['GET'])
def researchHighway():
    selected_date = request.args.get('year', type=str)
    selected_gestionnaire = request.args.get('gestionnaire', type=str)

    # verifie si la data selection existe
    if selected_date is None or selected_gestionnaire is None:
        return jsonify({'error': 'year/gestionnaire pas inclut dans /dataRA'}), 400

    # print(selected_date, selected_gestionnaire) -> sert pour la verification

    # permet de comparer des chaines de caractère ici : l'année avec une date (str) complète
    regex_date = re.compile(r"\b" + re.escape(selected_date) + r"\b")
    regex_gestionnaire = re.compile(r"\b" + re.escape(selected_gestionnaire) + r"\b")

    pipeline = [
        {
            '$match': {
                'dateReferentiel': {'$regex': regex_date},
                'Gestionnaire': {'$regex': regex_gestionnaire}
            }
        },
        {'$project': {
            "_id": 0,
            "dateReferentiel": 1,
            "Gestionnaire": 1,
            "xD": 1,
            "xF": 1,
            "yD": 1,
            "yF": 1
        }

        }
    ]

    with collection.aggregate(pipeline) as cursor:
        data = list(cursor)

    # Convertir les coordonnées Lambert93 en latitude et longitude
    for entry in data:
        if 'xD' in entry and 'yD' in entry and 'xF' in entry and 'yF' in entry:
            xD = entry.get('xD')
            yD = entry.get('yD')
            xF = entry.get('xF')
            yF = entry.get('yF')

            xD = xD.replace(',', '.')
            yD = yD.replace(',', '.')
            xF = xF.replace(',', '.')
            yF = yF.replace(',', '.')

            entry['latD'], entry['lonD'] = lambert93_to_latlng(float(xD), float(yD))
            entry['latF'], entry['lonF'] = lambert93_to_latlng(float(xF), float(yF))
        else:
            # Si l'une des coordonnées est manquante, ignorer cette entrée
            print("Coordonnées manquantes pour une entrée")

    return jsonify(data), 200


@app.route('/graphique-bar-par-gestionnaire')
def graphicsConcession():
    data_dates = collection.distinct("dateReferentiel")
    concession = collection.distinct("concessionPrD")

    seen_years = set()
    years = []

    for entry in data_dates:
        # Utiliser une expression régulière pour extraire l'année de manière flexible
        match = re.search(r'\b(\d{4})\b', entry)
        if match:
            year = match.group(1)

            # Vérifier si l'année a déjà été vue
            if year not in seen_years:
                # Ajouter l'année à la liste et à l'ensemble des années déjà vues
                years.append(year)
                seen_years.add(year)

    return render_template('graphics/barGraph.html', annees=years, concessions=concession)

@app.route('/graphique-camenbert-par-gestionnaire')
def graphicsCamenbert():
    data_dates = collection.distinct("dateReferentiel")
    concession = collection.distinct("concessionPrD")

    seen_years = set()
    years = []

    for entry in data_dates:
        # Utiliser une expression régulière pour extraire l'année de manière flexible
        match = re.search(r'\b(\d{4})\b', entry)
        if match:
            year = match.group(1)

            # Vérifier si l'année a déjà été vue
            if year not in seen_years:
                # Ajouter l'année à la liste et à l'ensemble des années déjà vues
                years.append(year)
                seen_years.add(year)

    return render_template('graphics/doughnut.html', annees=years, concessions=concession)

@app.route('/api/routeGestionnaire', methods=['GET'])
def researchRoutesConcess():
    selected_year = request.args.get('years', type=str)
    selected_concession = request.args.get('concessionPrD', type=str)

    if selected_year is None or selected_concession is None:
        return jsonify({'error': 'year/concessionPrD pas inclut dans /api/routeGestionnaire'}), 400

    regex_year = re.compile(r"\b" + re.escape(selected_year) + r"\b")
    regex_concession = re.compile(r"\b" + re.escape(selected_concession) + r"\b")

    pipeline = [
        {
            '$match': {
                'dateReferentiel': {'$regex': regex_year},
                'concessionPrD': {'$regex': regex_concession}
            }
        },
        {
            '$group': {
                '_id': "$Gestionnaire",
                'count': {'$sum': {'$cond': [["$route", 'null'], 1, 0]}},
            }
        },
        {
            '$match': {
                'count': {'$gte': 5}
            }
        }
    ]

    with collection.aggregate(pipeline) as cursor:
        data = list(cursor)

    return jsonify(data), 200

@app.route('/api/longueurGestionnaire', methods=['GET'])
def get_longueurGestionnaire():
    selected_year = request.args.get('years', type=str)
    selected_concession = request.args.get('concessionPrD', type=str)

    if selected_year is None or selected_concession is None:
        return jsonify({'error': 'year/concessionPrD pas inclut dans /api/routeGestionnaire'}), 400

    regex_year = re.compile(r"\b" + re.escape(selected_year) + r"\b")
    regex_concession = re.compile(r"\b" + re.escape(selected_concession) + r"\b")

    pipeline = [
        {
            '$match': {
                'dateReferentiel': {'$regex': regex_year},
                'concessionPrD': {'$regex': regex_concession}
            }
        },
        {
            '$group': {
                '_id': "$Gestionnaire",
                'longueur': {'$sum': '$longueur'},
            }
        },
        {
            '$match': {
                'longueur': {'$gte': 70000}  # Filtrer les routes de plus de 70 km (70,000 mètres)
            }
        },
        {
            '$addFields': {
                'longueur_formate': {
                    '$concat': [
                        {
                            '$cond': [
                                {'$gte': ['$longueur', 1000]},
                                {'$substr': [{'$toString': {'$divide': ['$longueur', 1000]}}, 0, -1]},
                                {'$concat': ['0.', {'$substr': [{'$toString': '$longueur'}, 0, -3]}]}
                            ]
                        },
                    ]
                }
            }
        },
        {
            '$addFields': {
                'longueur_formate': {
                    '$concat': [
                        {'$substr': ['$longueur_formate', 0, {'$indexOfBytes': ['$longueur_formate', '.']}]}
                    ]
                }
            }
        }
    ]

    with collection.aggregate(pipeline) as cursor:
        data = list(cursor)

    return jsonify(data), 200

@app.route('/highway')
def highwayConcessionaire():
    data_dates = collection.distinct("dateReferentiel")

    seen_years = set()
    years = []

    for entry in data_dates:
        # Utiliser une expression régulière pour extraire l'année de manière flexible
        match = re.search(r'\b(\d{4})\b', entry)
        if match:
            year = match.group(1)

            # Vérifier si l'année a déjà été vue
            if year not in seen_years:
                # Ajouter l'année à la liste et à l'ensemble des années déjà vues
                years.append(year)
                seen_years.add(year)

    return render_template('highway/highway.html', annees=years)

# Définition d'une route pour récupérer les longueurs des autoroutes en fonction du type et de l'année
@app.route('/api/highway/<type>/<year>')
def longueur_route(type, year):
    strYear = str(year)  # Convertit l'année en chaîne de caractères

    # Vérifie le type d'autoroute (nationale ou autre)
    if type == 'nationale':
        # Filtre pour les autoroutes nationales
        match_filter = {
            "dateReferentiel": {'$regex': strYear},  # Filtre par année
            "route": {"$regex": "^N"},  # Filtre pour les routes commençant par N
            "cote": {"$ne": "G"}  # Exclut les valeurs avec "cote" égal à G
        }
    else:
        # Filtre pour les autres types d'autoroutes (non-nationales)
        match_filter = {
            "dateReferentiel": {'$regex': strYear},  # Filtre par année
            "route": {"$regex": "^A"},  # Filtre pour les routes commençant par A
            "cote": {"$ne": "G"}  # Exclut les valeurs avec "cote" égal à G
        }

    # Pipeline d'agrégation MongoDB pour calculer les longueurs des autoroutes
    pipeline = [
        {"$match": match_filter},  # Filtrage des données
        {"$group": {
            "_id": {
                "route": "$route"  # Groupe par route
            },
            "metres": {"$sum": "$longueur"}  # Calcule la somme des longueurs
        }}
    ]

    # Exécute la requête avec le pipeline défini
    result = list(collection.aggregate(pipeline))

    # Renvoie les résultats au format JSON
    return jsonify(result)

# Définition d'une route pour récupérer les concessionnaires d'une autoroute pour une année donnée
@app.route('/api/concessionaire/<year>/<route>')
def concessionaire(year, route):
    strYear = str(year)  # Convertit l'année en chaîne de caractères

    # Filtre pour récupérer les données des concessionnaires d'une route pour une année spécifique
    match_filter = {
        "dateReferentiel": {'$regex': strYear},  # Filtre par année
        "route": route,  # Filtre par route spécifique
        "cote": {"$ne": "G"}  # Exclut les valeurs avec "cote" égal à G
    }

    # Pipeline d'agrégation MongoDB pour calculer les longueurs des autoroutes
    pipeline = [
        {"$match": match_filter},  # Filtrage des données
        {"$group": {
            "_id": {
                "concessionaire": "$Gestionnaire"  # Groupe par concessionnaire
            },
            "metres": {"$sum": "$longueur"}  # Calcule la somme des longueurs
        }}
    ]

    # Exécute la requête avec le pipeline défini
    result = list(collection.aggregate(pipeline))

    # Renvoie les résultats au format JSON
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
