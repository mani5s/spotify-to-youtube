import os
import sqlite3
import threading


class SQLiteConnectionPool:
    def __init__(self, db_name):
        self.db_name = db_name
        self.lock = threading.Lock()

    def __enter__(self):
        self.lock.acquire()
        self.connection = sqlite3.connect(self.db_name)
        return self.connection

    def __exit__(self, type, value, traceback):
        self.connection.close()
        self.lock.release()


class Database:
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

    def configure_database(self):
        with SQLiteConnectionPool(f"{self.db_id}.db") as conn:
            c = conn.cursor()
            c.execute("PRAGMA journal_mode=WAL")
            c.execute("PRAGMA cache_size=10000")

    def initialize_database(self, conn):
        self.configure_database()
        try:
            if conn:
                c = conn.cursor()
            else:
                with SQLiteConnectionPool(f"{self.db_id}.db") as conn:
                    c = conn.cursor()

            c.execute("CREATE TABLE status "
                      "(id INTEGER PRIMARY KEY, status INTEGER NOT NULL);")
            c.execute("INSERT INTO status (id, status) VALUES (1, 1);")
            # create tables for spotify data
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
            # create tables for youtube
            c.execute("CREATE TABLE youtube_playlists"
                      "(id INTEGER PRIMARY KEY AUTOINCREMENT, yt_playlist_id TEXT NOT NULL,"
                      "playlist_name TEXT NOT NULL, playlist_description TEXT);")
            c.execute("CREATE TABLE youtube_songs"
                      "(id INTEGER PRIMARY KEY AUTOINCREMENT, yt_song_id TEXT NOT NULL, song_name TEXT NOT NULL);")
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

    def batch_insert_with_ignore(self, conn, table, columns, data_list):
        placeholders = ', '.join('?' * len(columns))
        columns = ', '.join(columns)
        try:
            c = conn.cursor()
            c.executemany(f"INSERT OR IGNORE INTO {table} ({columns}) VALUES ({placeholders})", data_list)
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error batch inserting into {table}: {e}")

    async def insert_spotify_playlists(self, playlists: list) -> None:
        with SQLiteConnectionPool(f"{self.db_id}.db") as conn:
            columns = ['sp_playlist_id', 'playlist_name', 'playlist_description']
            self.batch_insert_with_ignore(conn, "spotify_playlists", columns, playlists)

    async def insert_spotify_songs(self, songs: list) -> None:
        data = [(s[0], s[1]) for s in songs]
        with SQLiteConnectionPool(f"{self.db_id}.db") as conn:
            self.batch_insert_with_ignore(conn, "spotify_songs", ['sp_song_id', 'song_name'], data)

    async def insert_spotify_albums(self, albums: list) -> None:
        data = [(a[0], a[1], a[2]) for a in albums]
        with SQLiteConnectionPool(f"{self.db_id}.db") as conn:
            self.batch_insert_with_ignore(conn, "spotify_albums", ['sp_album_id', 'album_name', 'album_date'], data)

    async def insert_spotify_artists(self, artists: list) -> list:
        data = [(a[0], a[1]) for a in artists]
        with SQLiteConnectionPool(f"{self.db_id}.db") as conn:
            self.batch_insert_with_ignore(conn, "spotify_artists", ['sp_artist_id', 'artist_name'], data)

    async def insert_spotify_song_artist(self, song_artist_data: list) -> None:
        with SQLiteConnectionPool(f"{self.db_id}.db") as conn:
            self.batch_insert_with_ignore(conn, "spotify_song_artist", ['song_id', 'artist_id'], song_artist_data)

    async def insert_spotify_song_album(self, song_album_data: list) -> None:
        with SQLiteConnectionPool(f"{self.db_id}.db") as conn:
            self.batch_insert_with_ignore(conn, "spotify_song_album", ['song_id', 'album_id'], song_album_data)

    async def insert_spotify_playlist_songs(self, playlist_songs: list) -> None:
        with SQLiteConnectionPool(f"{self.db_id}.db") as conn:
            self.batch_insert_with_ignore(conn, "spotify_playlist_songs", ['playlist_id', 'song_id'], playlist_songs)

    def get_existing_song_id(self, song: tuple) -> int:
        try:
            with SQLiteConnectionPool(f"{self.db_id}.db") as conn:
                c = conn.cursor()
                c.execute("SELECT id FROM spotify_songs WHERE sp_song_id=? AND song_name=?", (song[0], song[1]))
                result = c.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Error getting existing song ID: {e}")
            return None

    def get_existing_album_id(self, album: tuple) -> int:
        try:
            with SQLiteConnectionPool(f"{self.db_id}.db") as conn:
                c = conn.cursor()
                c.execute("SELECT id FROM spotify_albums WHERE sp_album_id=? AND album_name=?", (album[0], album[1]))
                result = c.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Error getting existing album ID: {e}")
            return None

    def get_existing_artist_id(self, artist: tuple) -> int:
        try:
            with SQLiteConnectionPool(f"{self.db_id}.db") as conn:
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
            with SQLiteConnectionPool(f"{self.db_id}.db") as conn:
                c = conn.cursor()
                c.execute("UPDATE status SET status = 2 WHERE id = 1;")
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error updating Spotify status: {e}")

    def get_status(self) -> int:
        try:
            with SQLiteConnectionPool(f"{self.db_id}.db") as conn:
                c = conn.cursor()
                c.execute("SELECT status FROM status WHERE id = 1;")
                status = c.fetchone()
                return status[0] if status else None
        except sqlite3.Error as e:
            print(f"Error getting status: {e}")
            return None

    def list_spotify_songs(self) -> list:
        try:
            with SQLiteConnectionPool(f"{self.db_id}.db") as conn:
                c = conn.cursor()
                c.execute("SELECT id, song_name FROM spotify_songs;")
                songs = c.fetchall()
                return songs
        except sqlite3.Error as e:
            print(f"Error listing Spotify songs: {e}")
            return []

    def get_spotify_song_artist(self, song_id: int) -> list:
        try:
            with SQLiteConnectionPool(f"{self.db_id}.db") as conn:
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
            with SQLiteConnectionPool(f"{self.db_id}.db") as conn:
                c = conn.cursor()
                c.execute("SELECT artist_name FROM spotify_artists WHERE id = ?", (artist_id,))
                result = c.fetchone()
                return result[0] if result else ""
        except sqlite3.Error as e:
            print(f"Error getting artist name: {e}")
            return ""
        

    async def insert_youtube_songs(self, songs: list) -> None:
        data = [(s[0], s[1]) for s in songs]
        with SQLiteConnectionPool(f"{self.db_id}.db") as conn:
            self.batch_insert_with_ignore(conn, "yt_songs", ['yt_song_id', 'song_name'], data)

    async def insert_youtube_playlist(self, playlist_info: str) -> None:
        with SQLiteConnectionPool(f"{self.db_id}.db") as conn:
            self.batch_insert_with_ignore(conn, "yt_playlists", ["yt_playlist_id", "playlist_name", "playlist_description"], playlist_info)

    async def insert_youtube_playlist_songs(self, playlist_id: str, songs: list) -> None: 
        data = [(playlist_id, song) for song in songs]
        with SQLiteConnectionPool(f"{self.db_id}.db") as conn:
            self.batch_insert_with_ignore(conn, "youtube_playlist_songs", ["playlist_id", "song_id"], data)

        
    async def insert_youtube_spotify_playlists(self, yt_id: str, sp_id: str) -> None:
        with SQLiteConnectionPool(f"{self.db_id}.db") as conn:
            self.batch_insert_with_ignore(conn, "youtube_spotify_playlists", ["spotify_id", "youtube_id", "done"], (sp_id, yt_id, 0))

    async def update_youtube_spotify_playlist(self, yt_id: str, update: int) -> None:
        try:
            with SQLiteConnectionPool(f"{self.db_id}.db") as conn:
                c = conn.cursor()
                c.execute("UPDATE done=? WHERE yt_id=?", (update, yt_id))
                conn.commit()

        except sqlite3.error as e:
            print(f"Error updating youtube_spotify_playlist {e}")

    async def insert_youtube_spotify_songs(self, data: list):
        with SQLiteConnectionPool(f"{self.db_id}.db") as conn:
            self.batch_insert_with_ignore(conn, "youtube_spotify_songs", ["spotify_id", "youtube_id"], data)