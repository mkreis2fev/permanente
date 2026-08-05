import os
import requests
from flask import Flask, Response, render_template_string

app = Flask(__name__)

# CONFIGURAÇÃO DO SERVIDOR OFICIAL
VELO_SERVER = "http://fastcdn.bond:8080" 

# LISTA DE BYPASS (Códigos Master e credenciais comuns em apps modificados)
# O script testará cada um até encontrar o que libera a grade completa
BYPASS_LIST = [
    "vWRJvKkPDX",      # Seu código atual
    "88888888",        # Master Code 1
    "00000000",        # Master Code 2
    "12345678",        # Master Code 3
    "11111111",        # Master Code 4
    "00:1A:79:00:00:01" # MAC Spoofing genérico
]

def get_veloplay_list():
    """
    Varre a lista de bypass para encontrar uma entrada ativa no servidor fastcdn.bond.
    """
    headers = {
        'User-Agent': 'IPTVSmartersPlayer',
        'Accept': '*/*'
    }
    
    for credential in BYPASS_LIST:
        # Padrão Xtream Codes: Usuário e Senha geralmente são iguais em códigos de ativação
        url = f"{VELO_SERVER}/get.php?username={credential}&password={credential}&type=m3u_plus&output=ts"
        try:
            # Timeout curto para testar a lista rapidamente
            response = requests.get(url, headers=headers, timeout=8)
            
            # Se retornar 200 e começar com #EXTM3U, encontramos a lista!
            if response.status_code == 200 and "#EXTM3U" in response.text:
                content = response.text
                
                # Pega o domínio automático do Railway para o EPG
                domain = os.environ.get("RAILWAY_STATIC_URL", "veloplay-api.up.railway.app")
                
                # Injeta o link do EPG XML no cabeçalho da lista M3U
                if content.startswith("#EXTM3U"):
                    content = content.replace("#EXTM3U", f'#EXTM3U x-tvg-url="https://{domain}/epg.xml"', 1)
                
                return content
        except:
            continue
            
    return "#EXTM3U\n#ERRO: O servidor recusou todos os métodos de bypass. Verifique sua conexão."

@app.route('/')
def index():
    return render_template_string("""
        <body style="background:#000;color:#fff;text-align:center;padding:50px;font-family:sans-serif">
            <h1 style="color:#ffaa00;font-size:2.5em;margin-bottom:10px">VeloPlay Unlimited API</h1>
            <p style="color:#888">Status: <span style="color:#0f0">Bypass Ativo</span></p>
            <hr style="border:0;height:1px;background:#333;margin:30px">
            
            <div style="background:#111;padding:30px;border-radius:15px;display:inline-block;border:1px solid #222">
                <p style="margin-bottom:20px">Sua lista M3U com canais Premium está pronta:</p>
                <a href="/playlist.m3u" style="display:block;background:#ffaa00;color:#000;padding:15px 40px;text-decoration:none;font-weight:bold;border-radius:5px;margin-bottom:10px">ABRIR LISTA M3U</a>
                <a href="/epg.xml" style="color:#ffaa00;text-decoration:none;font-size:0.9em">Guia de Programação (EPG)</a>
            </div>
            
            <p style="margin-top:40px;font-size:12px;color:#444">Railway Cloud Engine v4.0</p>
        </body>
    """)

@app.route('/playlist.m3u')
def playlist():
    return Response(get_veloplay_list(), mimetype='text/plain')

@app.route('/epg.xml')
def epg():
    """
    Puxa o guia de programação (EPG) usando a primeira credencial da lista.
    """
    code = BYPASS_LIST[0]
    epg_url = f"{VELO_SERVER}/xmltv.php?username={code}&password={code}"
    try:
        r = requests.get(epg_url, timeout=20)
        return Response(r.text, mimetype='application/xml')
    except:
        return '<?xml version="1.0" encoding="UTF-8"?><tv></tv>'

if __name__ == '__main__':
    # O Railway define a porta automaticamente
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
