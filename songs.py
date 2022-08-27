import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from dotenv import load_dotenv
import os
import pprint
pp = pprint.PrettyPrinter(indent=4)


scope = os.getenv("scope")

def load_spotify():
    global scope
    load_dotenv()
    SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
    SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
    # spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET))
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
    return sp

def get_playlist():
    playlist_id = "6beAf74Ikpjps9qxCm1Gid"
    sp = load_spotify()
    songs = sp.current_user_playlists(limit=50, offset=0)
    # print(songs)
    print(type(songs))
    playlist = sp.playlist(playlist_id, fields=None, market=None, additional_types=('track', ))
    print("-"*50)
    pp.pprint(playlist)
    print("-"*70)
    tracks = playlist["tracks"]
    for track in tracks:
        print(track["album"]["name"])
        print(track["artist"]["name"])
        print(track["name"])

def get_songs(playlist_id):
    songs = 1



if __name__ == "__main__":
    get_playlist()