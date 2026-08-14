from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import requests
import re
import os
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)

# Lista de links com nome e logo personalizados
LINKS = [
    {
        "url": "https://t5r4e3w2q1y0.s21-cloudfront-net.lat/test/621b3ae6f484f822954cfcdb5e94d66d/file.txt",
        "name": "Globo News",
        "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globonews.png"
    }
]

def extrair_canais(link_info):
    url = link_info["url"]
    nome_padrao = link_info.get("name", "Canal TV")
    logo = link_info.get("logo", "")

    canais = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            content = response.text

            if "#EXTM3U" in content:
                # Criamos o link de Proxy para resolver os caminhos internos do vídeo
                link_proxy = f"{request.url_root}play.m3u8?u={url}"
                canais.append({
                    "name": nome_padrao,
                    "url": link_proxy,
                    "logo": logo
                })
            else:
                canais.append({"name": nome_padrao, "url": url, "logo": logo})
    except Exception as e:
        print(f"Erro ao processar {url}: {e}")

    if not canais:
        canais.append({"name": nome_padrao, "url": url, "logo": logo})
    return canais

@app.route('/')
def index():
    return "Servidor TV Online ativo! Use /lista.m3u no seu player."

@app.route('/canais')
def get_canais():
    todos = []
    for link in LINKS:
        todos.extend(extrair_canais(link))
    return jsonify({"total": len(todos), "canais": todos})

@app.route('/lista.m3u')
def get_m3u():
    todos = []
    for link in LINKS:
        todos.extend(extrair_canais(link))
    m3u = "#EXTM3U\n"
    for c in todos:
        # Adiciona o nome e o logo no formato padrão M3U para o player
        logo_attr = f' tvg-logo="{c["logo"]}"' if c.get("logo") else ""
        m3u += f'#EXTINF:-1{logo_attr}, {c["name"]}\n{c["url"]}\n'
    return Response(m3u, mimetype='text/plain')

# ESTA ROTA É O "TRADUTOR" QUE FAZ O VÍDEO FUNCIONAR NO CLOUDFRONT
@app.route('/play.m3u8')
def proxy_m3u8():
    target_url = request.args.get('u')
    if not target_url:
        return "URL ausente", 400

    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(target_url, headers=headers)
        
        # Pega o domínio original para completar os links internos do arquivo .txt
        parsed_uri = urlparse(target_url)
        domain_base = f"{parsed_uri.scheme}://{parsed_uri.netloc}"

        lines = resp.text.splitlines()
        new_lines = []

        for line in lines:
            line = line.strip()
            # Resolve caminhos que começam com /
            if line.startswith("/") and not line.startswith("//"):
                new_lines.append(domain_base + line)
            # Resolve caminhos relativos sem /
            elif line and not line.startswith("#") and not line.startswith("http"):
                path_base = target_url.rsplit('/', 1)[0]
                new_lines.append(path_base + "/" + line)
            else:
                new_lines.append(line)

        return Response("\n".join(new_lines), mimetype='application/vnd.apple.mpegurl')
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    # Porta configurada automaticamente pelo Railway
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
