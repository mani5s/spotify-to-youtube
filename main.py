from sys import argv
from time import sleep
from spotify import all_playlists, specific_playlist, get_songs, query, get_playlist_name
from yt_search import api_client, search_id
from playlist_insert import make_playlist, add_songs, make_client
import setup as s
from os.path import exists



def setup():
    setup_status = s.setup()
    if setup_status == False: pass 
    if not exists("client_secrets.json"):
        print("""You have not yet downloaded or renamed your youtube client secrets/
        Please ensure you have downloaded renamed and moved into this folder before re-running this Program.""")


def main(spotify_client, spotify_playlist):
    playlist_name, song_data = get_songs(spotify_client, spotify_playlist)
    print(f"exporting songs from {playlist_name}")
    sleep(0.4)
    queries = query(song_data)
    print(f"aquiring song id for songs in {playlist_name}")
    yt_song_ids = search_id(queries)
    youtube_client = make_client()
    yt_playlist_id = make_playlist(playlist_name, youtube_client)
    print(f"adding songs to {playlist_name}")
    add = add_songs(youtube_client, yt_playlist_id, yt_song_ids)
    print(f"Shout out. {playlist_name} should be complete. Please check")
    sleep(0.6)
    return add




def main_all():
    spotify_playlists, spotify_client = all_playlists()
    count = 0
    for spotify_playlist in spotify_playlists:
        main(spotify_client, spotify_playlist)

def main_specific():
    knows = input("Do you know your playlist id? (yes/no)").lower()
    if knows == "yes":
        spotify_playlist = input("Enter your playlist id here: ")
        spotify_client = specific_playlist()
        print("Searching for playlist...",)
        sleep(0.1)
        correct = "no"
        playlist_name = get_playlist_name(spotify_client, spotify_playlist)
        if playlist_name == None: return 
        correct = input(f"Is '{playlist_name}' the playlist you are looking for? (yes/no) ")
        if correct.lower() == "yes": main(spotify_client, spotify_playlist)
        if correct.lower() == "no": print("Playlist Not Found")


    else:
        user_playlist_name = input("Enter your playlist name: ")
        spotify_playlists, spotify_client = all_playlists()
        for spotify_playlist in spotify_playlists:
            print("Searching for playlist...",)
            sleep(0.1)
            correct = "no"
            playlist_name= get_playlist_name(spotify_client, spotify_playlist)
            if playlist_name.lower() ==  user_playlist_name:
                correct = input(f"Is {playlist_name} the playlist you are looking for? (yes/no) ")
                if correct.lower() == "yes": break
        if correct.lower() == "no": print("Playlist Not Found")
    # main(spotify_client, spotify_playlist)





if __name__ == "__main__":
    if not exists("setup_done.txt"):
        setup()
    else:
        if len(argv) > 1 and argv[1] == "--a":
            main_all()
        else:
            main_specific()