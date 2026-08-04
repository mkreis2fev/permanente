import os
import requests
import re
from flask import Flask, Response, render_template_string

app = Flask(__name__)

# URL de exemplo (IPTV-ORG Brasil). Substitua pela sua fonte de captura.
SOURCE_URL = "https://iptv-org.github.io/iptv/countries/br.m3u"

def get_channels():
    """
    Lógica para capturar os canais. 
    Pode ser adaptada para monitorar domínios como fastcdn.bond
    """
    try:
        response = requests.get(SOURCE_URL, timeout=10)
        
        # Exemplo de processamento (remover canais sem HTTPS, etc)
        if response.status_code == 200:
            return response.text
        else:
            return "#EXTM3U\n#ERRO: Servidor de origem offline."
    except Exception as e:
        return f"#EXTM3U\n#ERRO: {str(e)}"

@app.route('/')
def index():
    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Veloplay TV API</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #121212; color: white; }
                .btn { background-color: #ffaa00; color: black; padding: 15px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; }
                .btn:hover { background-color: #e69900; }
            </style>
        </head>
        <body>
            <h1>Veloplay TV - Gerador de M3U</h1>
            <p>Servidor rodando no Railway!</p>
            <br><br>
            <a href="/playlist.m3u" class="btn">Link da Lista M3U</a>
        </body>
        </html>
    """)

@app.route('/playlist.m3u')
def playlist():
    m3u_content = get_channels()
    return Response(m3u_content, mimetype='text/plain', 
                    headers={"Content-Disposition": "attachment;filename=playlist.m3u"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
