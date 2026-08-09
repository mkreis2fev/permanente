import requests
import json
import logging
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def decode_url(obfuscated_url, cr):
    if not obfuscated_url or not obfuscated_url.startswith("@y@") or not cr:
        return obfuscated_url
    
    mapping_orig = " !#$%&()+,-./023456789:;<=>?ABCDEFGHIJKLMNOPQRSTUVWXYZ[^_abcdefghijklmnopqrstuvwxz{}~"
    url = obfuscated_url[3:]
    decoded = ""
    
    for char in url:
        index = cr.find(char)
        if index != -1:
            decoded += mapping_orig[index]
        else:
            decoded += char
            
    return decoded.replace("@yy1111@", "https://").replace("@yy111@", "https://www.").replace("@yy11@", "http://").replace("@yy1@", "http://www.")

def get_channels():
    app_id = "3713506"
    # Servidores possíveis baseados no motor AppCreator24
    servers = [f"srv{i}.e-droid.net" for i in range(11, 20)]
    random.shuffle(servers)
    
    headers = {
        'User-Agent': 'Android Vinebre Software',
        'Accept': '*/*',
        'Connection': 'keep-alive'
    }

    for server in servers:
        config_url = f"https://{server}/srv/config.php?v=228&idapp={app_id}"
        try:
            logger.info(f"==> Analisando Servidor: {server}")
            response = requests.get(config_url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                continue

            # Se a resposta não for JSON, o IP pode estar bloqueado ou redirecionado
            try:
                data = response.json()
            except:
                logger.warning(f"Resposta de {server} não é um JSON válido. Verifique os logs de rede.")
                continue

            cr = data.get("cr", "")
            secciones = data.get("secciones", [])
            
            if isinstance(secciones, dict):
                secciones = list(secciones.values())

            channels = []
            logger.info(f"Capturadas {len(secciones)} seções totais no App.")

            for section in secciones:
                tipo = str(section.get("tipo", ""))
                tit = section.get("tit", "").upper()
                url_raw = section.get("url", "")

                # 1. Busca Canais Diretos (Tipo 6 - Vídeo)
                if tipo == "6" and url_raw:
                    url_dec = decode_url(url_raw, cr)
                    channels.append({"name": section.get("tit", "Canal"), "url": url_dec})
                    logger.info(f"[CANAL] Encontrado: {section.get('tit')}")

                # 2. Busca Canais em Categorias Web (Tipo 1) que contenham links de stream
                elif tipo == "1" and url_raw:
                    if ".m3u8" in url_raw or "stream" in url_raw or "cnd" in url_raw:
                        channels.append({"name": section.get("tit", "Canal Web"), "url": url_raw})
                        logger.info(f"[WEB-STREAM] Encontrado: {section.get('tit')}")

                # 3. Diagnóstico de Menus (Tipo 12)
                elif tipo == "12":
                    logger.info(f"[MENU] Categoria encontrada: {tit}")

            if channels:
                logger.info(f"Sucesso: {len(channels)} canais capturados no total.")
                return channels
            else:
                # Se chegou aqui, ele leu o JSON mas não achou "tipo 6"
                logger.error("JSON lido com sucesso, mas nenhum canal 'tipo 6' foi encontrado dentro dele.")
                # Vamos logar os tipos que ele achou para entender a estrutura
                tipos_achados = set([str(s.get("tipo")) for s in secciones])
                logger.info(f"Tipos de seções presentes neste App: {tipos_achados}")

        except Exception as e:
            logger.error(f"Erro ao conectar com {server}: {str(e)}")
            continue

    return []

if __name__ == "__main__":
    chans = get_channels()
    for c in chans:
        print(f"{c['name']}: {c['url']}")
