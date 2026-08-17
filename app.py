import os
import re
import requests
import base64
from flask import Flask, Response, request, redirect, jsonify

app = Flask(__name__)

# Configurações do Único Canal: Globo News
GLOBO_NEWS_URL = "http://177.52.24.163/GLOBO-NEWS-HD/index.m3u8"

def clean_url(url):
    """ Remove vírgulas, espaços e caracteres invisíveis da URL """
    if not url:
        return url
    return url.replace(',', '').replace(' ', '').replace('\n', '').replace('\r', '').strip()

@app.route('/')
def home():
    return "Servidor IPTV Proxy - Globo News Online. Playlist em /playlist.m3u"

@app.route('/playlist.m3u')
def playlist():
    host = request.host
    scheme = request.scheme

    # Apenas Globo News na playlist
    ch = {"id": "globonews", "name": "Globo News (HD Direto)", "logo": "https://logodownload.org/wp-content/uploads/2020/03/globo-news-logo.png"}

    m3u = "#EXTM3U\n"
    m3u += f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-logo="{ch["logo"]}" group-title="Canais",{ch["name"]}\n'
    m3u += f'{scheme}://{host}/stream/{ch["id"]}\n'

    return Response(m3u, mimetype='application/x-mpegurl')

@app.route('/stream/globonews')
@app.route('/stream/<channel_id>')
def stream(channel_id=None):
    # Redireciona diretamente para o link estável da Globo News
    return redirect(clean_url(GLOBO_NEWS_URL))

@app.route('/debug')
def debug():
    return jsonify({"channel": "globonews", "url": clean_url(GLOBO_NEWS_URL)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
