import os
import logging
from flask import Flask, Response, jsonify
from bot import get_channels

# Configuração de logs para capturar erros no Railway
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def index():
    """Página inicial para verificar se o servidor está vivo."""
    return jsonify({
        "status": "online",
        "message": "Servidor GehTV M3U ativo",
        "endpoints": {
            "m3u": "/lista.m3u",
            "json_debug": "/canais.json"
        }
    })

@app.route('/lista.m3u')
def generate_m3u():
    """Gera a lista M3U para players de IPTV."""
    try:
        logger.info("Iniciando geração de lista M3U...")
        channels = get_channels()
        
        if not channels:
            logger.error("Nenhum canal foi capturado.")
            return "Erro: O servidor não conseguiu capturar os canais. Verifique os logs do bot.", 503

        m3u_content = "#EXTM3U\n"
        for channel in channels:
            name = channel["name"]
            url = channel["url"]
            # Formato padrão M3U
            m3u_content += f'#EXTINF:-1 tvg-name="{name}" group-title="GehTV",{name}\n'
            m3u_content += f'{url}\n'
            
        logger.info(f"M3U gerado com {len(channels)} canais.")
        return Response(m3u_content, mimetype='audio/x-mpegurl')

    except Exception as e:
        logger.error(f"Erro crítico na rota M3U: {str(e)}")
        return f"Internal Server Error: {str(e)}", 500

@app.route('/canais.json')
def generate_json():
    """Retorna os canais em JSON (útil para testar no navegador)."""
    try:
        channels = get_channels()
        return jsonify({
            "total": len(channels),
            "canais": channels
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # O Railway usa a variável de ambiente PORT
    port = int(os.environ.get("PORT", 5000))
    # Host 0.0.0.0 é obrigatório para deploy externo
    app.run(host='0.0.0.0', port=port)
