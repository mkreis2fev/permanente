from flask import Flask, jsonify
from flask_cors import CORS
import requests
import re
import os
import m3u8

app = Flask(__name__)
CORS(app)

# Lista de links que você irá mandar
LINKS = [
    "https://t5r4e3w2q1y0.s21-cloudfront-net.lat/test/621b3ae6f484f822954cfcdb5e94d66d/file.txt",
]

def extrair_canais(url):
    canais = []
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            m3u8_obj = m3u8.loads(response.text)

            # Caso seja um Master Playlist (várias qualidades do mesmo canal)
            if m3u8_obj.playlists:
                for playlist in m3u8_obj.playlists:
                    name = playlist.stream_info.name or f"Qualidade {playlist.stream_info.bandwidth}"
                    canais.append({"name": name, "url": playlist.absolute_uri or playlist.uri})

            # Caso seja uma lista de segmentos (canal único) ou lista IPTV
            elif m3u8_obj.segments:
                lines = response.text.splitlines()
                temp_canais = []
                for i in range(len(lines)):
                    if lines[i].startswith("#EXTINF"):
                        info = lines[i]
                        name_match = re.search(r',([^,]*)$', info)
                        name = name_match.group(1).strip() if name_match else "Canal"
                        if i + 1 < len(lines):
                            link = lines[i+1].strip()
                            if link.startswith("http"):
                                temp_canais.append({"name": name, "url": link})

                if len(temp_canais) > 1:
                    canais = temp_canais
                else:
                    # Se for apenas um stream fragmentado, tratamos o link original como o canal
                    name = url.split('/')[-2] if len(url.split('/')) > 2 else "Canal TV"
                    canais.append({"name": name, "url": url})
            else:
                canais.append({"name": "Canal", "url": url})

    except Exception as e:
        print(f"Erro ao processar {url}: {e}")
    return canais

@app.route('/')
def index():
    return "Servidor TV Online está ativo! Use /canais para ver a lista."

@app.route('/canais')
def get_canais():
    todos_canais = []
    for link in LINKS:
        todos_canais.extend(extrair_canais(link))

    return jsonify({
        "total": len(todos_canais),
        "canais": todos_canais
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
