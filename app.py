import requests
import re
import os
from flask import Flask, Response, request, redirect, render_template_string
from urllib.parse import quote

app = Flask(__name__)

# Configurações de Agente
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

def capturar_m3u8(url, referer):
    """ Entra no player e varre o código fonte atrás do .m3u8 """
    try:
        headers = {"User-Agent": UA, "Referer": referer}
        res = requests.get(url, headers=headers, timeout=10)
        # Procura por qualquer link que termine em .m3u8
        match = re.search(r'["\'](https?://[^\s"\']+?\.m3u8[^\s"\']*)["\']', res.text)
        if match:
            return match.group(1).replace("\\/", "/")
        
        # Se houver um iframe, tenta entrar nele
        iframe = re.search(r'<iframe.*?src=["\'](https?://.*?)["\']', res.text)
        if iframe and "google" not in iframe.group(1):
            return capturar_m3u8(iframe.group(1), url)
    except: pass
    return None

@app.route('/')
def home():
    return f"Playlist: {request.host_url}playlist.m3u"

@app.route('/playlist.m3u')
def playlist():
    host = request.host_url.rstrip('/')
    m3u = ["#EXTM3U"]
    
    # S1 - Sinal Público
    try:
        r1 = requests.get("https://apisinalpublico.vercel.app/canais.json", timeout=10).json()
        for c in r1:
            cid = c.get('url', '').split('=')[-1]
            if cid:
                # Geramos um link de play simples
                link = f"{host}/play/s1/{cid}"
                m3u.append(f'#EXTINF:-1 tvg-logo="{c.get("image")}" group-title="S1", [S1] {c.get("name")}\n{link}')
    except: pass

    # S2 - Minha Tela
    try:
        headers_s2 = {"Referer": "https://minhatela.xyz/", "User-Agent": UA}
        r2 = requests.get("https://myapiplay.top/api/guiadejogos/epg.php", headers=headers_s2, timeout=10).json()
        for c in r2:
            cid = c.get('channelLogo')
            if cid:
                link = f"{host}/play/s2/{cid}"
                m3u.append(f'#EXTINF:-1 tvg-logo="{c.get("logo")}" group-title="S2", [S2] {c.get("name")}\n{link}')
    except: pass

    return Response("\n".join(m3u), mimetype='text/plain')

@app.route('/play/<source>/<cid>')
def play(source, cid):
    """ Resolve o link real e redireciona o player """
    target = None
    ref = ""

    if source == 's1':
        # Sinal Público: Primeiro tenta o link direto conhecido
        # domínios comuns: t5r4e3w2q1y0 ou a9b8c7d6e5f4
        target = f"https://t5r4e3w2q1y0-cloudflare-net.vercel.app/{cid}.m3u8"
        ref = "https://sinaldvd.github.io/"
        
        # Teste rápido de vida
        try:
            if requests.head(target, timeout=2).status_code != 200:
                target = f"https://a9b8c7d6e5f4-cloudflare-net.vercel.app/{cid}.m3u8"
        except: pass

    elif source == 's2':
        # Minha Tela: Varre o player dinamicamente
        url_player = f"https://meuplayeronlinehd.com/myplay/watch.html?id={cid}"
        target = capturar_m3u8(url_player, "https://minhatela.xyz/")
        ref = "https://minhatela.xyz/"
        if not target:
            target = f"https://meuplayeronlinehd.com/hls/{cid}.m3u8"

    if target:
        # Link com sufixo de headers para TiviMate/OTT/VLC
        final_link = f"{target}|User-Agent={quote(UA)}&Referer={quote(ref)}"
        return redirect(final_link)

    return "Canal não encontrado ou link expirado", 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
