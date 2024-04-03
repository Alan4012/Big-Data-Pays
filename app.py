import re

from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient

app = Flask(__name__,template_folder='templates')

client = MongoClient("mongodb://localhost:27017/")
db = client["Routes"]
collection = db["routes"]

@app.route('/')
def dashboard():
    return render_template('index.html')

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
                'count': { '$sum': { '$cond': [["$route", 'null'] , 1, 0] }},
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
                'count': { '$sum': { '$cond': [["$route", 'null'] , 1, 0] }},
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

@app.route('/researchHighway')
def researchCountries():
    return render_template('researchHighway/researchHighway.html')

if __name__ == '__main__':
    app.run(debug=True)
