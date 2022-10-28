import multiprocessing
from re import split, fullmatch
from webbrowser import open

from spotify_auth import run
import spotify
import database

q = multiprocessing.Queue()
p = multiprocessing.Process(target=run, args=(q,))
p.start()
open("localhost:8888")
code = q.get(block=True)
p.terminate()

user = spotify.spotify_user(code)
db = database.database(user.id)


def add_spotify_playlists():
    playlists = user.get_playlists()

    def print_playlists(playlists):
        for p in playlists:
            print(playlists.index(p), p["name"])

    print("\033[4mYour Playlists\033[0m")

    def playlist_selection(playlists):
        print_playlists(playlists)
        print("Which playlists to transfer? All(a) | Select playlists to include(i) | Select playlists to exclude(e): ")
        s_type = input("Selection: ").lower()
        if s_type == "a":
            print("Selected all playlists")
            return playlists
        elif s_type == "i":
            index = [int(i) for i in
                     split("\s+|,|\n", input("Enter index of playlist to include(comma or space seperated): ")) if
                     fullmatch("\d+", i)]
            return [playlists[i] for i in index if 0 <= i < len(playlists)]
        elif s_type == "e":
            index = [int(i) for i in
                     split("\s+|,|\n", input("Enter index of playlist to exclude(comma or space seperated): ")) if
                     fullmatch("\d+", i)]
            return [playlists[i] for i in range(len(playlists)) if i not in index]
        else:
            print("Invalid input")
            playlist_selection(playlists)

    def edit_selection(p_selection, all_playlists):
        i = input("Add(a) or Remove(r) playlists: ").lower()
        if i == "a":
            add_playlists = [p for p in all_playlists if p not in p_selection]
            print_playlists(add_playlists)
            index = [int(i) for i in
                     split("\s+|,|\n", input("Enter index of playlist to add(comma or space seperated): ")) if
                     fullmatch("\d+", i)]
            return p_selection + [add_playlists[i] for i in index if 0 <= i < len(add_playlists)]
        elif i == "r":
            print_playlists(p_selection)
            index = [int(i) for i in
                     split("\s+|,|\n", input("Enter index of playlist to remove(comma or space seperated): ")) if
                     fullmatch("\d+", i)]
            return [p_selection[i] for i in range(len(p_selection)) if i not in index]
        else:
            print("Invalid input")
            edit_selection(p_selection, all_playlists)

    p_selection = playlist_selection(playlists)

    while 1:
        print("\033[4mSelected Playlists\033[0m")
        print_playlists(p_selection)
        i = input("Confirm(c), Restart Selection(r) or Modify(m): ").lower()
        if i == "c":
            print("Confirmed playlists")
            break
        elif i == "m":
            p_selection = edit_selection(p_selection, playlists)
        else:  # if u entered an invalid option I'm just gonna restart bruh
            p_selection = playlist_selection(playlists)

    for p in p_selection:
        p_id = db.insert_spotify_playlist(user.id, p["id"], p["name"], p["description"])
        songs = user.get_playlist_songs(p["id"])
        for s in songs:
            song_id = db.insert_spotify_song(user.id, (s["track"]["id"], s["track"]["name"]))
            album_id = db.insert_spotify_album(user.id, (
                s["track"]["album"]["id"], s["track"]["album"]["name"], s["track"]["album"]["release_date"]))
            artist_ids = db.insert_spotify_artists(user.id, [(a["id"], a["name"]) for a in s["track"]["artists"]])
            db.insert_spotify_song_album(user.id, song_id, album_id)
            db.insert_spotify_song_artist(user.id, song_id, artist_ids)
        db.insert_spotify_playlist_songs(user.id, [(p_id, s["track"]["id"]) for s in songs])

    db.spotify_complete(user.id)


def youtube_song_search():
    print("Starting YT song search")


def youtube_transfer():
    pass


status = db.get_status()
if status == 1:
    add_spotify_playlists()
elif status == 2:
    print("Spotify done")
    youtube_song_search()
elif status == 3:
    print("YT song search completed")
    youtube_transfer()
elif status == 4:
    print("Started YT transfer")
elif status == 5:
    print("Transfer completed")
