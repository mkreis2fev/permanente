from flask import Flask, render_template, redirect, send_from_directory
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/globonews')
def globonews():
    return redirect("https://sinaldvd.github.io/tv/player.html?id=globonews")

# Rota para o App de IPTV encontrar a playlist
@app.route('/playlist.m3u')
def playlist():
    return send_from_directory('static', 'playlist.m3u')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
