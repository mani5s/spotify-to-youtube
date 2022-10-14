import os
import multiprocessing
from subprocess import call
from re import findall
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
playlists = user.get_playlists()


def clear():
    _ = call('clear' if os.name == 'posix' else 'cls')


def print_playlists(playlists):
    for p in playlists:
        print(playlists.index(p), p["name"])


print("\033[4mYour Playlists\033[0m")
print_playlists(playlists)


def playlist_selection(playlists):
    print("Which playlists to transfer? All(a) | Select playlists to include(i) | Select playlists to exclude(e): ")
    s_type = input("Selection: ").lower()
    if s_type == "a":
        print("Selected all playlists")
        return playlists
    elif s_type == "i":
        index = findall("\d", input("Enter index of playlist to include(comma or space seperated): "))
        return [playlists[i] for i in index if 0 <= i < len(index)]
    elif s_type == "e":
        index = findall("\d", input("Enter index of playlist to exclude(comma or space seperated): "))
        return [playlists[i] for i in range(len(playlists)) if i not in index]
    else:
        print("Invalid input")
        playlist_selection()


def edit_selection(p_selection, all_playlists):
    clear()
    i = input("Add(a) or Remove(r) playlists: ").lower()
    if i == "a":
        print_playlists([p for p in all_playlists if p not in p_selection])
        index = findall("\d", input("Enter index of playlist to add(comma or space seperated): "))
        return p_selection + [playlists[i] for i in index if 0 <= i < len(index)]
    elif i == "r":
        print_playlists(p_selection)
        index = findall("\d", input("Enter index of playlist to remove(comma or space seperated): "))
        return [p_selection[i] for i in range(len(p_selection)) if i not in index]
    else:
        print("Invalid input")
        edit_selection(p_selection, all_playlists)


p_selection = playlist_selection(playlists)

while 1:
    clear()
    print("\033[4mSelected Playlists\033[0m")
    print_playlists(p_selection)
    i = input("Confirm(c), Restart Selection(r) or Modify(m): ").lower()
    if i == "c":
        print("Confirmed playlists")
        break
    elif input == "m":
        p_selection = edit_selection(p_selection, playlists)
    else:  # if u entered an invalid option I'm just gonna restart bruh
        p_selection = playlist_selection(playlists)

for p in p_selection:
    database.insert_spotify_playlist(user.id, p["id"], p["name"], p["description"])
