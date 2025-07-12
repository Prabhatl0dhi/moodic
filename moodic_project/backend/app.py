import os
from flask import Flask, redirect, request, jsonify
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()
app = Flask(__name__)
CORS(app)

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

# Mood to audio feature map
mood_audio_map = {
    "Happy": {"min_valence": 0.7, "min_energy": 0.6},
    "Sad": {"max_valence": 0.4, "max_energy": 0.5},
    "Energetic": {"min_energy": 0.8},
    "Romantic": {"min_valence": 0.6, "max_energy": 0.6},
    "Chill": {"max_energy": 0.4, "min_valence": 0.4, "max_valence": 0.7},
    "Angry": {"min_energy": 0.8, "max_valence": 0.3},
    "Motivated": {"min_energy": 0.7, "min_valence": 0.6},
    "Nostalgic": {"max_valence": 0.5, "min_acousticness": 0.3}
}

# Basic language → market mapping
language_market_map = {
    "english": "US",
    "hindi": "IN",
    "punjabi": "IN",
    "bengali": "IN",
    "telugu": "IN",
    "tamil": "IN",
    "kannada": "IN"
}

@app.route("/")
def home():
    return "Moodic backend is running."

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
    token = data.get("token")
    moods = data.get("moods", [])
    language = data.get("language", "english").lower()

    if not token or not moods:
        return jsonify({"error": "Missing token or moods"}), 400

    headers = {
        "Authorization": f"Bearer {token}"
    }

    market = language_market_map.get(language, "US")

    # Combine audio filters from all moods
    audio_features = {}
    for mood in moods:
        filters = mood_audio_map.get(mood.capitalize())
        if filters:
            for key, value in filters.items():
                if key.startswith("min_"):
                    audio_features[key] = max(audio_features.get(key, 0), value)
                elif key.startswith("max_"):
                    audio_features[key] = min(audio_features.get(key, 1), value)

    seed_genres = "pop"

    params = {
        "limit": 30,
        "market": market,
        "seed_genres": seed_genres,
        **audio_features
    }

    res = requests.get("https://api.spotify.com/v1/recommendations", headers=headers, params=params)

    if res.status_code != 200:
        print("Spotify API error:", res.text)
        return jsonify({"error": "Spotify API error", "details": res.text})

    tracks = []
    for item in res.json().get("tracks", []):
        if item["preview_url"]:  # only include playable tracks
            tracks.append({
                "name": item["name"],
                "artist": item["artists"][0]["name"],
                "preview_url": item["preview_url"],
                "image": item["album"]["images"][0]["url"] if item["album"]["images"] else ""
            })

    return jsonify({"tracks": tracks[:20]})  # return only 20 at max

if __name__ == "__main__":
    app.run(debug=True)
