import os
import requests
from flask import Flask, Response, render_template_string

app = Flask(__name__)

# SERVIDOR OFICIAL EXTRAÍDO DO APP
VELO_SERVER = "http://fastcdn.bond:8080"

# Memória temporária para o código que funcionar (evita re-scan lento a cada clique)
working_cache = {"code": None}

# Lista de credenciais para o Bypass (Master Codes e MAC Spoofing)
BYPASS_LIST = [
    "vWRJvKkPDX", 
    "88888888", 
    "11111111", 
    "00000000", 
    "12345678",
    "00:1A:79:00:00:01"
]

def get_veloplay_list():
    """
    Varre a lista de bypass de forma otimizada para capturar os canais pagos.
    """
    headers = {
        'User-Agent': 'IPTVSmartersPlayer',
        'Accept': '*/*'
    }
    
    # Se já sabemos qual código funciona, tenta ele primeiro para ser instantâneo
    if working_cache["code"]:
        codes_to_try = [working_cache["code"]] + [c for c in BYPASS_LIST if c != working_cache["code"]]
    else:
        codes_to_try = BYPASS_LIST

    for code in codes_to_try:
        # Tenta o formato padrão de ativação (User=Pass)
        url = f"{VELO_SERVER}/get.php?username={code}&password={code}&type=m3u_plus&output=ts"
        try:
            # Timeout curto (4s) para não travar o Railway se o servidor estiver lento
            response = requests.get(url, headers=headers, timeout=4)
            
            if response.status_code == 200 and "#EXTM3U" in response.text:
                working_cache["code"] = code # Memoriza o sucesso
                content = response.text
                
                # Injeta o EPG dinâmico baseado na URL do seu Railway
                domain = os.environ.get("RAILWAY_STATIC_URL", "veloplay-api.up.railway.app")
                if content.startswith("#EXTM3U"):
                    content = content.replace("#EXTM3U", f'#EXTM3U x-tvg-url="https://{domain}/epg.xml"', 1)
                
                return content
        except:
            continue

    return "#EXTM3U\n#ERRO: O servidor oficial não respondeu. Tente novamente em alguns instantes."

@app.route('/')
def index():
    return render_template_string("""
        <body style="background:#000;color:#fff;text-align:center;padding:50px;font-family:sans-serif">
            <h1 style="color:#ffaa00;font-size:2.5em">VeloPlay Cloud Engine</h1>
            <p style="color:#888;margin-bottom:30px">Sincronizando com o servidor fastcdn.bond...</p>
            
            <div style="background:#111;padding:40px;border-radius:20px;display:inline-block;border:1px solid #222">
                <p style="margin-bottom:25px">Sua grade de canais Premium está disponível:</p>
                <a href="/playlist.m3u" style="display:block;background:#ffaa00;color:#000;padding:15px 40px;text-decoration:none;font-weight:bold;border-radius:8px;margin-bottom:15px">GERAR LISTA M3U</a>
                <a href="/epg.xml" style="color:#ffaa00;text-decoration:none;font-size:0.9em">Abrir Guia EPG (XML)</a>
            </div>
            
            <p style="margin-top:50px;font-size:11px;color:#444">Railway Deployment v5.0 - Unlimited Bypass Mode</p>
        </body>
    """)

@app.route('/playlist.m3u')
def playlist():
    return Response(get_veloplay_list(), mimetype='text/plain')

@app.route('/epg.xml')
def epg():
    """
    Puxa o guia de programação (EPG) oficial usando a credencial ativa.
    """
    code = working_cache["code"] or BYPASS_LIST[0]
    epg_url = f"{VELO_SERVER}/xmltv.php?username={code}&password={code}"
    try:
        r = requests.get(epg_url, timeout=10)
        return Response(r.text, mimetype='application/xml')
    except:
        return '<?xml version="1.0" encoding="UTF-8"?><tv></tv>'

if __name__ == '__main__':
    # O Railway gerencia a variável de ambiente PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
