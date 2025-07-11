import os
from flask import Flask, redirect, request, jsonify
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# Load environment variables
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")  # Should be your Render backend URL + /callback

# Route to start login with Spotify
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

# Spotify redirect URI callback route
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

    # Step 1: Get access token
    res = requests.post(token_url, data=payload, headers=headers)
    token_data = res.json()
    access_token = token_data.get("access_token")

    if not access_token:
        return jsonify({"error": "Failed to get access token", "details": token_data})

    # Step 2: Redirect to frontend mood page with token
    return redirect(f"https://moodic.vercel.app/mood.html?token={access_token}")

# Recommend songs based on mood
@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.get_json()
    token = data.get("token")
    moods = data.get("moods", [])

    if not token or not moods:
        return jsonify({"error": "Missing token or moods"}), 400

    try:
        all_tracks = []

        for mood in moods:
            q = f"{mood} mood"
            res = requests.get(
                "https://api.spotify.com/v1/search",
                headers={"Authorization": f"Bearer {token}"},
                params={"q": q, "type": "track", "limit": 1}
            )
            res_data = res.json()

            if "tracks" in res_data and res_data["tracks"]["items"]:
                track = res_data["tracks"]["items"][0]
                track_info = {
                    "name": track["name"],
                    "artist": track["artists"][0]["name"],
                    "preview_url": track["preview_url"],
                    "image": track["album"]["images"][0]["url"] if track["album"]["images"] else "",
                }
                all_tracks.append(track_info)

        return jsonify({"tracks": all_tracks})

    except Exception as e:
        return jsonify({"error": "Server error", "message": str(e)}), 500

# Default root route
@app.route("/")
def home():
    return "Moodic backend is running."

if __name__ == "__main__":
    app.run(debug=True)
