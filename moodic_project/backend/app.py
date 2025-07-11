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

# Mood to genre mapping
MOOD_GENRE_MAP = {
    "Happy": ["pop", "dance", "party"],
    "Sad": ["acoustic", "piano", "sad"],
    "Energetic": ["work-out", "edm", "electronic"],
    "Romantic": ["romance", "r-n-b", "soul"],
    "Chill": ["chill", "ambient", "lo-fi"],
    "Angry": ["metal", "punk", "hard-rock"],
    "Motivated": ["motivational", "pop", "hip-hop"],
    "Nostalgic": ["old-school", "classical", "retro"]
}

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
    language = data.get("language", "english")

    if not token or not moods:
        return jsonify({"error": "Missing token or moods"}), 400

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Compile genres from selected moods
    genres = set()
    for mood in moods:
        genres.update(MOOD_GENRE_MAP.get(mood, []))

    if not genres:
        return jsonify({"tracks": []})

    genre_string = ",".join(list(genres)[:5])  # Max 5 seed genres

    # Get recommendations from Spotify
    params = {
        "seed_genres": genre_string,
        "limit": 20,
        "market": "IN",
        "min_popularity": 50
    }

    res = requests.get("https://api.spotify.com/v1/recommendations", headers=headers, params=params)

    if res.status_code != 200:
        print("Spotify API error:", res.text)
        return jsonify({"error": "Failed to fetch recommendations"})

    items = res.json().get("tracks", [])
    tracks = []

    for item in items:
        if not item.get("preview_url"):
            continue  # Skip if no preview

        track = {
            "name": item["name"],
            "artist": item["artists"][0]["name"],
            "preview_url": item["preview_url"],
            "image": item["album"]["images"][0]["url"] if item["album"]["images"] else ""
        }
        tracks.append(track)

    return jsonify({"tracks": tracks})

@app.route("/")
def home():
    return "Moodic backend is running."

if __name__ == "__main__":
    app.run(debug=True)
