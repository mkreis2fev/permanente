import requests
import re
import os
from flask import Flask, Response, request, render_template_string

app = Flask(__name__)

# Configuração de Navegação para evitar bloqueios
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

def catch_m3u8(url, referer):
    """
    Entra no site, simula um navegador e captura o link real do vídeo (.m3u8)
    """
    try:
        headers = {"User-Agent": UA, "Referer": referer}
        # 1. Tenta acessar a página do player
        response = requests.get(url, headers=headers, timeout=10)
        html = response.text

        # 2. Busca o link do sinal (.m3u8) no código fonte
        # Procura por padrões como source: "...", file: "..." ou link direto
        matches = re.findall(r'["\'](https?://[^\s"\']+?\.m3u8[^\s"\']*)["\']', html)
        
        if matches:
            direct_link = matches[0].replace("\\/", "/")
            # Retorna o link decorado com headers que o App de IPTV reconhece
            return f"{direct_link}|User-Agent={UA}&Referer={url}"

        # 3. Se estiver em um IFRAME, tenta entrar nele (Busca profunda)
        iframe = re.search(r'<iframe.*?src=["\'](https?://.*?)["\']', html)
        if iframe:
            iframe_url = iframe.group(1)
            if "google" not in iframe_url:
                return catch_m3u8(iframe_url, url)
    except:
        pass
    return None

@app.route('/')
def index():
    host = request.host_url
    return render_template_string("""
        <body style="font-family:sans-serif; background:#0f172a; color:white; text-align:center; padding:50px;">
            <h1 style="color:#3b82f6;">Agregador IPTV S1 & S2 Ativo</h1>
            <p>Use o link abaixo no seu aplicativo de IPTV:</p>
            <div style="background:#1e293b; padding:15px; border-radius:8px; border:1px solid #334155; display:inline-block;">
                <code style="color:#10b981; font-size:1.1em;">{{ host }}playlist.m3u</code>
            </div>
        </body>
    """, host=host)

@app.route('/playlist.m3u')
def playlist():
    """Gera a lista M3U unificada e identificada"""
    m3u = ["#EXTM3U"]
    base_url = request.host_url.rstrip('/')

    # --- CANAIS S1 (Sinal Público) ---
    try:
        r1 = requests.get("https://apisinalpublico.vercel.app/canais.json", timeout=10)
        for c in r1.json():
            name, logo, target = c.get('name'), c.get('image'), c.get('url')
            # O link aponta para nossa rota /play que vai 'limpar' o sinal
            link = f"{base_url}/play?s=S1&id={target}"
            m3u.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="S1", [S1] {name}\n{link}')
    except: pass

    # --- CANAIS S2 (Minha Tela) ---
    try:
        h2 = {"Referer": "https://minhatela.xyz/", "User-Agent": UA}
        r2 = requests.get("https://myapiplay.top/api/guiadejogos/epg.php", headers=h2, timeout=10)
        for c in r2.json():
            if c.get('channelLogo'):
                name, logo = c.get('name'), c.get('logo')
                target = f"https://meuplayeronlinehd.com/myplay/watch.html?id={c.get('channelLogo')}"
                link = f"{base_url}/play?s=S2&id={target}"
                m3u.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="S2", [S2] {name}\n{link}')
    except: pass

    return Response("\n".join(m3u), mimetype='text/plain')

@app.route('/play')
def play():
    """Converte o link do site em sinal de vídeo real e redireciona"""
    source = request.args.get('s')
    target = request.args.get('id')
    
    # Define de qual site vamos fingir que o acesso está vindo
    ref = "https://sinalpublic.vercel.app/" if source == "S1" else "https://minhatela.xyz/"
    
    # Tenta descobrir o link .m3u8 real
    real_stream = catch_m3u8(target, ref)
    
    if real_stream:
        # Redireciona o player IPTV para o link direto com headers de bypass
        return Response("", status=302, headers={"Location": real_stream})
    
    # Se falhar, tenta mandar o original (último recurso)
    return Response("", status=302, headers={"Location": target})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
