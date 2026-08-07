import requests
import re
import os
from flask import Flask, Response, request, jsonify

app = Flask(__name__)

# Configurações de Identidade
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

def resolver_sinal(url, referer):
    """ Tenta extrair o link real .m3u8 simulando um navegador """
    session = requests.Session()
    headers = {
        "User-Agent": UA,
        "Referer": referer,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,webp,*/*;q=0.8"
    }
    
    try:
        # 1. Acessa a página do player
        response = session.get(url, headers=headers, timeout=10)
        html = response.text

        # 2. Procura por links .m3u8 no código (comum em players Clappr ou VideoJS)
        # Procura em aspas simples ou duplas, tratando barras invertidas
        match = re.search(r'["\'](https?://[^\s"\']+?\.m3u8[^\s"\']*)["\']', html)
        if match:
            stream_url = match.group(1).replace("\\/", "/")
            # Retorna o link com o sufixo de headers para o player IPTV
            return f"{stream_url}|User-Agent={UA}&Referer={url}"

        # 3. Se não achar, tenta buscar dentro de IFRAMES
        iframes = re.findall(r'<iframe.*?src=["\'](https?://.*?)["\']', html)
        for ifr_url in iframes:
            if "google" not in ifr_url and "ads" not in ifr_url:
                # Busca recursiva no iframe
                return resolver_sinal(ifr_url, url)

    except Exception as e:
        print(f"Erro ao resolver {url}: {e}")
    
    return None

@app.route('/')
def home():
    return f"<h1>Servidor Ativo</h1><p>Playlist: {request.host_url}playlist.m3u</p>"

@app.route('/playlist.m3u')
def playlist():
    """ Gera a playlist M3U unificada """
    channels = ["#EXTM3U"]
    base_url = request.host_url.rstrip('/')

    # --- S1 (Sinal Público) ---
    try:
        r1 = requests.get("https://apisinalpublico.vercel.app/canais.json", timeout=10)
        for c in r1.json():
            name, logo, target = c.get('name'), c.get('image'), c.get('url')
            link = f"{base_url}/play?s=S1&id={target}"
            channels.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="S1", [S1] {name}\n{link}')
    except: pass

    # --- S2 (Minha Tela) ---
    try:
        h2 = {"Referer": "https://minhatela.xyz/", "User-Agent": UA}
        r2 = requests.get("https://myapiplay.top/api/guiadejogos/epg.php", headers=h2, timeout=10)
        for c in r2.json():
            if c.get('channelLogo'):
                name, logo = c.get('name'), c.get('logo')
                # Gera link direto do player deles
                target = f"https://meuplayeronlinehd.com/myplay/watch.html?id={c.get('channelLogo')}"
                link = f"{base_url}/play?s=S2&id={target}"
                channels.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="S2", [S2] {name}\n{link}')
    except: pass

    return Response("\n".join(channels), mimetype='text/plain')

@app.route('/play')
def play():
    """ Roda o resolvedor e redireciona para o sinal real """
    source = request.args.get('s')
    target = request.args.get('id')
    
    ref = "https://sinalpublic.vercel.app/" if source == "S1" else "https://minhatela.xyz/"
    
    real_link = resolver_sinal(target, ref)
    
    if real_link:
        # Redireciona o player de IPTV para o fluxo direto
        return Response("", status=302, headers={"Location": real_link})
    
    # Se tudo falhar, tenta o link original
    return Response("", status=302, headers={"Location": target})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
