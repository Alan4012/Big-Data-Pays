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


@app.route('/dataRA', methods=['GET'])
def researchHighway():
    selected_date = request.args.get('year', type=str)
    selected_gestionnaire = request.args.get('gestionnaire', type=str)

    if selected_date is None or selected_gestionnaire is None:
        return jsonify({'error': 'year/gestionnaire pas inclut dans /dataRA'}), 400

    print(selected_date, selected_gestionnaire)

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
            # Si l'une des coordonnées est manquante, ignorer cette entrée ou gérer l'erreur selon vos besoins
            print("Coordonnées manquantes pour une entrée")

    return jsonify(data), 200


@app.route('/nombre-routes-par-gestionnaire')
def graphicsConcession():
    data_dates = collection.distinct("dateReferentiel")
    seen_year = set()
    years = []

    for entry in data_dates:
        match = re.search(r'\b(\d{4})\b', entry)
        if match :
            year = match.group(1)

            if year not in seen_year:
                years.append(year)
                seen_year.add(year)

    return render_template('graphics/graphics.html', annees=years)

@app.route('/api/routeGestionnaireConcedee', methods=['GET'])
def autorouteGestionnaireConcedee():
    selected_year = request.args.get('years', type=str)

    if selected_year is None:
        return jsonify({'error': 'year pas inclut dans /api/routeGestionnaireConcedee'}), 400

    print(selected_year)

    regex_date = re.compile(r"\b" + re.escape(selected_year) + r"\b")

    pipeline = [
        {
            '$match': {
                'dateReferentiel': {'$regex': regex_date},
                'concessionPrD': {'$regex': '^C'}
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

@app.route('/api/routeGestionnaireNonConcedee', methods=['GET'])
def autorouteGestionnaireNonConcedee():
    selected_year = request.args.get('years', type=str)

    if selected_year is None:
        return jsonify({'error': 'year pas inclut dans /api/routeGestionnaireNonConcedee'}), 400

    print(selected_year)

    regex_date = re.compile(r"\b" + re.escape(selected_year) + r"\b")

    pipeline = [
        {
            '$match': {
                'dateReferentiel': {'$regex': regex_date},
                'concessionPrD': {'$regex': '^N'}
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

@app.route('/api/LongueurRouteGestionnaireConcedee', methods=['GET'])
def autorouteLongueurGestionnaireConcedee():
    selected_year = request.args.get('years', type=str)

    if selected_year is None:
        return jsonify({'error': 'year pas inclut dans /api/LongueurRouteGestionnaireConcedee'}), 400

    print(selected_year)

    regex_date = re.compile(r"\b" + re.escape(selected_year) + r"\b")

    pipeline = [
        {
            '$match': {
                'dateReferentiel': {'$regex': regex_date},
                'concessionPrD': {'$regex': '^C'}
            }
        },
        {
            '$group': {
              '_id': "$Gestionnaire",
                'longueur': {'$sum': '$longueur'},
            }
        },
        {
            '$addFields': {
                'longueur_formate': {
                    '$concat': [
                        {
                            '$cond': [
                                {'$gte': ['$longueur', 1000]},
                                {'$substr': [{'$toString': {'$divide': ['$longueur', 1000]}}, 0, -1]},  # Ajout de la virgule
                                {'$concat': ['0.', {'$substr': [{'$toString': '$longueur'}, 0, -3]}]}  # Ajout du "0" avant la virgule si nécessaire
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

@app.route('/api/LongueurRouteGestionnaireNonConcedee', methods=['GET'])
def autorouteLongueurGestionnaireNonConcedee():
    selected_year = request.args.get('years', type=str)

    if selected_year is None:
        return jsonify({'error': 'year pas inclut dans /api/LongueurRouteGestionnaireNonConcedee'}), 400

    print(selected_year)

    regex_date = re.compile(r"\b" + re.escape(selected_year) + r"\b")

    pipeline = [
        {
            '$match': {
                'dateReferentiel': {'$regex': regex_date},
                'concessionPrD': {'$regex': '^N'}
            }
        },
        {
            '$group': {
              '_id': "$Gestionnaire",
                'longueur': {'$sum': '$longueur'},
            }
        },
        {
            '$addFields': {
                'longueur_formate': {
                    '$concat': [
                        {
                            '$cond': [
                                {'$gte': ['$longueur', 1000]},
                                {'$substr': [{'$toString': {'$divide': ['$longueur', 1000]}}, 0, -1]},  # Ajout de la virgule
                                {'$concat': ['0.', {'$substr': [{'$toString': '$longueur'}, 0, -3]}]}  # Ajout du "0" avant la virgule si nécessaire
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


if __name__ == '__main__':
    app.run(debug=True)
