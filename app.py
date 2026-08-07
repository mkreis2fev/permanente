import requests
import re
import os
from flask import Flask, Response, request, redirect, render_template_string

app = Flask(__name__)

# Configurações de Navegação (Fingindo ser um navegador real)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

def resolver_s1(cid):
    """ Varre o Sinal Público para extrair o sinal de vídeo atual """
    try:
        # Acessa a página do player intermediário
        url_player = f"https://sinalpublicoetv.vercel.app/?id={cid}"
        headers = {"User-Agent": UA, "Referer": "https://sinalpublic.vercel.app/"}
        res = requests.get(url_player, headers=headers, timeout=5)
        
        # Procura o link do player final no github.io dentro do código
        iframe_match = re.search(r'src=["\'](https?://sinaldvd\.github\.io/tv/player\.html\?id=.*?)["\']', res.text)
        if iframe_match:
            iframe_url = iframe_match.group(1)
            # Acessa o player final para capturar o link .m3u8
            res2 = requests.get(iframe_url, headers={"User-Agent": UA, "Referer": url_player}, timeout=5)
            m3u8_match = re.search(r'["\'](https?://.*?\.m3u8.*?)["\']', res2.text)
            if m3u8_match:
                return m3u8_match.group(1).replace("\\/", "/")
    except Exception as e:
        print(f"Erro ao resolver S1 ({cid}): {e}")
    
    # Fallback para o domínio de nuvem comum do S1
    return f"https://t5r4e3w2q1y0-cloudflare-net.vercel.app/{cid}.m3u8"

def resolver_s2(cid):
    """ Varre o Minha Tela para extrair o sinal de vídeo atual """
    try:
        # Minha Tela geralmente usa este player base
        url_player = f"https://meuplayeronlinehd.com/myplay/watch.html?id={cid}"
        headers = {"User-Agent": UA, "Referer": "https://minhatela.xyz/"}
        res = requests.get(url_player, headers=headers, timeout=5)
        
        # Tenta capturar o link do stream .m3u8 direto do código fonte do player
        m3u8_match = re.search(r'["\'](https?://.*?\.m3u8.*?)["\']', res.text)
        if m3u8_match:
            return m3u8_match.group(1).replace("\\/", "/")
    except Exception as e:
        print(f"Erro ao resolver S2 ({cid}): {e}")
    return None

@app.route('/')
def index():
    host = request.host_url
    return render_template_string("""
        <body style="font-family:sans-serif; background:#0f172a; color:white; text-align:center; padding:50px;">
            <h1 style="color:#3b82f6;">🚀 IPTV Proxy Server - S1 & S2</h1>
            <p>Servidor de captura dinâmica para Railway</p>
            <div style="background:#1e293b; padding:20px; border-radius:10px; border:1px solid #334155; display:inline-block; margin:20px;">
                <p>Playlist M3U:</p>
                <code style="color:#10b981; font-size:1.1em;">{{ host }}playlist.m3u</code>
            </div>
            <p style="color:#64748b; font-size:0.9em;">Recomendado: OTT Navigator, Televizo ou VLC.</p>
        </body>
    """, host=host)

@app.route('/playlist.m3u')
def playlist():
    host = request.host_url.rstrip('/')
    m3u = ["#EXTM3U"]
    
    # --- Fonte S1: Sinal Público ---
    try:
        r1 = requests.get("https://apisinalpublico.vercel.app/canais.json", timeout=10).json()
        for c in r1:
            cid = c.get('url', '').split('=')[-1]
            if cid:
                m3u.append(f'#EXTINF:-1 tvg-logo="{c.get("image")}" group-title="S1 (Sinal Publico)", [S1] {c.get("name")}')
                m3u.append(f'{host}/play/s1/{cid}')
    except: pass

    # --- Fonte S2: Minha Tela ---
    try:
        h2 = {"Referer": "https://minhatela.xyz/", "User-Agent": UA}
        r2 = requests.get("https://myapiplay.top/api/guiadejogos/epg.php", headers=h2, timeout=10).json()
        for c in r2:
            cid = c.get('channelLogo')
            if cid:
                m3u.append(f'#EXTINF:-1 tvg-logo="{c.get("logo")}" group-title="S2 (Minha Tela)", [S2] {c.get("name")}')
                m3u.append(f'{host}/play/s2/{cid}')
    except: pass

    return Response("\n".join(m3u), mimetype='text/plain')

@app.route('/play/<source>/<cid>')
def play(source, cid):
    """ Rota que resolve o link final e redireciona o reprodutor """
    stream_url = None
    referer = ""

    if source == 's1':
        stream_url = resolver_s1(cid)
        referer = "https://sinaldvd.github.io/"
    elif source == 's2':
        stream_url = resolver_s2(cid)
        referer = f"https://meuplayeronlinehd.com/myplay/watch.html?id={cid}"

    if stream_url:
        # Formato que players de IPTV entendem para passar o Referer corretamente
        final_url = f"{stream_url}|Referer={referer}&User-Agent={UA}"
        return redirect(final_url)
    
    return "Não foi possível capturar o sinal do canal.", 404

if __name__ == '__main__':
    # Configuração para rodar no Railway
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
