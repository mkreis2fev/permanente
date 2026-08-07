import requests
import re
import os
from flask import Flask, Response, request, render_template_string

app = Flask(__name__)

# Configurações de Identificação
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def resolver_m3u8(url, referer):
    """ Entra na página do player e extrai o link .m3u8 real """
    try:
        headers = {"User-Agent": UA, "Referer": referer}
        response = requests.get(url, headers=headers, timeout=10)
        html = response.text
        
        # Procura por links .m3u8 (HLS) no código-fonte
        # Tenta encontrar em variáveis JS ou links diretos
        found_links = re.findall(r'["\'](https?://[^\s"\']+?\.m3u8[^\s"\']*)["\']', html)
        
        if found_links:
            link = found_links[0].replace("\\/", "/")
            # Alguns players precisam do Referer grudado no link para o App IPTV aceitar
            return f"{link}|Referer={referer}&User-Agent={UA}"
            
        # Busca em iframes caso não ache na principal
        iframe = re.search(r'iframe.*?src=["\'](https?://.*?)["\']', html)
        if iframe:
            iframe_url = iframe.group(1)
            if "google" not in iframe_url:
                return resolver_m3u8(iframe_url, url)
    except:
        pass
    return None

@app.route('/')
def home():
    host = request.host_url
    return render_template_string("""
        <body style="font-family:sans-serif; background:#0f172a; color:white; text-align:center; padding:50px;">
            <h1 style="color:#3b82f6;">Agregador IPTV S1 & S2</h1>
            <div style="background:#1e293b; padding:20px; border-radius:10px; border:1px solid #334155; display:inline-block;">
                <p>Cole este link no seu aplicativo de IPTV:</p>
                <code style="color:#10b981; font-size:1.2em;">{{ host }}playlist.m3u</code>
            </div>
            <p style="margin-top:20px; color:#64748b;">S1: Sinal Público | S2: Minha Tela</p>
        </body>
    """, host=host)

@app.route('/playlist.m3u')
def playlist():
    channels = []
    base_url = request.host_url.rstrip('/')

    # --- EXTRAÇÃO S1 (Sinal Público) ---
    try:
        r1 = requests.get("https://apisinalpublico.vercel.app/canais.json", timeout=10)
        for c in r1.json():
            name = c.get('name')
            logo = c.get('image')
            target = c.get('url')
            # Rota de redirecionamento para o nosso servidor resolver o link
            link = f"{base_url}/play?s=S1&id={target}"
            channels.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="S1", [S1] {name}\n{link}')
    except: pass

    # --- EXTRAÇÃO S2 (Minha Tela) ---
    try:
        h2 = {"Referer": "https://minhatela.xyz/", "User-Agent": UA}
        r2 = requests.get("https://myapiplay.top/api/guiadejogos/epg.php", headers=h2, timeout=10)
        for c in r2.json():
            if c.get('channelLogo'):
                name = c.get('name')
                logo = c.get('logo')
                target = f"https://meuplayeronlinehd.com/myplay/watch.html?id={c.get('channelLogo')}"
                link = f"{base_url}/play?s=S2&id={target}"
                channels.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="S2", [S2] {name}\n{link}')
    except: pass

    m3u = "#EXTM3U\n" + "\n".join(channels)
    return Response(m3u, mimetype='text/plain')

@app.route('/play')
def play():
    """ Rota que resolve o link e redireciona o fluxo """
    source = request.args.get('s')
    target = request.args.get('id')
    referer = "https://sinalpublic.vercel.app/" if source == "S1" else "https://minhatela.xyz/"
    
    real_link = resolver_m3u8(target, referer)
    
    if real_link:
        # Redireciona o aplicativo para o sinal direto decodificado
        return Response("", status=302, headers={"Location": real_link})
    return "Não foi possível carregar o sinal.", 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
