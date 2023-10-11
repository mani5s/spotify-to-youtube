import multiprocessing
import re
from webbrowser import open
from spotify_auth import run
import spotify
import database
#import youtube


def start_spotify_auth_process():
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=run, args=(q,))
    p.start()
    open("localhost:6969")
    code = q.get(block=True)
    p.terminate()
    return code


def get_playlist_indices(prompt):
    return [int(i) for i in re.split("\s+|,|\n", input(prompt)) if re.fullmatch("\d+", i)]


def print_playlists(playlists):
    for index, playlist in enumerate(playlists):
        print(index, playlist["name"])


def playlist_selection(playlists):
    print("\033[4mYour Playlists\033[0m")
    print_playlists(playlists)

    selection_type = input(
        "Which playlists to transfer? All(a) | Select to include(i) | Select to exclude(e): ").lower()

    if selection_type == "a":
        return playlists

    elif selection_type in ("i", "e"):
        action = "include" if selection_type == "i" else "exclude"
        indices = get_playlist_indices(f"Enter index of playlist to {action}(comma or space separated): ")

        if selection_type == "i":
            return [playlists[i] for i in indices if 0 <= i < len(playlists)]
        else:
            return [playlist for i, playlist in enumerate(playlists) if i not in indices]

    else:
        print("Invalid input")
        return playlist_selection(playlists)


def edit_selected_playlists(selected_playlists, all_playlists):
    action = input("Add(a) or Remove(r) playlists: ").lower()

    if action == "a":
        available_playlists = [p for p in all_playlists if p not in selected_playlists]
        print_playlists(available_playlists)
        indices = get_playlist_indices("Enter index of playlist to add(comma or space separated): ")
        return selected_playlists + [available_playlists[i] for i in indices if 0 <= i < len(available_playlists)]

    elif action == "r":
        print_playlists(selected_playlists)
        indices = get_playlist_indices("Enter index of playlist to remove(comma or space separated): ")
        return [playlist for i, playlist in enumerate(selected_playlists) if i not in indices]

    else:
        print("Invalid input")
        return edit_selected_playlists(selected_playlists, all_playlists)


def confirm_playlists_selection(selected_playlists, all_playlists):
    while True:
        print("\033[4mSelected Playlists\033[0m")
        print_playlists(selected_playlists)
        option = input("Confirm(c), Restart Selection(r) or Modify(m): ").lower()

        if option == "c":
            print("Confirmed playlists")
            return selected_playlists

        elif option == "m":
            selected_playlists = edit_selected_playlists(selected_playlists, all_playlists)

        else:
            selected_playlists = playlist_selection(all_playlists)


def add_spotify_playlists(user, db):
    playlists = user.get_playlists()
    confirmed_playlists = confirm_playlists_selection(playlist_selection(playlists), playlists)

    for playlist in confirmed_playlists:
        p_id = db.insert_spotify_playlist(playlist["id"], playlist["name"], playlist["description"])
        songs = user.get_playlist_songs(playlist["id"])

        for song in songs:
            song_id = db.insert_spotify_song((song["track"]["id"], song["track"]["name"]))
            album_id = db.insert_spotify_album(
                (song["track"]["album"]["id"], song["track"]["album"]["name"], song["track"]["album"]["release_date"]))
            artist_ids = db.insert_spotify_artists([(a["id"], a["name"]) for a in song["track"]["artists"]])
            db.insert_spotify_song_album(song_id, album_id)
            db.insert_spotify_song_artist(song_id, artist_ids)

        db.insert_spotify_playlist_songs([(p_id, s["track"]["id"]) for s in songs])

    db.spotify_complete()


def youtube_song_search(db):
    print("Starting YT song search")
    songs = db.list_spotify_songs()
    yt_song_search = list(map(lambda song: (
    song[0], youtube.search_song(f"{song[1]} {' '.join(a for a in db.get_spotify_song_artist(song[0]))}")), songs))
    return yt_song_search


def youtube_transfer():
    pass


def main():
    code = start_spotify_auth_process()
    user = spotify.spotify_user(code)
    db = database.database(user.id)

    status_actions = {
        1: lambda: (add_spotify_playlists(user, db), youtube_song_search(db)),
        2: lambda: print("Spotify done"),
        3: lambda: print("YT song search completed"),
        4: lambda: print("Started YT transfer"),
        5: lambda: print("Transfer completed")
    }

    status = db.get_status()
    if status in status_actions:
        status_actions[status]()


if __name__ == "__main__":
    main()
