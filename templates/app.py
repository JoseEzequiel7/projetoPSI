from flask import Flask, render_template, request, redirect, make_response
import json
from datetime import datetime, timedelta

app = Flask(__name__)

FILMES = {
    'acao': ['Mad Max: Estrada da Fúria', 'John Wick', 'Velozes e Furiosos'],
    'comedia': ['Superbad', 'Se Beber, Não Case', 'O Máskara'],
    'drama': ['Forrest Gump', 'À Espera de um Milagre', 'O Poderoso Chefão'],
    'ficcao': ['Interestelar', 'Matrix', 'Blade Runner'],
    'terror': ['Invocação do Mal', 'O Iluminado', 'Hereditário']
}

@app.route('/' , methods=['GET' , 'POST'])
def index():
    if request.method == 'POST':
        nome = request.form['nome']
        return f"voce digitou: {nome}"
    else:
        return render_template('index.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome')
        genero = request.form.get('genero')
        notificacoes = 'notificacoes' in request.form

        prefs = {'nome': nome, 'genero': genero, 'notificacoes': notificacoes}
        resp = make_response(redirect('/preferencias'))
        expira = datetime.now() + timedelta(days=7)
        resp.set_cookie('preferencias', json.dumps(prefs), expires=expira)

        return resp
    return render_template('cadastro.html')

@app.route('/preferencias')
def preferencias():
    prefs = request.cookies.get('preferencias')
    if prefs:
        prefs = json.loads(prefs)
        return render_template('preferencias.html', prefs=prefs)
    return render_template('preferencias.html', prefs=None)

@app.route('/recomendar')
def recomendar():
    genero = request.args.get('genero', '')
    filmes = FILMES.get(genero.lower())
    prefs = request.cookies.get('preferencias')
    nome = None
    if prefs:
        prefs = json.loads(prefs)
        nome = prefs.get('nome')
    return render_template('recomendar.html', genero=genero, filmes=filmes, nome=nome)


if __name__ == '__main__':
    app.run(debug=True)

