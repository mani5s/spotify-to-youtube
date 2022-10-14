import sqlite3


def init_db(user_id:str) -> None:
    conn = sqlite3.connect(f"{user_id}.db")
    c = conn.cursor()
    c.execute("CREATE TABLE status "
              "(id INTEGER PRIMARY KEY, status INTEGER NOT NULL);")
    c.execute("INSERT INTO status (id, status) VALUES (1, 1);")
    c.execute("CREATE TABLE spotify_playlists "
              "(id INTEGER PRIMARY KEY AUTOINCREMENT, sp_playlist_id TEXT NOT NULL, "
              "playlist_name TEXT NOT NULL, playlist_description TEXT);")
    c.execute("CREATE TABLE spotify_songs "
              "(id INTEGER PRIMARY KEY AUTOINCREMENT, sp_song_id TEXT NOT NULL, song_name TEXT NOT NULL, "
              "album_name TEXT NOT NULL, album_date DATE NOT NULL , artist_name TEXT NOT NULL);")
    c.execute("CREATE TABLE spotify_playlist_songs "
              "(id INTEGER PRIMARY KEY AUTOINCREMENT, playlist_id INT NOT NULL, song_id INTEGER NOT NULL);")
    c.execute("CREATE TABLE youtube_playlists "
              "(id INTEGER PRIMARY KEY AUTOINCREMENT, yt_playlist_id TEXT NOT NULL, playlist_name TEXT NOT NULL );")
    c.execute("CREATE TABLE youtube_songs"
              "(id INTEGER PRIMARY KEY AUTOINCREMENT, yt_song_id TEXT NOT NULL, song_name TEXT NOT NULL, "
              "channel_id TEXT NOT NULL, channel_name TEXT NOT NULL);")
    c.execute("CREATE TABLE youtube_playlist_songs "
              "(id INTEGER PRIMARY KEY AUTOINCREMENT, playlist_id TEXT NOT NULL, song_id TEXT NOT NULL);")
    c.execute("CREATE TABLE youtube_spotify_playlists "
              "(id INTEGER PRIMARY KEY AUTOINCREMENT, spotify_id INTEGER NOT NULL, youtube_id INTEGER NOT NULL, "
              "done INTEGER NOT NULL);")
    conn.commit()
    conn.close()


def insert_spotify_playlist(user_id:str, sp_id: str, name: str, description: str) -> None:
    conn = sqlite3.connect(f"{user_id}.db")
    c = conn.cursor()
    c.execute("INSERT INTO spotify_playlists (sp_playlist_id, playlist_name, playlist_description) VALUES (?, ?, ?)",
              (sp_id, name, description))
    conn.commit()
    conn.close()


def insert_spotify_song() -> None:
    pass


def get_status(user_id:str) -> int:
    conn = sqlite3.connect(f"{user_id}.db")
    c = conn.cursor()
    c.execute("SELECT status FROM status WHERE id = 1;")
    status = c.fetchone()
    conn.close()
    return status


def get_spotify_playlist(user_id:str, id: tuple) -> tuple:
    conn = sqlite3.connect(f"{user_id}.db")
    c = conn.cursor()
    c.execute(f"SELECT * FROM spotify_playlists WHERE {id[0]} = {id[1]};")
    playlist = c.fetchone()
    conn.close()
    return playlist


def list_spotify_playlists(user_id:str) -> tuple:
    conn = sqlite3.connect(f"{user_id}.db")
    c = conn.cursor()
    c.execute("SELECT * FROM spotify_playlists;")
    playlists = c.fetchall()
    conn.close()
    return playlists


def get_spotify_song(user_id:str, id: tuple) -> tuple:
    conn = sqlite3.connect(f"{user_id}.db")
    c = conn.cursor()
    c.execute(f"SELECT * FROM spotify_songs WHERE {id[0]} = {id[1]};")
    song = c.fetchone()
    conn.close()
    return song


def list_spotify_songs(user_id:str) -> tuple:
    conn = sqlite3.connect(f"{user_id}.db")
    c = conn.cursor()
    c.execute("SELECT * FROM spotify_songs;")
    songs = c.fetchall()
    conn.close()
    return songs


def list_songs_in_spotify_playlist(user_id:str, playlist_id: int) -> tuple:
    conn = sqlite3.connect(f"{user_id}.db")
    c = conn.cursor()
    c.execute(f"SELECT song_id FROM spotify_playlist_songs WHERE playlisd_id = {playlist_id};")
    songs = c.fetchall()
    conn.close()
    return songs
