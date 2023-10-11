import os
import sqlite3


class database:
    def __init__(self, user_id: str) -> None:
        self.db_id = user_id
        db_file = f"{self.db_id}.db"

        if os.path.exists(db_file):
            with sqlite3.connect(db_file) as conn:
                if not self.is_table_present(conn, 'status'):
                    self.initialize_database(conn)
                else:
                    print(f"Table 'status' already exists in database '{db_file}'. Skipping initialization.")
        else:
            with sqlite3.connect(db_file) as conn:
                self.initialize_database(conn)

    @staticmethod
    def is_table_present(conn, table_name: str) -> bool:
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
        return bool(c.fetchone())

    def initialize_database(self, conn):
        try:
            if conn:
                c = conn.cursor()
            else:
                with sqlite3.connect(f"{self.db_id}.db") as conn:
                    c = conn.cursor()

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
                      "(id INTEGER PRIMARY KEY AUTOINCREMENT, yt_playlist_id TEXT NOT NULL);")
            c.execute("CREATE TABLE youtube_songs"
                      "(id INTEGER PRIMARY KEY AUTOINCREMENT, yt_song_id TEXT NOT NULL);")
            c.execute("CREATE TABLE youtube_playlist_songs"
                      "(playlist_id INTEGER NOT NULL, song_id INTEGER NOT NULL,"
                      "PRIMARY KEY (playlist_id, song_id),"
                      "FOREIGN KEY (playlist_id) REFERENCES youtube_playlists(id),"
                      "FOREIGN KEY (song_id) REFERENCES youtube_songs(id));")
            c.execute("CREATE TABLE youtube_spotify_playlists"
                      "(spotify_id INTEGER NOT NULL, youtube_id INTEGER NOT NULL, done INTEGER NOT NULL,"
                      "PRIMARY KEY (spotify_id, youtube_id),"
                      "FOREIGN KEY (spotify_id) REFERENCES spotify_playlists(id),"
                      "FOREIGN KEY (youtube_id) REFERENCES youtube_playlists(id));")
            c.execute("CREATE TABLE youtube_spotify_songs"
                      "(spotify_id INTEGER NOT NULL, youtube_id INTEGER NOT NULL,"
                      "PRIMARY KEY (spotify_id, youtube_id),"
                      "FOREIGN KEY (spotify_id) REFERENCES spotify_songs(id),"
                      "FOREIGN KEY (youtube_id) REFERENCES youtube_songs(id));")
            conn.commit()
            print("Initialised.")
        except sqlite3.Error as e:
            print(f"Error initializing database: {e}")

    def insert_with_ignore(self, conn, table, columns, data):
        placeholders = ', '.join('?' * len(data))
        columns = ', '.join(columns)
        try:
            c = conn.cursor()
            c.execute(f"INSERT OR IGNORE INTO {table} ({columns}) VALUES ({placeholders})", data)
            conn.commit()
            return c.lastrowid
        except sqlite3.Error as e:
            print(f"Error inserting into {table}: {e}")
            return None

    def insert_spotify_playlist(self, sp_id: str, name: str, description: str) -> int:
        with sqlite3.connect(f"{self.db_id}.db") as conn:
            return self.insert_with_ignore(conn, "spotify_playlists",
                                           ['sp_playlist_id', 'playlist_name', 'playlist_description'],
                                           (sp_id, name, description))

    def insert_spotify_song(self, song: tuple) -> int:
        with sqlite3.connect(f"{self.db_id}.db") as conn:
            return self.insert_with_ignore(conn, "spotify_songs", ['sp_song_id', 'song_name'], song)

    def insert_spotify_album(self, album: tuple) -> int:
        with sqlite3.connect(f"{self.db_id}.db") as conn:
            return self.insert_with_ignore(conn, "spotify_albums", ['sp_album_id', 'album_name', 'album_date'], album)

    def insert_spotify_artists(self, artists: list) -> list:
        artist_ids = []
        with sqlite3.connect(f"{self.db_id}.db") as conn:
            for artist in artists:
                artist_id = self.insert_with_ignore(conn, "spotify_artists", ['sp_artist_id', 'artist_name'], artist)
                artist_ids.append(artist_id)
        return artist_ids

    def insert_spotify_song_artist(self, song_id: int, artist_ids: list) -> None:
        with sqlite3.connect(f"{self.db_id}.db") as conn:
            for artist_id in artist_ids:
                self.insert_with_ignore(conn, "spotify_song_artist", ['song_id', 'artist_id'], (song_id, artist_id))

    def insert_spotify_song_album(self, song_id: int, album_id: int) -> None:
        with sqlite3.connect(f"{self.db_id}.db") as conn:
            self.insert_with_ignore(conn, "spotify_song_album", ['song_id', 'album_id'], (song_id, album_id))

    def insert_spotify_playlist_songs(self, playlist_songs: list) -> None:
        with sqlite3.connect(f"{self.db_id}.db") as conn:
            for ps in playlist_songs:
                self.insert_with_ignore(conn, "spotify_playlist_songs", ['playlist_id', 'song_id'], ps)

    def get_existing_song_id(self, song: tuple) -> int:
        try:
            with sqlite3.connect(f"{self.db_id}.db") as conn:
                c = conn.cursor()
                c.execute("SELECT id FROM spotify_songs WHERE sp_song_id=? AND song_name=?", (song[0], song[1]))
                result = c.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Error getting existing song ID: {e}")
            return None

    def get_existing_album_id(self, album: tuple) -> int:
        try:
            with sqlite3.connect(f"{self.db_id}.db") as conn:
                c = conn.cursor()
                c.execute("SELECT id FROM spotify_albums WHERE sp_album_id=? AND album_name=?", (album[0], album[1]))
                result = c.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Error getting existing album ID: {e}")
            return None

    def get_existing_artist_id(self, artist: tuple) -> int:
        try:
            with sqlite3.connect(f"{self.db_id}.db") as conn:
                c = conn.cursor()
                c.execute("SELECT id FROM spotify_artists WHERE sp_artist_id=? AND artist_name=?",
                          (artist[0], artist[1]))
                result = c.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Error getting existing artist ID: {e}")
            return None

    def spotify_complete(self) -> None:
        try:
            with sqlite3.connect(f"{self.db_id}.db") as conn:
                c = conn.cursor()
                c.execute("UPDATE status SET status = 2 WHERE id = 1;")
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error updating Spotify status: {e}")

    def get_status(self) -> int:
        try:
            with sqlite3.connect(f"{self.db_id}.db") as conn:
                c = conn.cursor()
                c.execute("SELECT status FROM status WHERE id = 1;")
                status = c.fetchone()
                return status[0] if status else None
        except sqlite3.Error as e:
            print(f"Error getting status: {e}")
            return None

    def list_spotify_songs(self) -> list:
        try:
            with sqlite3.connect(f"{self.db_id}.db") as conn:
                c = conn.cursor()
                c.execute("SELECT id, song_name FROM spotify_songs;")
                songs = c.fetchall()
                return songs
        except sqlite3.Error as e:
            print(f"Error listing Spotify songs: {e}")
            return []

    def get_spotify_song_artist(self, song_id: int) -> list:
        try:
            with sqlite3.connect(f"{self.db_id}.db") as conn:
                c = conn.cursor()
                artist_ids = c.execute("SELECT artist_id FROM spotify_song_artist WHERE song_id = ?",
                                       (song_id,)).fetchall()
                artists = [self.get_artist_name(artist_id[0]) for artist_id in artist_ids]
                return artists
        except sqlite3.Error as e:
            print(f"Error getting song artists: {e}")
            return []

    def get_artist_name(self, artist_id: int) -> str:
        try:
            with sqlite3.connect(f"{self.db_id}.db") as conn:
                c = conn.cursor()
                c.execute("SELECT artist_name FROM spotify_artists WHERE id = ?", (artist_id,))
                result = c.fetchone()
                return result[0] if result else ""
        except sqlite3.Error as e:
            print(f"Error getting artist name: {e}")
            return ""
