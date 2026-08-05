import os
import requests
from flask import Flask, Response, render_template_string

app = Flask(__name__)

# CONFIGURAÇÃO OFICIAL VELO PLAY
VELO_SERVER = "http://fastcdn.bond:8080" 
CREDENTIAL = "vwrjvkkpdx" # Seu código de acesso

def get_veloplay_list():
    """
    Captura a lista completa de canais (incluindo Premium) 
    direto do servidor fastcdn.bond
    """
    # Usando seu código para Usuário e Senha (padrão Xtream)
    url = f"{VELO_SERVER}/get.php?username={CREDENTIAL}&password={CREDENTIAL}&type=m3u_plus&output=ts"
    
    headers = {
        'User-Agent': 'IPTVSmartersPlayer', # Essencial para o servidor aceitar a conexão
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            content = response.text
            # Adiciona o link do EPG dinâmico do Railway
            domain = os.environ.get("RAILWAY_STATIC_URL", "veloplay-api.up.railway.app")
            if content.startswith("#EXTM3U"):
                content = content.replace("#EXTM3U", f'#EXTM3U x-tvg-url="https://{domain}/epg.xml"', 1)
            return content
        else:
            return f"#EXTM3U\n#ERRO: O servidor do Velo Play negou o acesso (Código {response.status_code}). Verifique se o código expirou."
    except Exception as e:
        return f"#EXTM3U\n#ERRO: Falha de conexão com fastcdn.bond\n#{str(e)}"

@app.route('/')
def index():
    return render_template_string("""
        <body style="background:#000;color:#fff;text-align:center;padding:50px;font-family:sans-serif">
            <h1 style="color:#ffaa00;font-size:2.5em">VeloPlay Private Server</h1>
            <p style="color:#888">Sincronizado com o código: <code style="color:#fff">vwrjvkkpdx</code></p>
            <hr style="border:0;height:1px;background:#333;margin:30px">
            <div style="margin-top:30px">
                <a href="/playlist.m3u" style="display:inline-block;background:#ffaa00;color:#000;padding:15px 40px;text-decoration:none;font-weight:bold;border-radius:5px">GERAR LISTA M3U PREMIUM</a>
            </div>
            <p style="margin-top:20px"><a href="/epg.xml" style="color:#ffaa00;text-decoration:none">Link do EPG (Guia de Programação)</a></p>
        </body>
    """)

@app.route('/playlist.m3u')
def playlist():
    return Response(get_veloplay_list(), mimetype='text/plain')

@app.route('/epg.xml')
def epg():
    # Puxa o Guia de Programação oficial do Velo Play
    epg_url = f"{VELO_SERVER}/xmltv.php?username={CREDENTIAL}&password={CREDENTIAL}"
    try:
        r = requests.get(epg_url, timeout=20)
        return Response(r.text, mimetype='application/xml')
    except:
        return '<?xml version="1.0" encoding="UTF-8"?><tv></tv>'

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
