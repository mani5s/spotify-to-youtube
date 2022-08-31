from sys import argv
from time import sleep
from sqlite3 import *
from spotify import all_playlists, specific_playlist, get_songs, query, get_playlist_name
from yt_search import api_client, search_id
from playlist_insert import make_playlist, add_songs, make_client
import setup as s
from os.path import exists

def prep():
    status = s.setup()
    if status:
        if not exists("client_secrets.json"):
            print("""Please ensure you have installed and re-located and renamed your google client secrets file.
            Refer to README for instructions""")
            exit()
    else:
        exit()
    return 

def make_main_db():
    db = connect("SPOTOYT.db") #creating a database to store data to remove possible redundancies
    c = db.cursor()
    c.execute("""CREATE TABLE 'Main'(
    '_ID' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
    'PlaylistName' TEXT NOT NULL,
    'YTID' TEXT UNIQUE,
    'SPID' TEXT NOT NULL UNIQUE
    )""") #creating a main table to link both yt and spotify data for easy access
    c.execute("""CREATE TABLE 'Queries'(
    '_ID' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    'SongName'  TEXT NOT NULL UNIQUE,
    'Query' TEXT NOT NULL UNIQUE
    )""") #create a table of songs to prevent repeated searching in yt. Can be identified with query
    db.commit()
    db.close()

def make_playlist_db(playlist_name, YTID, SPID):
    db = connect("SPOTOYT.db")
    c = db.cursor()
    c.execute("""INSERT INTO 'Main'(
        'PlaylistName',
        'YTID',
        'SPID')
        VALUES(?,?,?)
    """, (playlist_name, YTID, SPID))#inserting into main table the playlist ids and name of current playlist
    _id = c.execute("SELECT _ID FROM 'Main' WHERE SPID = ?", (SPID,)).fetchone()
    c.execute("""CREATE TABLE '{}'(
        'Song_id' TEXT NOT NULL UNIQUE,
        PRIMARY KEY('Song_id'),
        FOREIGN KEY('Song_id') REFERENCES 'Queries'('_ID')
    )""".format(_id[0])) #Make a table with song_ids of songs in playlist
    db.commit()
    db.close()
    return _id
