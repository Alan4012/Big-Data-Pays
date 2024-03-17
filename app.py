from flask import Flask, render_template

app = Flask(__name__,template_folder='templates')


@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/recherche-de-pays')
def researchCountries():
    return render_template('researchCountries/researchCountries.html')

@app.route('/graphique')
def graphicsCountries():
    return render_template('graphics/graphics.html')

if __name__ == '__main__':
    app.run(debug=True)
