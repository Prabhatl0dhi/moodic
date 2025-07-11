import os
from flask import Flask, redirect, request, jsonify
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# Load env variables
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")  # should be: https://moodic-backend.onrender.com/callback

# Login route
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

# Callback route
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

    # Get token
    res = requests.post(token_url, data=payload, headers=headers)
    token_data = res.json()
    access_token = token_data.get("access_token")

    if not access_token:
        return jsonify({"error": "Failed to get access token", "details": token_data})

    # Redirect to mood.html with token
    return redirect(f"https://moodic.vercel.app/mood.html?token={access_token}")

# Recommend route
@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.get_json()
    token = data.get("token")
    moods = data.get("moods")

    if not token or not moods:
        return jsonify({"error": "Missing token or moods"}), 400

    # Mood to genre mapping
    mood_to_genre = {
        "happy": "pop",
        "sad": "acoustic",
        "romantic": "romance",
        "energetic": "work-out",
        "calm": "chill",
        "party": "party"
    }

    genres = [mood_to_genre.get(m.lower()) for m in moods if mood_to_genre.get(m.lower())]
    if not genres:
        return jsonify({"error": "No matching genres for moods"}), 400

    genre_param = ",".join(genres[:5])  # max 5 genres
    endpoint = f"https://api.spotify.com/v1/recommendations?seed_genres={genre_param}&limit=10"

    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(endpoint, headers=headers)

    if res.status_code != 200:
        return jsonify({"error": "Failed to fetch from Spotify", "details": res.json()}), 500

    data = res.json()
    tracks = []
    for track in data["tracks"]:
        tracks.append({
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "image": track["album"]["images"][0]["url"] if track["album"]["images"] else "",
            "preview_url": track["preview_url"]
        })

    return jsonify({"tracks": tracks})

# Fallback route
@app.route("/")
def home():
    return "🎧 Moodic backend is live!"

if __name__ == "__main__":
    app.run(debug=True)
