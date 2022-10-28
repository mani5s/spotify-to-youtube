import sqlite3


class database:
    def __init__(self, user_id: str) -> int:
        self.db_id = user_id
        conn = sqlite3.connect(f"{self.db_id}.db")
        c = conn.cursor()
        try:
            c.execute("CREATE TABLE status "
                      "(id INTEGER PRIMARY KEY, status INTEGER NOT NULL);")
            c.execute("INSERT INTO status (id, status) VALUES (1, 1);")
            c.execute("CREATE TABLE spotify_playlists"
                      "(id INTEGER PRIMARY KEY AUTOINCREMENT, sp_playlist_id TEXT NOT NULL UNIQUE, "
                      "playlist_name TEXT NOT NULL, playlist_description TEXT);")
            c.execute("CREATE TABLE spotify_albums"
                      "(id INTEGER PRIMARY KEY AUTOINCREMENT, sp_album_id TEXT NOT NULL UNIQUE, album_name TEXT NOT NULL, album_date TEXT NOT NULL);")
            c.execute("CREATE TABLE spotify_artists"
                      "(id INTEGER PRIMARY KEY AUTOINCREMENT, sp_artist_id TEXT NOT NULL UNIQUE, artist_name TEXT NOT NULL);")
            c.execute("CREATE TABLE spotify_songs"
                      "(id INTEGER PRIMARY KEY AUTOINCREMENT, sp_song_id TEXT NOT NULL UNIQUE, song_name TEXT NOT NULL);")
            c.execute("CREATE TABLE spotify_song_album"
                      "(song_id INTEGER NOT NULL, album_id INTEGER NOT NULL,"
                      "PRIMARY KEY (song_id, album_id),"
                      "FOREIGN KEY (song_id) REFERENCES spotify_songs(id),"
                      "FOREIGN KEY (album_id) REFERENCES spotify_albums(id));")
            c.execute("CREATE TABLE spotify_song_artist"
                      "(song_id INTEGER NOT NULL, artist_id INTEGER NOT NULL,"
                      "PRIMARY KEY (song_id, artist_id),"
                      "FOREIGN KEY (song_id) REFERENCES spotify_songs(id),"
                      "FOREIGN KEY (artist_id) REFERENCES spotify_artists(id));")
            c.execute("CREATE TABLE spotify_playlist_songs"
                      "(playlist_id INTEGER NOT NULL, song_id INTEGER NOT NULL,"
                      "PRIMARY KEY (playlist_id, song_id),"
                      "FOREIGN KEY (playlist_id) REFERENCES spotify_playlists(id),"
                      "FOREIGN KEY (song_id) REFERENCES spotify_songs(id));")
            c.execute("CREATE TABLE youtube_playlists"
                      "(id INTEGER PRIMARY KEY AUTOINCREMENT, yt_playlist_id TEXT NOT NULL, playlist_name TEXT NOT NULL);")
            c.execute("CREATE TABLE youtube_songs"
                      "(id INTEGER PRIMARY KEY AUTOINCREMENT, yt_song_id TEXT NOT NULL, song_name TEXT NOT NULL, "
                      "channel_id TEXT NOT NULL, channel_name TEXT NOT NULL);")
            c.execute("CREATE TABLE youtube_playlist_songs"
                      "(playlist_id TEXT NOT NULL, song_id TEXT NOT NULL,"
                      "PRIMARY KEY (playlist_id, song_id),"
                      "FOREIGN KEY (playlist_id) REFERENCES youtube_playlists(id),"
                      "FOREIGN KEY (song_id) REFERENCES youtube_songs(id));")
            c.execute("CREATE TABLE youtube_spotify_playlists"
                      "(spotify_id INTEGER NOT NULL, youtube_id INTEGER NOT NULL, done INTEGER NOT NULL,"
                      "PRIMARY KEY (spotify_id, youtube_id),"
                      "FOREIGN KEY (spotify_id) REFERENCES spotify_playlists(id),"
                      "FOREIGN KEY (youtube_id) REFERENCES youtube_playlists(id));")
            conn.commit()
            print("Initialised.")
        except sqlite3.OperationalError:
            print("DB already exits.")

    def insert_spotify_playlist(self, sp_id: str, name: str, description: str) -> int:
        conn = sqlite3.connect(f"{self.db_id}.db")
        c = conn.cursor()
        r = c.execute(
            "INSERT INTO spotify_playlists (sp_playlist_id, playlist_name, playlist_description) VALUES (?, ?, ?)",
            (sp_id, name, description))
        r = r.lastrowid
        conn.commit()
        conn.close()
        return r

    def insert_spotify_song(self, song: tuple) -> int:
        conn = sqlite3.connect(f"{self.db_id}.db")
        c = conn.cursor()
        try:
            song_id = c.execute("INSERT INTO spotify_songs (sp_song_id, song_name) VALUES (?, ?)",
                                (song[0], song[1])).lastrowid
            conn.commit()
        except sqlite3.IntegrityError:
            song_id = c.execute(
                f"SELECT id FROM spotify_songs WHERE sp_song_id={song[0]} AND song_name={song[1]}").fetchone()

        conn.close()
        return song_id

    def insert_spotify_album(self, album: tuple) -> int:
        conn = sqlite3.connect(f"{self.db_id}.db")
        c = conn.cursor()
        try:
            album_id = c.execute("INSERT INTO spotify_albums (sp_album_id, album_name, album_date) VALUES (?, ?, ?)",
                                 (album[0], album[1], album[2])).lastrowid
            conn.commit()
        except sqlite3.IntegrityError:
            album_id = c.execute(
                f"SELECT id FROM spotify_albums WHERE sp_album_id={album[0]} AND album_name={album[1]}").fetchone()

        conn.close()
        return album_id

    def insert_spotify_artists(self, artists: list) -> list:
        def insert_artist(artist):
            try:
                return c.execute("INSERT INTO spotify_artists (sp_artist_id, artist_name) VALUES (?, ?)",
                                 (artist[0], artist[1])).lastrowid
            except sqlite3.IntegrityError:
                return c.execute(
                    f"SELECT id FROM spotify_artists WHERE sp_artist_id={artist[0]} AND artist_name={artist[1]}").fetchone()

        conn = sqlite3.connect(f"{self.db_id}.db")
        c = conn.cursor()
        album_ids = list(map(insert_artist, artists))
        conn.commit()
        conn.close()
        return album_ids

    def insert_spotify_song_artist(self, song_id: int, artist_ids: tuple) -> None:
        conn = sqlite3.connect(f"{self.db_id}.db")
        c = conn.cursor()
        data = [(song_id, a) for a in artist_ids]
        c.executemany("INSERT INTO spotify_song_artist (song_id, artist_id) VALUES (?, ?)", data)
        conn.commit()
        conn.close()

    def insert_spotify_song_album(self, song_id: int, album_id: int) -> None:
        conn = sqlite3.connect(f"{self.db_id}.db")
        c = conn.cursor()
        c.execute("INSERT INTO spotify_song_album (song_id, album_id) VALUES (?, ?)",
                  (song_id, album_id))
        conn.commit()
        conn.close()

    def insert_spotify_playlist_songs(self, playlist_songs: list) -> None:
        conn = sqlite3.connect(f"{self.db_id}.db")
        c = conn.cursor()
        c.executemany("INSERT INTO spotify_playlist_songs (playlist_id, song_id) VALUES (?, ?)", playlist_songs)
        conn.commit()
        conn.close()

    def spotify_complete(self) -> None:
        conn = sqlite3.connect(f"{self.db_id}.db")
        c = conn.cursor()
        c.execute("UPDATE status SET status = 2 WHERE id = 1;")
        conn.commit()
        conn.close()

    def get_status(self) -> int:
        conn = sqlite3.connect(f"{self.db_id}.db")
        c = conn.cursor()
        c.execute("SELECT status FROM status WHERE id = 1;")
        status = c.fetchone()
        conn.close()
        return status

    def get_spotify_playlist(self, id: tuple) -> tuple:
        conn = sqlite3.connect(f"{self.db_id}.db")
        c = conn.cursor()
        c.execute(f"SELECT * FROM spotify_playlists WHERE {id[0]} = {id[1]};")
        playlist = c.fetchone()
        conn.close()
        return playlist

    def list_spotify_playlists(self) -> tuple:
        conn = sqlite3.connect(f"{self.db_id}.db")
        c = conn.cursor()
        c.execute("SELECT * FROM spotify_playlists;")
        playlists = c.fetchall()
        conn.close()
        return playlists

    def get_spotify_song(self, id: tuple) -> tuple:
        conn = sqlite3.connect(f"{self.db_id}.db")
        c = conn.cursor()
        c.execute(f"SELECT * FROM spotify_songs WHERE {id[0]} = {id[1]};")
        song = c.fetchone()
        conn.close()
        return song

    def list_spotify_songs(self) -> tuple:
        conn = sqlite3.connect(f"{self.db_id}.db")
        c = conn.cursor()
        c.execute("SELECT * FROM spotify_songs;")
        songs = c.fetchall()
        conn.close()
        return songs

    def list_songs_in_spotify_playlist(self, playlist_id: int) -> tuple:
        conn = sqlite3.connect(f"{self.db_id}.db")
        c = conn.cursor()
        c.execute(f"SELECT song_id FROM spotify_playlist_songs WHERE playlisd_id = {playlist_id};")
        songs = c.fetchall()
        conn.close()
        return songs
