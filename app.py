from flask import Flask, render_template, redirect, request
import requests
import re

app = Flask(__name__)

# Rota para a página inicial (seu player)
@app.route('/')
def index():
    return render_template('index.html')

# Rota que "captura" ou redireciona para o sinal da Globo News
@app.route('/globonews')
def get_globo_news():
    # Aqui você pode adicionar lógica de scraping para pegar o link .m3u8 real
    # Por agora, redirecionamos para o player estável que você já usa
    sinal_url = "https://sinaldvd.github.io/tv/player.html?id=globonews"
    return redirect(sinal_url)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
