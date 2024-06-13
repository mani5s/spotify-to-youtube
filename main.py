import multiprocessing
import asyncio
import re
from webbrowser import open
from spotify_auth import run
import spotify
import database
import youtube
import yt_search


def start_spotify_auth_process():
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=run, args=(q,))
    p.start()
    open("http://localhost:6969")
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


async def insert_songs_for_playlist(playlist, user, db):
    await db.insert_spotify_playlists([(playlist["id"], playlist["name"], playlist["description"])])
    p_id = playlist["id"]
    songs = await user.get_playlist_songs(playlist["id"])

    song_data = [(s["track"]["id"], s["track"]["name"]) for s in songs]
    album_data = [(s["track"]["album"]["id"], s["track"]["album"]["name"], s["track"]["album"]["release_date"]) for s in
                  songs]
    artist_data = [(a["id"], a["name"]) for s in songs for a in s["track"]["artists"]]
    song_artist_data = [(s["track"]["id"], a["id"]) for s in songs for a in s["track"]["artists"]]
    song_album_data = [(s["track"]["id"], s["track"]["album"]["id"]) for s in songs]
    playlist_song_data = [(p_id, s["track"]["id"]) for s in songs]

    await db.insert_spotify_songs(song_data)
    await db.insert_spotify_albums(album_data)
    await db.insert_spotify_artists(artist_data)
    await db.insert_spotify_song_artist(song_artist_data)
    await db.insert_spotify_song_album(song_album_data)
    await db.insert_spotify_playlist_songs(playlist_song_data)


async def add_spotify_playlists(user, db):
    playlists = await user.get_playlists()
    confirmed_playlists = confirm_playlists_selection(playlist_selection(playlists), playlists)

    # Create a list of tasks to insert songs for each playlist
    tasks = [insert_songs_for_playlist(playlist, user, db) for playlist in confirmed_playlists]

    # Run tasks concurrently
    await asyncio.gather(*tasks)

    db.spotify_complete()


def youtube_song_search(db):
    print("Starting YT song search")
    songs = db.list_spotify_songs()
    yt_song_search = list(map(lambda song: (
        song[0], yt_search.search_song(f"{song[1]} {' '.join(a for a in db.get_spotify_song_artist(song[0]))}")), songs))
    return yt_song_search


def youtube_transfer():
    pass


async def execute_status_action(status, user, db):
    if status == 1:
        await add_spotify_playlists(user, db)
        # youtube_song_search(db)
    elif status == 2:
        print("Spotify done")
        # youtube_song_search(db)
    elif status == 3:
        print("YT song search completed")
    elif status == 4:
        print("Started YT transfer")
    elif status == 5:
        print("Transfer completed")


def main():
    code = start_spotify_auth_process()
    user = spotify.spotify_user(code)
    db = database.Database(user.id)

    status = db.get_status()
    asyncio.run(execute_status_action(status, user, db))


if __name__ == "__main__":
    main()
