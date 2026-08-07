import requests
import re
import os
from flask import Flask, Response, request, render_template_string, redirect
from urllib.parse import urljoin

app = Flask(__name__)

# Configuração de Navegação
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

def extrair_link_direto(url_player, referer):
    """ Entra no site e pega o link .m3u8 real """
    try:
        headers = {"User-Agent": UA, "Referer": referer}
        res = requests.get(url_player, headers=headers, timeout=10)
        html = res.text
        
        # Busca por links m3u8 no código
        matches = re.findall(r'["\'](https?://[^\s"\']+?\.m3u8[^\s"\']*)["\']', html)
        if matches:
            return matches[0].replace("\\/", "/")
            
        # Se estiver em iframe, entra nele
        iframe = re.search(r'<iframe.*?src=["\'](https?://.*?)["\']', html)
        if iframe:
            return extrair_link_direto(iframe.group(1), url_player)
    except:
        pass
    return None

@app.route('/')
def home():
    return render_template_string("""
        <body style="font-family:sans-serif; background:#0f172a; color:white; text-align:center; padding:50px;">
            <h1 style="color:#3b82f6;">📡 Servidor IPTV S1 & S2</h1>
            <p>Lista M3U Unificada e Desbloqueada</p>
            <div style="background:#1e293b; padding:20px; border-radius:10px; border:1px solid #334155; display:inline-block;">
                Link para o seu App:<br>
                <code style="color:#10b981; font-size:1.2em;">{{ host }}playlist.m3u</code>
            </div>
        </body>
    """, host=request.host_url)

@app.route('/playlist.m3u')
def playlist():
    lines = ["#EXTM3U"]
    host = request.host_url.rstrip('/')

    # S1 - Sinal Público
    try:
        r1 = requests.get("https://apisinalpublico.vercel.app/canais.json", timeout=10)
        for c in r1.json():
            # Pegamos o ID do canal da URL
            cid = c.get('url').split('=')[-1]
            link = f"{host}/stream.m3u8?s=s1&id={cid}"
            lines.append(f'#EXTINF:-1 tvg-logo="{c.get("image")}" group-title="S1", [S1] {c.get("name")}\n{link}')
    except: pass

    # S2 - Minha Tela
    try:
        h2 = {"Referer": "https://minhatela.xyz/", "User-Agent": UA}
        r2 = requests.get("https://myapiplay.top/api/guiadejogos/epg.php", headers=h2, timeout=10)
        for c in r2.json():
            if c.get('channelLogo'):
                link = f"{host}/stream.m3u8?s=s2&id={c.get('channelLogo')}"
                lines.append(f'#EXTINF:-1 tvg-logo="{c.get("logo")}" group-title="S2", [S2] {c.get("name")}\n{link}')
    except: pass

    return Response("\n".join(lines), mimetype='text/plain')

@app.route('/stream.m3u8')
def stream():
    """ Rota que engana o player e entrega o vídeo real """
    source = request.args.get('s')
    cid = request.args.get('id')
    
    if source == 's1':
        # S1 usa um redirector próprio
        target = f"https://t5r4e3w2q1y0-cloudflare-net.vercel.app/{cid}.m3u8"
        ref = "https://sinaldvd.github.io/"
    else:
        # S2 extrai do player do Minha Tela
        player_url = f"https://meuplayeronlinehd.com/myplay/watch.html?id={cid}"
        target = extrair_link_direto(player_url, "https://minhatela.xyz/") or player_url
        ref = "https://minhatela.xyz/"

    # Adiciona a "Chave" de desbloqueio que os Apps IPTV (Smarters/OTT/TiviMate) entendem
    final_url = f"{target}|Referer={ref}&User-Agent={UA}"
    return redirect(final_url)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
