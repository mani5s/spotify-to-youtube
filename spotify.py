from time import sleep
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from dotenv import load_dotenv
import os

load_dotenv() #loads in environmental varibales to be called in for use
scope = os.getenv("scope")


def all_playlists():
    client = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope)) #connects to spotify api with Oauth. More troublesome need copy paste som link

    playlists = client.current_user_playlists(limit = 50, offset = 0)["items"] #gets data of all the playlist in logged in spotify account 
    playlist_ids = [playlist["id"] for playlist in playlists] #extracts and adds the playlist ids into a list

    return playlist_ids, client

def specific_playlist():
    my_client_id = os.getenv("SPOTIFY_CLIENT_ID")
    my_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    client = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=my_client_id, client_secret=my_client_secret)) #connects to spotify api via Oauth2 easier to connect but limited capabilities

    return client

def get_playlist_name(client,playlist_id):
    try:
        all_info = client.playlist(playlist_id) #all_info is all the raw information you get from spotify
        playlist_name = all_info["name"]
        return playlist_name
    except:
        print("Sorry there is no such playlist ID in spotify")
        return None


def get_songs(client, playlist_id):
    all_info = client.playlist(playlist_id) #all_info is all the raw information you get from spotify
    playlist_name = all_info["name"]
    songs_data = [] #creating a list with playlist name as element 0
    tracks = all_info["tracks"]#gets information of all and only the tracks
    for track in tracks["items"]:
        item = dict.fromkeys(['song_name','artist_name','album_name']) #create a dictionary with stated values as keys and valuesd as NONE
        song = track["track"]
        item["song_name"] = song["name"]
        item["album_name"] = song["album"]["name"]
        item["artist_name"] = song["artists"][0]["name"]
        songs_data.append(item)
    return playlist_name, songs_data

def query(songs_data):
    queries = []
    for song in songs_data:
        song_name = "'" + song["song_name"] + "'"
        artist_name = song["artist_name"]
        queries.append("{} {}".format(song_name, artist_name)) #just constructs a simple string to pass to youtube api
        print("Query for {} created".format(song_name))
        sleep(0.2)
    return queries