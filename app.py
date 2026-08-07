import requests
import re
import os
from flask import Flask, Response, request, jsonify

app = Flask(__name__)

# Headers para fingir ser um navegador real
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
}

def extrair_sinal_real(url, referer):
    """ Tenta encontrar o link .m3u8 escondido no código do site """
    try:
        h = HEADERS.copy()
        h["Referer"] = referer
        
        # 1. Acessa a página do player
        resp = requests.get(url, headers=h, timeout=10)
        html = resp.text

        # 2. Busca padrão de link .m3u8 (HLS) no JavaScript ou HTML
        # Procura por: "https://...m3u8" ou 'https://...m3u8'
        links = re.findall(r'["\'](https?://[^\s"\']+?\.m3u8[^\s"\']*)["\']', html)
        
        if links:
            # Pega o primeiro link encontrado e limpa escapes de barra
            return links[0].replace("\\/", "/")

        # 3. Se não achar, tenta buscar dentro de um IFRAME
        iframe = re.search(r'iframe.*?src=["\'](.*?)["\']', html)
        if iframe:
            iframe_url = iframe.group(1)
            if iframe_url.startswith("//"): iframe_url = "https:" + iframe_url
            if "google" not in iframe_url: # Evita anúncios
                return extrair_sinal_real(iframe_url, url)

    except Exception as e:
        print(f"Erro ao extrair de {url}: {e}")
    return None

@app.route('/')
def index():
    return "<h1>Servidor IPTV S1 & S2 Ativo</h1><p>Playlist: /playlist.m3u</p>"

@app.route('/playlist.m3u')
def playlist():
    """ Gera a playlist com o resolvedor de links integrado """
    lines = ["#EXTM3U"]
    base_url = request.host_url.rstrip('/')

    # --- CANAIS S1 (Sinal Público) ---
    try:
        r1 = requests.get("https://apisinalpublico.vercel.app/canais.json", timeout=10)
        for c in r1.json():
            name = c.get("name")
            target = c.get("url")
            logo = c.get("image")
            # Link que passa pelo nosso script para ser 'desbloqueado'
            link = f"{base_url}/stream?url={target}&ref=https://sinalpublic.vercel.app/"
            lines.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="S1", [S1] {name}\n{link}')
    except: pass

    # --- CANAIS S2 (Minha Tela) ---
    try:
        r2 = requests.get("https://myapiplay.top/api/guiadejogos/epg.php", 
                          headers={"Referer": "https://minhatela.xyz/"}, timeout=10)
        for c in r2.json():
            if c.get("channelLogo"):
                name = c.get("name")
                logo = c.get("logo")
                target = f"https://meuplayeronlinehd.com/myplay/watch.html?id={c.get('channelLogo')}"
                link = f"{base_url}/stream?url={target}&ref=https://minhatela.xyz/"
                lines.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="S2", [S2] {name}\n{link}')
    except: pass

    return Response("\n".join(lines), mimetype='text/plain')

@app.route('/stream')
def stream():
    """ Resolve o link em tempo real e redireciona o player """
    target_url = request.args.get('url')
    referer = request.args.get('ref')
    
    if not target_url:
        return "URL faltando", 400

    # Tenta descobrir o .m3u8 real
    real_m3u8 = extrair_sinal_real(target_url, referer)
    
    if real_m3u8:
        # Se achou o link direto, redireciona o player IPTV para ele
        return Response("", status=302, headers={"Location": real_m3u8})
    else:
        # Se falhou, manda para o link original (provavelmente não vai abrir no IPTV comum)
        return Response("", status=302, headers={"Location": target_url})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
