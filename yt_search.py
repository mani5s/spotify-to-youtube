from googleapiclient.discovery import build
from time import sleep
import os
from dotenv import load_dotenv

load_dotenv()

def api_client(api_key):
    client = build(serviceName="youtube", version="v3", developerKey=api_key)
    return client

def search_id(song_queries):
    song_ids = []
    client = api_client(os.getenv("yt_api"))
    for query in song_queries:
        request = client.search().list(
            part = "snippet",
            maxResults = 2,
            q = query
        )
        response = request.execute()
        _id = response["items"][0]["id"]["videoId"]
        song_ids.append(_id)
        print(f"Id retrieved for {query}")
        sleep(0.1)
    return song_ids