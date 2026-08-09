import os
import logging
import requests
from flask import Flask, Response, jsonify
from bot import get_channels

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def index():
    return "Servidor GehTV Online. Vá para /lista.m3u"

@app.route('/debug')
def debug():
    """Rota para ver o que o servidor do GehTV está mandando para o Railway"""
    app_id = "3713506"
    url = f"https://config.e-droid.net/srv/config.php?v=260&idapp={app_id}"
    headers = {'User-Agent': 'Android Vinebre Software'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        return jsonify({
            "status_code": r.status_code,
            "headers": dict(r.headers),
            "content_preview": r.text[:1000] # Mostra o começo da resposta
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/lista.m3u')
def generate_m3u():
    try:
        channels = get_channels()
        if not channels:
            return "Erro: O bot nao encontrou canais. Acesse /debug para diagnostico.", 503
        
        m3u = "#EXTM3U\n"
        for c in channels:
            m3u += f'#EXTINF:-1 tvg-name="{c["name"]}",{c["name"]}\n{c["url"]}\n'
        return Response(m3u, mimetype='application/x-mpegURL')
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
