import requests
from flask import Flask, jsonify, render_template_string
import os

app = Flask(__name__)

# Configurações das fontes de extração
SOURCES = {
    "minhatela": {
        "url": "https://myapiplay.top/api/guiadejogos/epg.php",
        "referer": "https://minhatela.xyz/",
        "player_base": "https://meuplayeronlinehd.com/myplay/watch.html?id="
    },
    "sinalpublic": {
        "url": "https://apisinalpublico.vercel.app/canais.json",
        "referer": "https://sinalpublic.vercel.app/"
    }
}

def fetch_minhatela():
    """Extrai canais do site Minha Tela"""
    try:
        headers = {
            "Referer": SOURCES["minhatela"]["referer"],
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(SOURCES["minhatela"]["url"], headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            channels = []
            for item in data:
                if item.get("channelLogo"):
                    channels.append({
                        "name": item.get("name"),
                        "embed_url": f"{SOURCES['minhatela']['player_base']}{item.get('channelLogo')}",
                        "logo": item.get("logo"),
                        "source": "Minha Tela"
                    })
            return channels
    except Exception as e:
        print(f"Erro Minha Tela: {e}")
    return []

def fetch_sinalpublic():
    """Extrai canais do site Sinal Público"""
    try:
        headers = {
            "Referer": SOURCES["sinalpublic"]["referer"],
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(SOURCES["sinalpublic"]["url"], headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            channels = []
            for item in data:
                channels.append({
                    "name": item.get("name"),
                    "embed_url": item.get("url"),
                    "logo": item.get("image"),
                    "source": "Sinal Público"
                })
            return channels
    except Exception as e:
        print(f"Erro Sinal Público: {e}")
    return []

@app.route('/')
def index():
    """Página inicial com interface visual"""
    html = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Meu Agregador de Canais</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f0f0f; color: white; padding: 20px; }
            h1 { text-align: center; color: #007bff; }
            .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 15px; margin-top: 30px; }
            .card { background: #1a1a1a; padding: 15px; border-radius: 12px; text-align: center; border: 1px solid #333; transition: 0.3s; }
            .card:hover { transform: translateY(-5px); border-color: #007bff; box-shadow: 0 5px 15px rgba(0,123,255,0.3); }
            img { width: 100%; height: 80px; object-fit: contain; margin-bottom: 10px; border-radius: 5px; background: #000; }
            .name { font-size: 0.9em; font-weight: bold; height: 40px; overflow: hidden; }
            .source { font-size: 0.7em; color: #888; margin-bottom: 10px; }
            .btn { background: #007bff; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-size: 0.8em; display: inline-block; }
        </style>
    </head>
    <body>
        <h1>📺 Canais Ao Vivo</h1>
        <div class="grid" id="channels">Carregando canais...</div>
        <script>
            fetch('/api/channels').then(r => r.json()).then(data => {
                const container = document.getElementById('channels');
                container.innerHTML = '';
                data.forEach(c => {
                    const card = document.createElement('div');
                    card.className = 'card';
                    card.innerHTML = `
                        <img src="${c.logo}" onerror="this.src='https://placehold.co/150x100/1e1e1e/white?text=TV'">
                        <div class="name">${c.name}</div>
                        <div class="source">${c.source}</div>
                        <a href="${c.embed_url}" class="btn" target="_blank">ASSISTIR</a>
                    `;
                    container.appendChild(card);
                });
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/api/channels')
def get_channels():
    """Endpoint da API que retorna o JSON unificado"""
    all_channels = fetch_minhatela() + fetch_sinalpublic()
    return jsonify(all_channels)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
