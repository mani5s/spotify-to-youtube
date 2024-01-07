import os
import time
import httpx
from dotenv import load_dotenv

load_dotenv()


class spotify_user:
    def __init__(self, code: str) -> None:
        r = httpx.post("https://accounts.spotify.com/api/token",
                       data={"grant_type": "authorization_code",
                             "code": code,
                             "redirect_uri": "http://localhost:6969/callback",
                             "client_id": os.getenv("client_id"),
                             "client_secret": os.getenv("client_secret")})
        self.token_expiry = time.time() + r.json()["expires_in"]
        self.access_token = r.json()["access_token"]
        self.refresh_token = r.json()["refresh_token"]

        r = httpx.get("https://api.spotify.com/v1/me", headers={"Authorization": f"Bearer {self.access_token}"})
        self.id = r.json()["id"]

    async def async_fetch(self, url: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers={"Authorization": f"Bearer {self.access_token}"})
            return response.json()

    async def get_all_pages(self, initial_url: str) -> list:
        results = []
        next_url = initial_url

        while next_url:
            response = await self.async_fetch(next_url)
            results.extend(response["items"])
            next_url = response["next"]

        return results

    async def get_playlists(self) -> list:
        return await self.get_all_pages("https://api.spotify.com/v1/me/playlists")

    async def get_playlist_songs(self, playlist_id: str) -> list:
        return await self.get_all_pages(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks")

    def check_token(self) -> None:
        if time.time() >= self.token_expiry:
            self.refresh()
