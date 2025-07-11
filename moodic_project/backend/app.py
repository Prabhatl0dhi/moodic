import os
from flask import Flask, redirect, request, jsonify
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# Environment variables
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")  # Should match Spotify app settings

# Mood to genre mapping
MOOD_TO_GENRES = {
    "Happy": ["pop", "dance"],
    "Sad": ["acoustic", "piano"],
    "Energetic": ["work-out", "electronic"],
    "Romantic": ["romance", "r-n-b"],
    "Chill": ["chill", "lo-fi"],
    "Angry": ["metal", "punk"],
    "Motivated": ["hip-hop", "power-pop"],
    "Nostalgic": ["classic-rock", "old-school"]
}

@app.route("/")
def home():
    return "Moodic backend is running 🎶"

# Spotify login redirect
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

# Spotify callback
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

    # Step 1: Get token
    res = requests.post(token_url, data=payload, headers=headers)
    token_data = res.json()
    access_token = token_data.get("access_token")

    if not access_token:
        return jsonify({"error": "Failed to get access token", "details": token_data})

    # Step 2: Redirect to mood page with token
    return redirect(f"https://moodic.vercel.app/mood.html?token={access_token}")

# Recommend songs based on moods
@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.get_json()
    token = data.get("token")
    moods = data.get("moods", [])

    if not token or not moods:
        return jsonify({"error": "Missing token or moods"}), 400

    # Combine genres
    seed_genres = []
    for mood in moods:
        genres = MOOD_TO_GENRES.get(mood, [])
        seed_genres.extend(genres)

    # Unique and max 5 genres
    seed_genres = list(set(seed_genres))[:5]

    rec_url = "https://api.spotify.com/v1/recommendations"
    params = {
        "seed_genres": ",".join(seed_genres),
        "limit": 10,
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }

    res = requests.get(rec_url, headers=headers, params=params)
    if res.status_code != 200:
        return jsonify({"error": "Failed to fetch recommendations", "details": res.json()}), res.status_code

    tracks_data = res.json().get("tracks", [])
    tracks = []
    for track in tracks_data:
        track_info = {
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "image": track["album"]["images"][0]["url"] if track["album"]["images"] else "",
            "preview_url": track["preview_url"]  # May be None
        }
        tracks.append(track_info)

    return jsonify({"tracks": tracks})

if __name__ == "__main__":
    app.run(debug=True)
