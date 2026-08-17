from flask import Flask, render_template, redirect, send_from_directory
import os

app = Flask(__name__)

# Rota principal: Abre o seu player (index.html que está na pasta templates)
@app.route('/')
def index():
    return render_template('index.html')

# Rota direta para o canal (se quiser usar apenas este link no navegador)
@app.route('/globonews')
def globonews():
    # Redireciona para o sinal estável da Globo News
    return redirect("https://sinaldvd.github.io/tv/player.html?id=globonews")

# Rota para o App de IPTV: entrega o arquivo M3U
@app.route('/playlist.m3u')
def playlist():
    # Busca o arquivo playlist.m3u que está dentro da pasta static
    return send_from_directory('static', 'playlist.m3u')

# Configuração para o Railway rodar o app na porta correta
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
