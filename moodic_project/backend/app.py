import os
from flask import Flask, redirect, request, jsonify
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv
from flask_cors import CORS
import traceback

load_dotenv()
app = Flask(__name__)
CORS(app)

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

@app.route("/")
def home():
    return "Moodic backend is running (Playlist version)."

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
    try:
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

    except Exception as e:
        print("Callback error:", e)
        traceback.print_exc()
        return jsonify({"error": "Callback exception", "details": str(e)}), 500

@app.route("/recommend", methods=["POST"])
def recommend_playlists():
    try:
        data = request.get_json()
        token = data.get("token")
        moods = data.get("moods", [])
        language = data.get("language", "english").lower()

        if not token or not moods:
            return jsonify({"error": "Missing token or moods"}), 400

        query = f"{' '.join(moods)} {language} playlist"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        params = {
            "q": query,
            "type": "playlist",
            "limit": 10
        }

        res = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params)

        if res.status_code != 200:
            print("Spotify API error:", res.text)
            return jsonify({"error": "Spotify API error", "details": res.text}), 502

        playlists = []
        items = res.json().get("playlists", {}).get("items", [])
        for item in items:
            playlists.append({
                "name": item["name"],
                "image": item["images"][0]["url"] if item["images"] else "",
                "spotify_url": item["external_urls"]["spotify"],
                "owner": item["owner"]["display_name"]
            })

        return jsonify({"playlists": playlists})

    except Exception as e:
        print("Recommendation error:", e)
        traceback.print_exc()
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
