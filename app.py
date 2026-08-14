from flask import Flask, jsonify
from flask_cors import CORS
import requests
import re
import os
import m3u8

app = Flask(__name__)
CORS(app)

# Lista de links que você irá mandar (adicione mais links aqui se quiser)
LINKS = [
    "https://t5r4e3w2q1y0.s21-cloudfront-net.lat/test/621b3ae6f484f822954cfcdb5e94d66d/file.txt",
]

def extrair_canais(url):
    canais = []
    # Headers para simular um navegador e evitar bloqueios de servidores (como Cloudfront)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            content = response.text

            # Se o conteúdo contém tags M3U8 (comum em streams de vídeo)
            if "#EXTM3U" in content:
                m3u8_obj = m3u8.loads(content)

                # Caso 1: Master Playlist (múltiplas qualidades de vídeo)
                if m3u8_obj.playlists:
                    for playlist in m3u8_obj.playlists:
                        name = playlist.stream_info.name or f"Qualidade {playlist.stream_info.bandwidth}"
                        uri = playlist.absolute_uri or playlist.uri
                        canais.append({"name": name, "url": uri})

                # Caso 2: É uma lista de canais IPTV ou um stream único fragmentado
                else:
                    lines = content.splitlines()
                    temp_canais = []
                    for i in range(len(lines)):
                        if lines[i].startswith("#EXTINF"):
                            info = lines[i]
                            # Tenta pegar o nome do canal após a vírgula
                            name_match = re.search(r',([^,]*)$', info)
                            name = name_match.group(1).strip() if name_match else "Canal"

                            # Procura a URL do vídeo nas linhas seguintes (até 5 linhas abaixo)
                            for j in range(i + 1, min(i + 5, len(lines))):
                                next_line = lines[j].strip()
                                if next_line.startswith("http"):
                                    temp_canais.append({"name": name, "url": next_line})
                                    break

                    if temp_canais:
                        canais = temp_canais
                    else:
                        # Se for um stream mas sem lista de canais, usa o nome extraído da URL
                        nome_canal = url.split('/')[-2] if '/' in url else "Canal TV"
                        canais.append({"name": nome_canal, "url": url})
            else:
                # Se não for M3U8, trata como um link direto de vídeo/arquivo
                canais.append({"name": "Link Direto", "url": url})
        else:
            print(f"Erro na requisição: Status {response.status_code}")

    except Exception as e:
        print(f"Erro ao processar {url}: {e}")

    # Garantia final: se não conseguiu extrair nada, retorna o link original como canal
    if not canais and url.startswith("http"):
        nome_final = url.split('/')[-2] if len(url.split('/')) > 2 else "Canal"
        canais.append({"name": nome_final, "url": url})

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
    # O Railway define a porta automaticamente na variável de ambiente PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
