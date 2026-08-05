import os
import requests
from flask import Flask, Response, render_template_string

app = Flask(__name__)

# SERVIDORES OFICIAIS (Principal e Backup)
SERVERS = ["http://fastcdn.bond:8080", "http://vodcast.sbs:8080"]
CREDENTIAL = "vWRJvKkPDX"

def get_list():
    headers = {'User-Agent': 'IPTVSmartersPlayer'}
    
    # Tenta o servidor principal e depois o de backup
    for base_url in SERVERS:
        url = f"{base_url}/get.php?username={CREDENTIAL}&password={CREDENTIAL}&type=m3u_plus&output=ts"
        try:
            # Timeout curtíssimo (3 segundos) para o Railway não travar
            response = requests.get(url, headers=headers, timeout=3)
            if response.status_code == 200 and "#EXTM3U" in response.text:
                return response.text
        except:
            continue
            
    return "#EXTM3U\n#ERRO: O servidor original nao respondeu. Tente novamente no player."

@app.route('/')
def index():
    return render_template_string("""
        <body style="background:#000;color:#fff;text-align:center;padding:50px;font-family:sans-serif">
            <h1 style="color:#ffaa00">VeloPlay Cloud</h1>
            <p>Status: Online</p>
            <div style="margin-top:30px">
                <a href="/playlist.m3u" style="background:#ffaa00;color:#000;padding:15px 30px;text-decoration:none;font-weight:bold;border-radius:5px">ABRIR LISTA M3U</a>
            </div>
        </body>
    """)

@app.route('/playlist.m3u')
def playlist():
    # Retorna a lista ou o erro rapidamente
    return Response(get_list(), mimetype='text/plain')

@app.route('/epg.xml')
def epg():
    url = f"{SERVERS[0]}/xmltv.php?username={CREDENTIAL}&password={CREDENTIAL}"
    try:
        r = requests.get(url, timeout=5)
        return Response(r.text, mimetype='application/xml')
    except:
        return '<?xml version="1.0" encoding="UTF-8"?><tv></tv>'

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
