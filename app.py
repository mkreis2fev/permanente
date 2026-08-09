import os
import requests
import json
import logging
from flask import Flask, Response, jsonify

# Configuração de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def decode_url(url, cr):
    if not url or not url.startswith("@y@") or not cr:
        return url
    mapping_orig = " !#$%&()+,-./023456789:;<=>?ABCDEFGHIJKLMNOPQRSTUVWXYZ[^_abcdefghijklmnopqrstuvwxz{}~"
    try:
        # Lógica de substituição do AppCreator24
        decoded = "".join([mapping_orig[cr.find(c)] if c in cr else c for c in url[3:]])
        return decoded.replace("@yy1111@", "https://").replace("@yy111@", "https://www.").replace("@yy11@", "http://").replace("@yy1@", "http://www.")
    except:
        return url

def fetch_channels():
    app_id = "3713506"
    # v=260 é a versão mais recente que traz submenus abertos
    config_url = f"https://config.e-droid.net/srv/config.php?v=260&idapp={app_id}"
    headers = {'User-Agent': 'Android Vinebre Software'}
    
    try:
        response = requests.get(config_url, headers=headers, timeout=15, verify=False)
        if response.status_code != 200:
            return []

        data = response.json()
        cr = data.get("cr", "")
        secciones = data.get("secciones", [])
        
        # Converte dicionário para lista se necessário
        if isinstance(secciones, dict):
            secciones = list(secciones.values())

        channels = []

        # Função para entrar em todos os menus (TV > CATEGORIA > CANAL)
        def deep_scan(items):
            for item in items:
                if not isinstance(item, dict): continue
                
                url_raw = item.get("url", "")
                tipo = str(item.get("tipo", ""))
                
                # Se for tipo 6 ou tiver link de vídeo
                if tipo == "6" or ".m3u8" in url_raw or url_raw.startswith("@y@"):
                    if url_raw:
                        channels.append({
                            "name": item.get("tit", "Canal Sem Nome"),
                            "url": decode_url(url_raw, cr)
                        })
                
                # Procura sub-itens dentro de Menus (tipo 12)
                for key in ["atribs", "submenu_items", "items"]:
                    if key in item and item[key]:
                        sub_items = item[key]
                        if isinstance(sub_items, dict): sub_items = list(sub_items.values())
                        deep_scan(sub_items)

        deep_scan(secciones)
        return channels
    except Exception as e:
        logger.error(f"Erro ao capturar: {e}")
        return []

@app.route('/')
def home():
    # Rota raiz para teste
    return "<h1>Servidor GehTV Ativo</h1><p>Use: <a href='/lista.m3u'>/lista.m3u</a></p>"

@app.route('/lista.m3u')
def generate_m3u():
    channels = fetch_channels()
    if not channels:
        return "Erro: O servidor do GehTV nao retornou canais. Tente novamente em instantes.", 503
    
    m3u_content = "#EXTM3U\n"
    for channel in channels:
        m3u_content += f'#EXTINF:-1 tvg-name="{channel["name"]}",{channel["name"]}\n'
        m3u_content += f'{channel["url"]}\n'
        
    return Response(m3u_content, mimetype='application/x-mpegURL')

@app.route('/debug')
def debug():
    # Rota para ver se o JSON está chegando
    app_id = "3713506"
    config_url = f"https://config.e-droid.net/srv/config.php?v=260&idapp={app_id}"
    r = requests.get(config_url, headers={'User-Agent': 'Android Vinebre Software'}, verify=False)
    return jsonify({
        "status": r.status_code,
        "content_length": len(r.text),
        "preview": r.text[:500]
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
