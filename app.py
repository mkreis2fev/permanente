from flask import Flask, render_template, redirect, send_from_directory, Response
import requests
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# Rota que tenta capturar o fluxo de vídeo e repassar para o app de IPTV
@app.route('/live/globonews.m3u8')
def live_globonews():
    # Link de uma fonte que costuma ser estável para IPTV
    url = "https://sinalpublico.com/player3/globonews.php"
    # Nota: Capturar sinal puro de PHP/HTML exige scraping avançado.
    # Por enquanto, vamos redirecionar para o stream direto se disponível.
    stream_url = "https://tv.sinalpublico.com/globonews/index.m3u8"
    return redirect(stream_url)

@app.route('/playlist.m3u')
def playlist():
    return send_from_directory('static', 'playlist.m3u')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
