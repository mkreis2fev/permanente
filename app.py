import requests
import re
import os
from flask import Flask, Response, request, render_template_string

app = Flask(__name__)

# Configuração de Navegação
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

def extrair_m3u8_real(url_do_site, referer):
    """ Entra no site, pula os frames e pega o link .m3u8 real """
    try:
        session = requests.Session()
        headers = {"User-Agent": UA, "Referer": referer}
        
        # 1. Abre a página do player
        res = session.get(url_do_site, headers=headers, timeout=15)
        content = res.text

        # 2. Tenta achar o link m3u8 (HLS)
        # Procura por padrões como: source: "...", file: "...", ou links diretos
        links = re.findall(r'["\'](https?://[^\s"\']+?\.m3u8[^\s"\']*)["\']', content)
        
        if links:
            # Limpa o link de escapes de barras
            return links[0].replace("\\/", "/")

        # 3. Se não achou, procura por um IFRAME e entra nele (muitos sites escondem o player assim)
        iframe = re.search(r'<iframe.*?src=["\'](https?://.*?)["\']', content)
        if iframe:
            iframe_url = iframe.group(1)
            if "google" not in iframe_url and "ads" not in iframe_url:
                return extrair_m3u8_real(iframe_url, url_do_site)

    except Exception as e:
        print(f"Erro ao buscar sinal: {e}")
    return None

@app.route('/')
def index():
    host = request.host_url
    return render_template_string("""
        <body style="font-family:sans-serif; background:#0f172a; color:white; text-align:center; padding:50px;">
            <h1 style="color:#3b82f6;">Sinal S1 & S2 Ativo</h1>
            <p>Se o canal não abrir, tente novamente em 5 segundos.</p>
            <div style="background:#1e293b; padding:15px; border-radius:8px; border:1px solid #334155; display:inline-block;">
                Link IPTV: <code style="color:#10b981;">{{ host }}playlist.m3u</code>
            </div>
        </body>
    """, host=host)

@app.route('/playlist.m3u')
def playlist():
    """ Gera a playlist M3U """
    base_url = request.host_url.rstrip('/')
    lines = ["#EXTM3U"]

    # --- S1: Sinal Público ---
    try:
        r1 = requests.get("https://apisinalpublico.vercel.app/canais.json", timeout=10)
        for c in r1.json():
            name, logo, target = c.get('name'), c.get('image'), c.get('url')
            # Link via nosso resolvedor
            link = f"{base_url}/stream?s=S1&id={target}"
            lines.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="S1", [S1] {name}\n{link}')
    except: pass

    # --- S2: Minha Tela ---
    try:
        h2 = {"Referer": "https://minhatela.xyz/", "User-Agent": UA}
        r2 = requests.get("https://myapiplay.top/api/guiadejogos/epg.php", headers=h2, timeout=10)
        for c in r2.json():
            if c.get('channelLogo'):
                name, logo = c.get('name'), c.get('logo')
                target = f"https://meuplayeronlinehd.com/myplay/watch.html?id={c.get('channelLogo')}"
                link = f"{base_url}/stream?s=S2&id={target}"
                lines.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="S2", [S2] {name}\n{link}')
    except: pass

    return Response("\n".join(lines), mimetype='text/plain')

@app.route('/stream')
def stream():
    """ 
    Esta é a parte que resolve o erro de formato.
    Nós pegamos o link m3u8 real e redirecionamos o player IPTV com os cabeçalhos corretos.
    """
    source = request.args.get('s')
    target = request.args.get('id')
    
    # Referer necessário para o sinal não bloquear
    ref = "https://sinalpublic.vercel.app/" if source == "S1" else "https://minhatela.xyz/"
    
    # 1. Tenta descobrir o .m3u8 real do momento
    m3u8_url = extrair_m3u8_real(target, ref)
    
    if m3u8_url:
        # 2. Retorna o link com o formato de injeção de header que 90% dos Apps de IPTV usam
        # O sufixo |User-Agent... é o que faz o player IPTV se "disfarçar" de navegador
        final_link = f"{m3u8_url}|User-Agent={UA}&Referer={target}"
        return Response("", status=302, headers={"Location": final_link})
    
    return "Sinal não encontrado ou offline.", 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
