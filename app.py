import requests
import re
from flask import Flask, jsonify, Response, request, render_template_string
import os

app = Flask(__name__)

# Configurações de Identificação
LABELS = {
    "S1": {"name": "S1", "ref": "https://sinalpublic.vercel.app/"},
    "S2": {"name": "S2", "ref": "https://minhatela.xyz/"}
}

def get_real_m3u8(url, referer):
    """ Tenta extrair o link .m3u8 real escondido no código do site """
    try:
        headers = {
            "Referer": referer,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        # 1. Pega o HTML da página do player
        response = requests.get(url, headers=headers, timeout=5)
        html = response.text
        
        # 2. Procura por padrões de links .m3u8 (HLS)
        # Tenta encontrar em variáveis JS (source: '...', file: '...', etc)
        match = re.search(r'["\'](https?://[0-9a-zA-Z\-\.\/\\\?\&\_=]+?\.m3u8.*?)["\']', html)
        if match:
            link = match.group(1).replace("\\/", "/")
            return link
            
        # 3. Se não achar, procura por iframes (muitos usam players externos)
        iframe_match = re.search(r'iframe.*?src=["\'](.*?)["\']', html)
        if iframe_match:
            iframe_url = iframe_match.group(1)
            if iframe_url.startswith("//"): iframe_url = "https:" + iframe_url
            return get_real_m3u8(iframe_url, url) # Busca recursiva
            
    except:
        pass
    return None

@app.route('/')
def home():
    return "<h1>Servidor IPTV S1 & S2 Ativo</h1><p>Link M3U: <b>/playlist.m3u</b></p>"

@app.route('/playlist.m3u')
def playlist():
    """ Gera a playlist com links que passam pelo nosso 'Resolvedor' """
    all_channels = []
    base_url = request.host_url.rstrip('/')
    
    # Busca canais S1 (Sinal Público)
    try:
        r1 = requests.get("https://apisinalpublico.vercel.app/canais.json", timeout=5)
        for item in r1.json():
            # Criamos um link que aponta para o nosso próprio servidor
            play_url = f"{base_url}/play?source=S1&id={item.get('url')}"
            all_channels.append(f'#EXTINF:-1 tvg-logo="{item.get("image")}" group-title="S1", [S1] {item.get("name")}\n{play_url}')
    except: pass

    # Busca canais S2 (Minha Tela)
    try:
        r2 = requests.get("https://myapiplay.top/api/guiadejogos/epg.php", 
                          headers={"Referer": "https://minhatela.xyz/"}, timeout=5)
        for item in r2.json():
            if item.get("channelLogo"):
                raw_url = f"https://meuplayeronlinehd.com/myplay/watch.html?id={item.get('channelLogo')}"
                play_url = f"{base_url}/play?source=S2&id={raw_url}"
                all_channels.append(f'#EXTINF:-1 tvg-logo="{item.get("logo")}" group-title="S2", [S2] {item.get("name")}\n{play_url}')
    except: pass

    m3u_content = "#EXTM3U\n" + "\n".join(all_channels)
    return Response(m3u_content, mimetype='text/plain')

@app.route('/play')
def play():
    """ 
    Esta é a parte mágica: Quando o player IPTV clica no canal, 
    nós descobrimos o link real e redirecionamos o player para ele.
    """
    source = request.args.get('source')
    target_url = request.args.get('id')
    
    if not source or not target_url:
        return "Erro: Parâmetros faltando", 400
        
    referer = LABELS[source]["ref"]
    
    # Tenta achar o sinal real (.m3u8)
    real_link = get_real_m3u8(target_url, referer)
    
    if real_link:
        # Redireciona o seu app IPTV para o link direto do vídeo
        return Response("", status=302, headers={"Location": real_link})
    else:
        # Se falhar em extrair, tenta redirecionar para a URL original (última tentativa)
        return Response("", status=302, headers={"Location": target_url})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
