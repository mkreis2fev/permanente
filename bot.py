import requests
import re

def decode_url(encoded_url, cad_rep):
    if not encoded_url.startswith("@y@"):
        return encoded_url
    
    orig = " !#$%&()+,-./023456789:;<=>?ABCDEFGHIJKLMNOPQRSTUVWXYZ[^_abcdefghijklmnopqrstuvwxz{}~"
    encoded_url = encoded_url[3:]
    decoded = ""
    for char in encoded_url:
        index = cad_rep.find(char)
        if index != -1:
            decoded += orig[index]
        else:
            decoded += char
    
    decoded = decoded.replace("@yy1111@", "https://")
    decoded = decoded.replace("@yy111@", "https://www.")
    decoded = decoded.replace("@yy11@", "http://")
    decoded = decoded.replace("@yy1@", "http://www.")
    return decoded

def get_channels():
    url = "https://config.e-droid.net/srv/config.php?idapp=3713506&idusu=1&v=228"
    headers = {"User-Agent": "Android Vinebre Software"}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return "Erro ao acessar servidor"

    data = response.text
    # Busca a chave de substituição (cr)
    cad_rep_match = re.search(r'\[cr=(.*?)\]', data)
    cad_rep = cad_rep_match.group(1) if cad_rep_match else ""

    # Encontra todas as seções (s[ID]_tipo=6 são vídeos/canais)
    sections = re.findall(r'\[s(\d+)_tipo=6\]', data)
    
    playlist = "#EXTM3U\n"
    for s_id in sections:
        title = re.search(rf'\[s{s_id}_tit=(.*?)\]', data).group(1)
        stream_url_enc = re.search(rf'\[s{s_id}_url=(.*?)\]', data).group(1)
        
        final_url = decode_url(stream_url_enc, cad_rep)
        if "http" in final_url:
            playlist += f"#EXTINF:-1, {title}\n{final_url}\n"
    
    return playlist

if __name__ == "__main__":
    print(get_channels())
