import asyncio
import logging
import re
from typing import List, Dict, Optional
from webbrowser import open
import multiprocessing

from spotify_auth import run
import spotify
import database
from youtube import YouTubeManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PlaylistTransferManager:
    def __init__(self):
        self.spotify_user = None
        self.database = None
        self.youtube_manager = None
        
    def initialize(self, user_id: Optional[str] = None) -> None:
        """Initialize the transfer manager with either existing user_id or new authentication"""
        if user_id:
            self.database = database.Database(user_id)
            logger.info(f"Initialized with existing user ID: {user_id}")
        else:
            code = self._start_spotify_auth_process()
            self.spotify_user = spotify.spotify_user(code)
            self.database = database.Database(self.spotify_user.id)
            logger.info("Initialized with new Spotify authentication")
            
        self.youtube_manager = YouTubeManager(self.database)

    @staticmethod
    def _start_spotify_auth_process() -> str:
        """Start Spotify authentication process and return the authorization code"""
        queue = multiprocessing.Queue()
        auth_process = multiprocessing.Process(target=run, args=(queue,))
        auth_process.start()
        
        open("http://localhost:6969")
        code = queue.get(block=True)
        auth_process.terminate()
        
        return code

    def _get_playlist_indices(self, prompt: str) -> List[int]:
        """Get playlist indices from user input"""
        return [
            int(i) for i in re.split(r"\s+|,|\n", input(prompt)) 
            if re.fullmatch(r"\d+", i)
        ]

    def _print_playlists(self, playlists: List[Dict]) -> None:
        """Print playlists with indices"""
        print("\n\033[4mPlaylists\033[0m")
        for index, playlist in enumerate(playlists):
            print(f"{index}: {playlist['name']}")

    def _select_playlists(self, playlists: List[Dict]) -> List[Dict]:
        """Handle playlist selection logic"""
        self._print_playlists(playlists)
        
        selection_type = input(
            "\nSelect playlists: (A)ll | (I)nclude specific | (E)xclude specific: "
        ).lower()

        if selection_type == "a":
            return playlists

        if selection_type in ("i", "e"):
            action = "include" if selection_type == "i" else "exclude"
            indices = self._get_playlist_indices(
                f"\nEnter indices to {action} (comma or space separated): "
            )

            if selection_type == "i":
                return [p for i, p in enumerate(playlists) if i in indices]
            return [p for i, p in enumerate(playlists) if i not in indices]

        logger.warning("Invalid selection type, defaulting to all playlists")
        return playlists

    def _edit_selected_playlists(
        self, selected: List[Dict], all_playlists: List[Dict]
    ) -> List[Dict]:
        """Edit the current playlist selection"""
        action = input("\n(A)dd or (R)emove playlists: ").lower()

        if action == "a":
            available = [p for p in all_playlists if p not in selected]
            self._print_playlists(available)
            indices = self._get_playlist_indices(
                "\nEnter indices to add (comma or space separated): "
            )
            return selected + [available[i] for i in indices if 0 <= i < len(available)]

        if action == "r":
            self._print_playlists(selected)
            indices = self._get_playlist_indices(
                "\nEnter indices to remove (comma or space separated): "
            )
            return [p for i, p in enumerate(selected) if i not in indices]

        logger.warning("Invalid edit action, returning original selection")
        return selected

    def _confirm_playlist_selection(
        self, selected: List[Dict], all_playlists: List[Dict]
    ) -> List[Dict]:
        """Confirm the playlist selection with the user"""
        while True:
            print("\n\033[4mSelected Playlists\033[0m")
            self._print_playlists(selected)
            
            option = input("\n(C)onfirm | (M)odify | (R)estart selection: ").lower()

            if option == "c":
                logger.info(f"Confirmed {len(selected)} playlists for transfer")
                return selected

            if option == "m":
                selected = self._edit_selected_playlists(selected, all_playlists)
            else:
                selected = self._select_playlists(all_playlists)

    async def _insert_songs_for_playlist(self, playlist: Dict) -> None:
        """Insert all songs from a playlist into the database"""
        try:
            await self.database.insert_spotify_playlists([
                (playlist["id"], playlist["name"], playlist["description"])
            ])
            
            songs = await self.spotify_user.get_playlist_songs(playlist["id"])
            
            # Prepare data for batch insertion
            song_data = [(s["track"]["id"], s["track"]["name"]) for s in songs]
            album_data = [
                (
                    s["track"]["album"]["id"],
                    s["track"]["album"]["name"],
                    s["track"]["album"]["release_date"]
                )
                for s in songs
            ]
            artist_data = [
                (a["id"], a["name"]) 
                for s in songs 
                for a in s["track"]["artists"]
            ]
            song_artist_data = [
                (s["track"]["id"], a["id"]) 
                for s in songs 
                for a in s["track"]["artists"]
            ]
            song_album_data = [
                (s["track"]["id"], s["track"]["album"]["id"]) 
                for s in songs
            ]
            playlist_song_data = [
                (playlist["id"], s["track"]["id"]) 
                for s in songs
            ]

            # Execute batch insertions
            await asyncio.gather(
                self.database.insert_spotify_songs(song_data),
                self.database.insert_spotify_albums(album_data),
                self.database.insert_spotify_artists(artist_data),
                self.database.insert_spotify_song_artist(song_artist_data),
                self.database.insert_spotify_song_album(song_album_data),
                self.database.insert_spotify_playlist_songs(playlist_song_data)
            )
            
            logger.info(f"Successfully processed playlist: {playlist['name']}")
            
        except Exception as e:
            logger.error(f"Error processing playlist {playlist['name']}: {e}")

    async def process_spotify_playlists(self) -> None:
        """Process all selected Spotify playlists"""
        try:
            playlists = await self.spotify_user.get_playlists()
            selected_playlists = self._confirm_playlist_selection(
                self._select_playlists(playlists),
                playlists
            )

            logger.info(f"Starting transfer of {len(selected_playlists)} playlists")
            
            # Process playlists concurrently
            await asyncio.gather(*[
                self._insert_songs_for_playlist(playlist)
                for playlist in selected_playlists
            ])
            
            self.database.spotify_complete()
            logger.info("Spotify playlist processing completed")
            
        except Exception as e:
            logger.error(f"Error in process_spotify_playlists: {e}")

    async def process_youtube_transfer(self) -> None:
        """Handle the YouTube transfer process"""
        try:
            # First authenticate with YouTube Music
            self.youtube_manager.authenticate()
            logger.info("YouTube Music authentication successful")

            # Get all playlists from database
            playlists = self.database.list_spotify_playlists()
            if not playlists:
                logger.error("No playlists found in database")
                return

            # Process each playlist
            for playlist_id, name, description in playlists:
                try:
                    # Sanitize playlist name and description
                    sanitized_name = name.strip() if name else "Untitled Playlist"
                    sanitized_desc = (description or "").strip()
                    
                    # Create playlist with sanitized inputs
                    logger.info(f"Creating playlist: {sanitized_name}")
                    yt_playlist_id = await self.youtube_manager.create_playlist(
                        name=sanitized_name,
                        description=sanitized_desc
                    )
                    
                    if not yt_playlist_id:
                        logger.error(f"Failed to create playlist: {sanitized_name}")
                        continue

                    # Get songs for this playlist and add them
                    spotify_songs = self.database.get_playlist_songs(playlist_id)
                    if spotify_songs:
                        logger.info(f"Adding {len(spotify_songs)} songs to playlist: {sanitized_name}")
                        # Add songs in batches
                        for i in range(0, len(spotify_songs), self.youtube_manager.batch_size):
                            batch = spotify_songs[i:i + self.youtube_manager.batch_size]
                            success = await self.youtube_manager.add_songs_to_playlist(
                                yt_playlist_id, 
                                [song['videoId'] for song in batch]
                            )
                            if success:
                                logger.info(f"Added batch {i//self.youtube_manager.batch_size + 1} to {sanitized_name}")
                            else:
                                logger.error(f"Failed to add batch to {sanitized_name}")
                            
                            await asyncio.sleep(2)  # Rate limiting between batches
                    
                except Exception as playlist_error:
                    logger.error(f"Error processing playlist {name}: {playlist_error}")
                    continue
                
            logger.info("YouTube transfer completed successfully")
            
        except Exception as e:
            logger.error(f"Error in YouTube transfer: {e}")
            raise

    async def execute_transfer(self) -> None:
        """Execute the complete transfer process based on current status"""
        status = self.database.get_status()
        logger.info(f"Current transfer status: {status}")

        if status == 1:
            await self.process_spotify_playlists()
            await self.process_youtube_transfer()
        elif status == 2:
            await self.process_youtube_transfer()
        else:
            logger.info("Transfer already completed or in invalid state")

async def main():
    """Main entry point for the application"""
    try:
        transfer_manager = PlaylistTransferManager()
        
        # For testing with existing user ID:
        # transfer_manager.initialize(user_id="existing_user_id")
        
        # For new authentication:
        transfer_manager.initialize()
        
        await transfer_manager.execute_transfer()
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())