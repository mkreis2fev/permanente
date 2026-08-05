import os
import requests
from flask import Flask, Response, render_template_string

app = Flask(__name__)

# --- CONFIGURAÇÕES ---

# Credencial exata fornecida
CREDENTIAL = "vWRJvKkPDX"

# Servidores Oficiais do Velo Play (Extraídos do seu projeto)
PRIVATE_SERVERS = [
    "http://fastcdn.bond:8080", 
    "http://vodcast.sbs:8080",
    "http://fastcdn.bond"
]

# Fontes Públicas de Segurança (Caso o Velo Play bloqueie a conexão do servidor)
PUBLIC_SOURCES = [
    "https://raw.githubusercontent.com/Fmacedo87/m3u/main/Canais.m3u",
    "https://iptv-org.github.io/iptv/countries/br.m3u"
]

# Link do EPG (Guia de Programação)
EPG_SOURCE = "https://iptv-org.github.io/epg/guides/br/mi.tv.epg.xml"

# --- LÓGICA DE CAPTURA ---

def get_combined_list():
    """
    Tenta capturar do Velo Play primeiro. Se falhar, usa fontes públicas.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; TV Box Build/QP1A.190711.020)',
        'Accept': '*/*'
    }
    
    # 1. TENTA FONTES PRIVADAS (Velo Play)
    for base in PRIVATE_SERVERS:
        url = f"{base}/get.php?username={CREDENTIAL}&password={CREDENTIAL}&type=m3u_plus&output=ts"
        try:
            # Timeout curto de 4s para evitar que o Railway derrube a aplicação
            response = requests.get(url, headers=headers, timeout=4)
            if response.status_code == 200 and "#EXTM3U" in response.text:
                content = response.text
                # Injeta o link do seu EPG do Railway no topo da lista
                domain = os.environ.get("RAILWAY_STATIC_URL", "veloplay-api.up.railway.app")
                if content.startswith("#EXTM3U"):
                    content = content.replace("#EXTM3U", f'#EXTM3U x-tvg-url="https://{domain}/epg.xml"', 1)
                return content
        except:
            continue

    # 2. TENTA FONTES PÚBLICAS (Fallback)
    combined_m3u = "#EXTM3U\n# MODO FALLBACK ATIVO: Servidor VeloPlay Ocupado\n"
    for url in PUBLIC_SOURCES:
        try:
            response = requests.get(url, headers=headers, timeout=8)
            if response.status_code == 200:
                lines = response.text.splitlines()
                for line in lines:
                    if not line.startswith("#EXTM3U"):
                        combined_m3u += line + "\n"
        except:
            continue
            
    return combined_m3u

# --- ROTAS DO SERVIDOR ---

@app.route('/')
def index():
    return render_template_string("""
        <body style="background:#000;color:#fff;text-align:center;padding:50px;font-family:sans-serif">
            <h1 style="color:#ffaa00;font-size:2.5em">VeloPlay Multi-Source API</h1>
            <p style="color:#888">Sincronizando Canais Premium e Guia EPG</p>
            <hr style="border:0;height:1px;background:#333;margin:30px">
            
            <div style="background:#111;padding:30px;border-radius:15px;display:inline-block;border:1px solid #222">
                <p style="margin-bottom:20px;color:#0f0">Status: Conectado</p>
                <a href="/playlist.m3u" style="display:block;background:#ffaa00;color:#000;padding:15px 40px;text-decoration:none;font-weight:bold;border-radius:5px;margin-bottom:15px">LINK DA LISTA M3U</a>
                <a href="/epg.xml" style="color:#ffaa00;text-decoration:none;font-size:0.9em">Abrir Guia de Programação (XML)</a>
            </div>
            
            <p style="margin-top:40px;font-size:12px;color:#444">Railway Engine v6.0 - Unlimited Mode</p>
        </body>
    """)

@app.route('/playlist.m3u')
def playlist():
    return Response(get_combined_list(), mimetype='text/plain')

@app.route('/epg.xml')
def epg():
    try:
        r = requests.get(EPG_SOURCE, timeout=15)
        return Response(r.text, mimetype='application/xml')
    except:
        return '<?xml version="1.0" encoding="UTF-8"?><tv></tv>'

if __name__ == '__main__':
    # Railway configura a porta automaticamente
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
