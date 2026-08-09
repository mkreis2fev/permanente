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
        # Lógica exata do Smali: substituição de caracteres baseada no mapa 'cr'
        decoded = "".join([mapping_orig[cr.find(c)] if c in cr else c for c in url[3:]])
        return decoded.replace("@yy1111@", "https://").replace("@yy111@", "https://www.").replace("@yy11@", "http://").replace("@yy1@", "http://www.")
    except:
        return url

def fetch_channels():
    app_id = "3713506"
    # Adicionando parâmetros extras que o AppCreator24 exige para validar o acesso
    # v=228 (versão do motor no smali), f=1 (apenas ativos)
    config_url = f"https://config.e-droid.net/srv/config.php?v=228&idapp={app_id}&f=1"
    
    headers = {
        'User-Agent': 'Android Vinebre Software',
        'X-Requested-With': 'go.geh', # Nome do pacote encontrado no AndroidManifest
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'Connection': 'Keep-Alive',
        'Host': 'config.e-droid.net'
    }
    
    try:
        # Usamos uma sessão para manter cookies se necessário
        session = requests.Session()
        response = session.get(config_url, headers=headers, timeout=15)
        
        if "[APLICNODISP]" in response.text:
            logger.error("Servidor detectou BOT e bloqueou o acesso.")
            return []

        data = response.json()
        cr = data.get("cr", "")
        secciones = data.get("secciones", [])
        
        if isinstance(secciones, dict):
            secciones = list(secciones.values())

        channels = []

        def deep_scan(items):
            for item in items:
                if not isinstance(item, dict): continue
                url_raw = item.get("url", "")
                tipo = str(item.get("tipo", ""))
                
                # Captura canais tipo 6 (Vídeo)
                if (tipo == "6" or ".m3u8" in url_raw or url_raw.startswith("@y@")) and url_raw:
                    channels.append({
                        "name": item.get("tit", "Canal"),
                        "url": decode_url(url_raw, cr)
                    })
                
                # Entra em submenus (TV > CATEGORIAS)
                for key in ["atribs", "submenu_items", "items"]:
                    if key in item and item[key]:
                        sub = item[key]
                        if isinstance(sub, dict): sub = list(sub.values())
                        deep_scan(sub)

        deep_scan(secciones)
        return channels
    except Exception as e:
        logger.error(f"Erro: {e}")
        return []

@app.route('/')
def home():
    return "<h1>Servidor GehTV Ativo</h1><p><a href='/lista.m3u'>Clique aqui para a Lista M3U</a></p>"

@app.route('/lista.m3u')
def generate_m3u():
    channels = fetch_channels()
    if not channels:
        return "Erro: O servidor bloqueou o acesso do Railway. Tente acessar /debug.", 503
    
    m3u = "#EXTM3U\n"
    for c in channels:
        m3u += f'#EXTINF:-1 tvg-name="{c["name"]}",{c["name"]}\n{c["url"]}\n'
    return Response(m3u, mimetype='application/x-mpegURL')

@app.route('/debug')
def debug():
    app_id = "3713506"
    url = f"https://config.e-droid.net/srv/config.php?v=228&idapp={app_id}"
    r = requests.get(url, headers={'User-Agent': 'Android Vinebre Software', 'X-Requested-With': 'go.geh'})
    return jsonify({
        "status": r.status_code,
        "raw_response": r.text[:1000]
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
