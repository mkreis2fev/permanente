import os
import requests
from flask import Flask, Response

app = Flask(__name__)

# URL Direta
VELO_LINK = "http://fastcdn.bond:8080/get.php?username=vWRJvKkPDX&password=vWRJvKkPDX&type=m3u_plus&output=ts"

@app.route('/')
def health_check():
    return "<h1>Servidor VeloPlay Online!</h1><p>Acesse <a href='/playlist.m3u'>/playlist.m3u</a> para ver os canais.</p>"

@app.route('/playlist.m3u')
def playlist():
    try:
        # Tenta pegar a lista real
        headers = {'User-Agent': 'IPTVSmartersPlayer'}
        r = requests.get(VELO_LINK, headers=headers, timeout=10)
        return Response(r.text, mimetype='text/plain')
    except:
        # Se o servidor original falhar, retorna um erro amigável em texto
        return "#EXTM3U\n#ERRO: O servidor original nao respondeu."

@app.route('/epg.xml')
def epg():
    r = requests.get("https://iptv-org.github.io/epg/guides/br/mi.tv.epg.xml", timeout=10)
    return Response(r.text, mimetype='application/xml')

if __name__ == '__main__':
    # Isso so roda localmente. No Railway, o Gunicorn assume.
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
