import os
import requests
import json
import logging
from flask import Flask, Response, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def decode_url(url, cr):
    if not url or not url.startswith("@y@") or not cr:
        return url
    mapping_orig = " !#$%&()+,-./023456789:;<=>?ABCDEFGHIJKLMNOPQRSTUVWXYZ[^_abcdefghijklmnopqrstuvwxz{}~"
    try:
        # Decodificação por mapa de substituição (Lógica Smali)
        decoded = "".join([mapping_orig[cr.find(c)] if c in cr else c for c in url[3:]])
        return decoded.replace("@yy1111@", "https://").replace("@yy111@", "https://www.").replace("@yy11@", "http://").replace("@yy11@", "http://").replace("@yy1@", "http://www.")
    except:
        return url

def fetch_channels():
    app_id = "3713506"
    cod_app = "fojywv" # Valor encontrado no smali (COD_APP)
    
    # URL com todos os parâmetros que o app envia
    config_url = f"https://config.e-droid.net/srv/config.php?v=260&idapp={app_id}&cod={cod_app}&ia=1"
    
    headers = {
        'User-Agent': 'Android Vinebre Software',
        'X-Requested-With': 'go.geh',
        'Accept-Language': 'pt-BR,pt;q=0.8',
        'Connection': 'Keep-Alive',
        'Host': 'config.e-droid.net'
    }
    
    try:
        # Desativar verify=False pode ajudar se houver erro de SSL no Railway
        response = requests.get(config_url, headers=headers, timeout=15)
        
        if "[APLICNODISP]" in response.text:
            logger.error("Acesso Negado: O servidor retornou APLICNODISP")
            return []

        data = response.json()
        cr = data.get("cr", "")
        secciones = data.get("secciones", [])
        
        if isinstance(secciones, dict):
            secciones = list(secciones.values())

        channels = []

        # Scan profundo em todas as categorias
        def find_recursively(items):
            for item in items:
                if not isinstance(item, dict): continue
                
                # Se for vídeo (tipo 6) ou tiver URL ofuscada
                u = item.get("url", "")
                if (str(item.get("tipo")) == "6" or u.startswith("@y@")) and u:
                    channels.append({
                        "name": item.get("tit", "Canal"),
                        "url": decode_url(u, cr)
                    })
                
                # Explora submenus e atributos
                for k in ["atribs", "submenu_items", "items"]:
                    if k in item and item[k]:
                        sub = item[k]
                        if isinstance(sub, dict): sub = list(sub.values())
                        find_recursively(sub)

        find_recursively(secciones)
        return channels
    except Exception as e:
        logger.error(f"Falha na captura: {e}")
        return []

@app.route('/')
def home():
    return "<h1>Servidor GehTV M3U</h1><p><a href='/lista.m3u'>Acessar Lista</a></p>"

@app.route('/lista.m3u')
def generate_m3u():
    channels = fetch_channels()
    if not channels:
        return "Erro: O servidor bloqueou o Railway (APLICNODISP). Verifique o /debug.", 503
    
    m3u = "#EXTM3U\n"
    for c in channels:
        m3u += f'#EXTINF:-1 tvg-name="{c["name"]}",{c["name"]}\n{c["url"]}\n'
    return Response(m3u, mimetype='application/x-mpegURL')

@app.route('/debug')
def debug():
    app_id = "3713506"
    cod_app = "fojywv"
    # Testamos a resposta bruta aqui
    url = f"https://config.e-droid.net/srv/config.php?v=260&idapp={app_id}&cod={cod_app}"
    r = requests.get(url, headers={'User-Agent': 'Android Vinebre Software', 'X-Requested-With': 'go.geh'})
    return jsonify({
        "status_code": r.status_code,
        "raw_text": r.text[:500],
        "is_blocked": "[APLICNODISP]" in r.text
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
