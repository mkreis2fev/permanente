import os
import logging
from flask import Flask, Response, jsonify
from bot import get_channels

# Configuração de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        "status": "online",
        "message": "Servidor GehTV ativo",
        "m3u_url": "/lista.m3u"
    })

@app.route('/lista.m3u')
def generate_m3u():
    try:
        logger.info("Solicitação de M3U recebida.")
        channels = get_channels()
        
        if not channels:
            logger.error("bot.py retornou lista vazia.")
            return "Erro: O bot nao encontrou canais. Verifique os logs no Railway.", 503

        # Construção da lista M3U
        m3u_content = "#EXTM3U\n"
        for channel in channels:
            name = channel["name"]
            url = channel["url"]
            m3u_content += f'#EXTINF:-1 tvg-name="{name}" group-title="GehTV",{name}\n'
            m3u_content += f'{url}\n'
            
        # Retorna com o cabeçalho correto para IPTV
        return Response(m3u_content, mimetype='application/x-mpegURL')

    except Exception as e:
        logger.error(f"Erro na rota: {str(e)}")
        return "Erro interno no servidor.", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
