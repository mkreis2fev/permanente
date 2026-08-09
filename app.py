import os
import requests
import logging
from flask import Flask, Response, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def decode_url(url, cr):
    if not url or not url.startswith("@y@") or not cr: return url
    orig = " !#$%&()+,-./023456789:;<=>?ABCDEFGHIJKLMNOPQRSTUVWXYZ[^_abcdefghijklmnopqrstuvwxz{}~"
    try:
        d = "".join([orig[cr.find(c)] if c in cr else c for c in url[3:]])
        return d.replace("@yy1111@", "https://").replace("@yy111@", "https://www.").replace("@yy11@", "http://").replace("@yy1@", "http://www.")
    except: return url

def fetch_channels():
    # Parâmetros exatos extraídos da engenharia reversa
    app_id = "3713506"
    cod_app = "fojywv"
    v_smali = "228" # Versão original VSOURCE no smali
    
    # Tentamos o servidor srv15 que é o mais comum para o GehTV
    url = f"https://srv15.e-droid.net/srv/config.php?v={v_smali}&idapp={app_id}&cod={cod_app}&p=1"
    
    headers = {
        'User-Agent': 'Android Vinebre Software',
        'X-Requested-With': 'go.geh',
        'Accept-Language': 'pt-BR',
        'Connection': 'Keep-Alive'
    }
    
    try:
        # verify=False para evitar problemas de SSL no Railway
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        
        if "[APLICNODISP]" in response.text:
            return []

        data = response.json()
        cr = data.get("cr", "")
        secciones = data.get("secciones", [])
        if isinstance(secciones, dict): secciones = list(secciones.values())

        channels = []
        def scan(items):
            for i in items:
                if not isinstance(i, dict): continue
                u = i.get("url", "")
                if (str(i.get("tipo")) == "6" or u.startswith("@y@")) and u:
                    channels.append({"name": i.get("tit", "Canal"), "url": decode_url(u, cr)})
                for k in ["atribs", "submenu_items", "items"]:
                    if k in i and i[k]: scan(i[k])
        
        scan(secciones)
        return channels
    except: return []

@app.route('/')
def home(): return "<h1>Servidor GehTV M3U</h1><p><a href='/lista.m3u'>Lista M3U</a></p>"

@app.route('/lista.m3u')
def generate_m3u():
    ch = fetch_channels()
    if not ch: return "O servidor bloqueou o IP do Railway. Use o Render.com", 503
    m3u = "#EXTM3U\n"
    for c in ch: m3u += f'#EXTINF:-1 tvg-name="{c["name"]}",{c["name"]}\n{c["url"]}\n'
    return Response(m3u, mimetype='application/x-mpegURL')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
