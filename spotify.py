import os
import requests
import time

from dotenv import load_dotenv

load_dotenv()


class spotify_user:
    def __init__(self, code: str) -> None:
        r = requests.post("https://accounts.spotify.com/api/token",
                          data={"grant_type": "authorization_code",
                                "code": code,
                                "redirect_uri": "http://localhost:8888/callback",
                                "client_id": os.getenv("client_id"),
                                "client_secret": os.getenv("client_secret")})

        self.token_expiry = time.time() + r.json()["expires_in"]
        self.access_token = r.json()["access_token"]
        self.refresh_token = r.json()["refresh_token"]

        r = requests.get("https://api.spotify.com/v1/me",
                         headers={"Authorization": f"Bearer {self.access_token}"})

        self.id = r.json()["id"]

    def refresh(self) -> None:
        r = requests.post("https://accounts.spotify.com/api/token",
                          data={"grant_type": "refresh_token",
                                "refresh_token": self.refresh_token,
                                "client_id": os.getenv("client_id"),
                                "client_secret": os.getenv("client_secret")})

        self.token_expiry = time.time() + r.json()["expires_in"]
        self.access_token = r.json()["access_token"]

    def check_token(self) -> None:
        if time.time() >= self.token_expiry + 10:  # If token is expired or expires within 10 seconds, for network and processing delays.
            self.refresh()

    def get_playlists(self) -> list:
        self.check_token()
        playlists = []
        r = requests.get("https://api.spotify.com/v1/me/playlists",
                         headers={"Authorization": f"Bearer {self.access_token}"})
        playlists += r.json()["items"]
        while r.json()["next"] is not None:
            r = requests.get(r.json()["next"],
                             headers={"Authorization": f"Bearer {self.access_token}"})
            playlists += r.json()["items"]
        return playlists

    def get_playlist_songs(self, playlist_id: str) -> list:
        self.check_token()
        songs = []
        r = requests.get(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
                         headers={"Authorization": f"Bearer {self.access_token}"})
        songs += r.json()["items"]
        while r.json()["next"] is not None:
            r = requests.get(r.json()["next"],
                             headers={"Authorization": f"Bearer {self.access_token}"})
            songs += r.json()["items"]
        return songs
