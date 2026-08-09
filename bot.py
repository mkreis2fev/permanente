import requests
import json
import logging
import random

# Configuração de logs para você ver no painel do Railway
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
            
    # Correção de protocolos
    decoded = decoded.replace("@yy1111@", "https://").replace("@yy111@", "https://www.").replace("@yy11@", "http://").replace("@yy1@", "http://www.")
    return decoded

def get_channels():
    app_id = "3713506"
    # Servidores do AppCreator24 capturados do Smali
    servers = [f"srv{i}.e-droid.net" for i in range(11, 20)]
    random.shuffle(servers)
    
    headers = {
        'User-Agent': 'Android Vinebre Software',
        'Accept': '*/*',
        'Connection': 'keep-alive'
    }

    for server in servers:
        # Usando a versão v=260 que é a mais estável para submenus
        config_url = f"https://{server}/srv/config.php?v=260&idapp={app_id}"
        try:
            logger.info(f"==> Tentando capturar de: {server}")
            response = requests.get(config_url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                continue

            data = response.json()
            cr = data.get("cr", "")
            secciones = data.get("secciones", [])
            
            if isinstance(secciones, dict):
                secciones = list(secciones.values())

            all_channels = []

            # Função interna para vasculhar itens aninhados (Categorias dentro de Categorias)
            def scan_recursive(items):
                found = []
                if not items: return found
                
                # Garante que items seja uma lista
                if isinstance(items, dict): items = items.values()

                for item in items:
                    tipo = str(item.get("tipo", ""))
                    tit = item.get("tit", "Canal")
                    url_raw = item.get("url", "")

                    # Se for tipo 6 (Vídeo), é um canal
                    if tipo == "6" and url_raw:
                        found.append({
                            "name": tit,
                            "url": decode_url(url_raw, cr)
                        })
                        logger.info(f"Canal encontrado: {tit}")

                    # Se tiver sub-itens (submenu), vasculha dentro deles
                    # Campos comuns no AppCreator24 para sub-itens:
                    for sub_key in ["submenu_items", "atribs", "items"]:
                        if sub_key in item:
                            found.extend(scan_recursive(item[sub_key]))
                return found

            # Inicia a busca em todas as seções do app
            all_channels = scan_recursive(secciones)

            if all_channels:
                logger.info(f"Sucesso: {len(all_channels)} canais capturados no total.")
                return all_channels
            else:
                logger.warning(f"Nenhum canal tipo 6 encontrado no servidor {server}.")

        except Exception as e:
            logger.error(f"Erro no servidor {server}: {str(e)}")
            continue

    return []

if __name__ == "__main__":
    # Teste local
    print(get_channels())
