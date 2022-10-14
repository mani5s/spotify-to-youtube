from time import sleep
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow


def make_client():
    scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
    client = InstalledAppFlow.from_client_secrets_file(
        "client_secrets_1.json",
        scopes
    )
    credentials = client.run_console()
    youtube = build(serviceName="youtube", version="v3", credentials=credentials)
    return youtube


def make_playlist(playlist_name, youtube):
    print(f"Creating youtube playlist {playlist_name}")
    request = youtube.playlists().insert(
        part="snippet",
        body={
            "snippet": {
                "title": str(playlist_name)
            }
        }
    )
    response = request.execute()
    print(f"{playlist_name} has been created.")
    sleep(0.1)
    return response["id"]


def add_songs(youtube, playlist_id, song_ids):
    temp = []
    for song in song_ids:
        request = youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": song
                    }
                }
            }
        )
        response = request.execute()
        temp.append(response)
        sleep(1)
    return temp
