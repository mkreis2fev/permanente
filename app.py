import requests
import re
import os
from flask import Flask, Response, request, redirect, render_template_string
from urllib.parse import quote

app = Flask(__name__)

# Configurações de Navegação
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

def resolver_m3u8(url, referer):
    """ Tenta encontrar o link .m3u8 real dentro do HTML """
    try:
        headers = {"User-Agent": UA, "Referer": referer}
        res = requests.get(url, headers=headers, timeout=10)
        # Procura por padrões de .m3u8
        match = re.search(r'["\'](https?://[^\s"\']+?\.m3u8[^\s"\']*)["\']', res.text)
        if match:
            return match.group(1).replace("\\/", "/")
        # Tenta em iframe
        iframe = re.search(r'<iframe.*?src=["\'](https?://.*?)["\']', res.text)
        if iframe and "google" not in iframe.group(1):
            return resolver_m3u8(iframe.group(1), url)
    except: pass
    return None

@app.route('/')
def home():
    return f"Playlist: {request.host_url}playlist.m3u"

@app.route('/playlist.m3u')
def playlist():
    host = request.host_url.rstrip('/')
    m3u = ["#EXTM3U"]
    
    # S1 - Sinal Público (Varrer API)
    try:
        r1 = requests.get("https://apisinalpublico.vercel.app/canais.json", timeout=10).json()
        for c in r1:
            cid = c.get('url', '').split('=')[-1]
            if cid:
                # Link aponta para o resolvedor direto
                link = f"{host}/play/s1/{cid}"
                m3u.append(f'#EXTINF:-1 tvg-logo="{c.get("image")}" group-title="S1", [S1] {c.get("name")}\n{link}')
    except: pass

    # S2 - Minha Tela (Varrer API)
    try:
        h2 = {"Referer": "https://minhatela.xyz/", "User-Agent": UA}
        r2 = requests.get("https://myapiplay.top/api/guiadejogos/epg.php", headers=h2, timeout=10).json()
        for c in r2:
            cid = c.get('channelLogo')
            if cid:
                link = f"{host}/play/s2/{cid}"
                m3u.append(f'#EXTINF:-1 tvg-logo="{c.get("logo")}" group-title="S2", [S2] {c.get("name")}\n{link}')
    except: pass

    return Response("\n".join(m3u), mimetype='text/plain')

@app.route('/play/<source>/<cid>')
def play_redirect(source, cid):
    """ Resolve o link e redireciona com o sufixo de headers """
    target_m3u8 = ""
    referer = ""

    if source == 's1':
        # S1 usa vários domínios Vercel/Cloudflare. Tentamos os mais comuns:
        urls_tentar = [
            f"https://t5r4e3w2q1y0-cloudflare-net.vercel.app/{cid}.m3u8",
            f"https://a9b8c7d6e5f4-cloudflare-net.vercel.app/{cid}.m3u8"
        ]
        referer = "https://sinaldvd.github.io/"
        
        # Testamos qual está on-line
        for url in urls_tentar:
            try:
                check = requests.head(url, headers={"User-Agent": UA, "Referer": referer}, timeout=3)
                if check.status_code == 200:
                    target_m3u8 = url
                    break
            except: continue
        
        if not target_m3u8: target_m3u8 = urls_tentar[0] # Fallback

    else:
        # S2 - Minha Tela
        player_page = f"https://meuplayeronlinehd.com/myplay/watch.html?id={cid}"
        target_m3u8 = resolver_m3u8(player_page, "https://minhatela.xyz/")
        referer = "https://minhatela.xyz/"
        if not target_m3u8:
            # Fallback se não conseguir varrer
            target_m3u8 = f"https://meuplayeronlinehd.com/hls/{cid}.m3u8"

    # Monta o link final com o segredo do Referer para o TiviMate/VLC
    # Formato: link.m3u8|User-Agent=...&Referer=...
    final_url = f"{target_m3u8}|User-Agent={quote(UA)}&Referer={quote(referer)}"
    
    return redirect(final_url)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
