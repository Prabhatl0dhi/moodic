import os
from flask import Flask, redirect, request, jsonify
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()
app = Flask(__name__)
CORS(app)  # 🟢 Enables CORS for all routes

# Load environment variables
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

@app.route("/login")
def login():
    auth_url = "https://accounts.spotify.com/authorize"
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": "user-read-private user-read-email",
    }
    return redirect(f"{auth_url}?{urlencode(params)}")

@app.route("/callback")
def callback():
    code = request.args.get("code")
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    res = requests.post(token_url, data=payload, headers=headers)
    token_data = res.json()
    access_token = token_data.get("access_token")

    if not access_token:
        return jsonify({"error": "Failed to get access token", "details": token_data})

    return redirect(f"https://moodic.vercel.app/mood.html?token={access_token}")

@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.get_json()
    print("Received /recommend POST:", data)

    token = data.get("token")
    moods = data.get("moods")

    if not token or not moods:
        return jsonify({"error": "Missing token or moods"}), 400

    # Placeholder logic for tracks (replace with real logic later)
    dummy_tracks = [
        {
            "name": "Song 1",
            "artist": "Artist A",
            "preview_url": "https://p.scdn.co/mp3-preview/sample1",
            "image": "https://via.placeholder.com/150"
        },
        {
            "name": "Song 2",
            "artist": "Artist B",
            "preview_url": "https://p.scdn.co/mp3-preview/sample2",
            "image": "https://via.placeholder.com/150"
        }
    ]

    return jsonify({"tracks": dummy_tracks})

@app.route("/")
def home():
    return "Moodic backend is running."

if __name__ == "__main__":
    app.run(debug=True)
