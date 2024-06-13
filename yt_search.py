from googleapiclient.discovery import build
from time import sleep
import os
from dotenv import load_dotenv

load_dotenv()

def api_client(api_key):
    client = build(serviceName="youtube", version="v3", developerKey=api_key)
    return client

def search_song(song_query):
    client = api_client(os.getenv("yt_api_key"))

    request = client.search().list(
        part = "snippet",
        maxResults = 2,
        q = song_query
    )
    response = request.execute()

    for item in response['items']:
        if item.get('id') and item['id'].get('kind') == 'youtube#video':
            _id = (item['id']['videoId'])

    print(f"Id retrieved for {song_query}")
    return _id