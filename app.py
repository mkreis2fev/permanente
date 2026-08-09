from flask import Flask, Response
from bot import get_channels

app = Flask(__name__)

@app.route('/lista.m3u')
def generate_m3u():
    channels = get_channels()
    m3u_content = "#EXTM3U\n"
    
    for channel in channels:
        m3u_content += f'#EXTINF:-1 tvg-name="{channel["name"]}",{channel["name"]}\n'
        m3u_content += f'{channel["url"]}\n'
        
    return Response(m3u_content, mimetype='audio/x-mpegurl')

@app.route('/')
def home():
    return "Servidor GehTV M3U Ativo. Acesse /lista.m3u"

if __name__ == '__main__':
    # Porta padrão para Railway
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
