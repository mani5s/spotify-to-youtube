import asyncio
import logging
import re
from typing import List, Dict, Optional, Tuple
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
            self.spotify_user = None  # Will authenticate on-demand if needed
            logger.info(f"Initialized with existing user ID: {user_id}")
        else:
            code = self._start_spotify_auth_process()
            self.spotify_user = spotify.spotify_user(code)
            self.database = database.Database(self.spotify_user.id)
            logger.info("Initialized with new Spotify authentication")
            
        self.youtube_manager = YouTubeManager(self.database)
        
    def ensure_spotify_authenticated(self) -> bool:
        """Ensure Spotify is authenticated if not already"""
        if not self.spotify_user:
            try:
                logger.info("Authenticating with Spotify (on-demand)...")
                code = self._start_spotify_auth_process()
                self.spotify_user = spotify.spotify_user(code)
                logger.info("Successfully authenticated with Spotify")
                return True
            except Exception as e:
                logger.error(f"Failed to authenticate with Spotify: {e}")
                return False
        return True

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

    @staticmethod
    def extract_spotify_playlist_id(url: str) -> Optional[str]:
        """
        Extract playlist ID from a Spotify playlist URL or ID.
        
        Args:
            url (str): Spotify playlist URL or ID
            
        Returns:
            Optional[str]: Playlist ID if found, None otherwise
            
        Examples:
            - From URL: "https://open.spotify.com/playlist/5g2H7vxp1LlkIXRsIX93ns"
            - From URL with parameters: "https://open.spotify.com/playlist/3dYjKLhLZdbzK6q4gUs3ur?si=db9fff4239db4f4b"
            - From direct ID: "5g2H7vxp1LlkIXRsIX93ns"
        """
        # If input is already just an ID, validate and return it
        if re.match(r'^[a-zA-Z0-9]{22}$', url):
            return url
            
        # Regular expression to match Spotify playlist URLs with optional query parameters
        pattern = r'spotify\.com/playlist/([a-zA-Z0-9]{22})(?:\?|$)'
        
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        return None

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
            print(f"{index}: {playlist[1]}")

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
            logger.info(f"selected: {selected}")
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

    async def process_playlist_from_url(self, playlist_url: str) -> bool:
        """
        Process a playlist from a Spotify URL or playlist ID.
        
        Args:
            playlist_url (str): Spotify playlist URL or ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        playlist_id = self.extract_spotify_playlist_id(playlist_url)
        if not playlist_id:
            logger.error(f"Invalid playlist URL or ID: {playlist_url}")
            return False
        
        # For single playlist processing, we need Spotify authentication
        if not self.spotify_user:
            if not self.ensure_spotify_authenticated():
                logger.error("Cannot process playlist without Spotify authentication")
                return False
                
        return await self.process_single_playlist(playlist_id)

    async def process_single_playlist(self, playlist_id: str) -> bool:
        """
        Process a single Spotify playlist and transfer it to YouTube Music.
        
        Args:
            playlist_id (str): Spotify playlist ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get playlist details
            playlist_data = await self.spotify_user.async_fetch(
                f"https://api.spotify.com/v1/playlists/{playlist_id}"
            )
            
            # Format playlist data
            playlist = {
                "id": playlist_data["id"],
                "name": playlist_data["name"],
                "description": playlist_data.get("description", "")
            }
            
            # Process playlist songs
            await self._insert_songs_for_playlist(playlist)
            
            # Create YouTube Music playlist and transfer songs
            sanitized_name = playlist["name"].strip() if playlist["name"] else "Untitled Playlist"
            sanitized_desc = (playlist["description"] or "").strip()
            
            yt_playlist_id = await self.youtube_manager.create_playlist(
                name=sanitized_name,
                description=sanitized_desc
            )
            
            if not yt_playlist_id:
                logger.error(f"Failed to create YouTube Music playlist: {sanitized_name}")
                return False
                
            # Get and process songs
            spotify_songs = await self.database.get_playlist_songs(playlist_id)
            if any(t[0] is None for t in spotify_songs):
                song_deets = self.database.get_song_data(playlist_id=playlist_id)
                spotify_songs, yt_spot_mappings, failed_songs = await self.youtube_manager.batch_search_songs(song_deets)
                await self.database.insert_youtube_songs(spotify_songs)
                await self.database.insert_youtube_playlist_songs(playlist_id, spotify_songs)
                await self.database.insert_youtube_spotify_songs(yt_spot_mappings)
                
            if spotify_songs:
                logger.info(f"Adding {len(spotify_songs)} songs to playlist: {sanitized_name}")
                
                # Add songs in batches
                for i in range(0, len(spotify_songs), self.youtube_manager.batch_size):
                    batch = spotify_songs[i:i + self.youtube_manager.batch_size]
                    success = await self.youtube_manager.add_songs_to_playlist(
                        yt_playlist_id,
                        [song[0] for song in batch]
                    )
                    
                    if success:
                        logger.info(f"Added batch {i//self.youtube_manager.batch_size + 1} to {sanitized_name}")
                    else:
                        logger.error(f"Failed to add batch to {sanitized_name}")
                    
                    await asyncio.sleep(2)  # Rate limiting between batches
                    
            logger.info(f"Successfully processed playlist: {playlist['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing playlist {playlist_id}: {e}")
            return False

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

            logger.info(f"Starting transfer of playlists")
            
            # Process playlists concurrently
            await asyncio.gather(*[
                self._insert_songs_for_playlist(playlist)
                for playlist in playlists
            ])
            
            self.database.spotify_complete()
            logger.info("Spotify playlist processing completed")
            
        except Exception as e:
            logger.error(f"Error in process_spotify_playlists: {e}")

    async def process_youtube_transfer(self, playlist_ids: Optional[List[str]] = None) -> bool:
        """
        Handle the YouTube transfer process for specific playlists or all playlists.
        
        Args:
            playlist_ids (Optional[List[str]]): List of specific playlist IDs to process
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # First authenticate with YouTube Music if not already done
            if not self.youtube_manager:
                self.youtube_manager.authenticate("browser.json")
                logger.info("YouTube Music authentication successful")

            # Get playlists to process
            all_playlists = self.database.list_spotify_playlists()
            if not all_playlists:
                logger.error("No playlists found in database")
                return False
            
            if playlist_ids:
                playlists = [p for p in all_playlists if p[0] in playlist_ids]
            else:
                # Let user select playlists
                selected_playlists = self._confirm_playlist_selection(
                    self._select_playlists(all_playlists),
                    all_playlists
                )
                playlists = selected_playlists

            if not playlists:
                logger.warning("No playlists selected for transfer")
                return False
                
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
                    spotify_songs = await self.database.get_playlist_songs(playlist_id)
                    if any(t[0] is None for t in spotify_songs):
                        song_deets = self.database.get_song_data(playlist_id=playlist_id)
                        searched_songs, yt_spot_mappings, failed_songs = await self.youtube_manager.batch_search_songs(song_deets)
                        await self.database.insert_youtube_songs(searched_songs)
                        await self.database.insert_youtube_playlist_songs(playlist_id, searched_songs)
                        await self.database.insert_youtube_spotify_songs(yt_spot_mappings)

                    spotify_songs = await self.database.get_playlist_songs(playlist_id)                    
                        
                    if spotify_songs:
                        logger.info(f"Adding {len(spotify_songs)} songs to playlist: {sanitized_name}")
                        # Add songs in batches
                        for i in range(0, len(spotify_songs), self.youtube_manager.batch_size):
                            batch = spotify_songs[i:i + self.youtube_manager.batch_size]
                            success = await self.youtube_manager.add_songs_to_playlist(
                                yt_playlist_id, 
                                [song[0] for song in batch]
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
            return True
            
        except Exception as e:
            logger.error(f"Error in YouTube transfer: {e}")
            return False

    async def execute_transfer(self) -> None:
        """Execute the complete transfer process based on current status"""
        status = self.database.get_status()
        logger.info(f"Current transfer status: {status}")

        if status == 1:
            await self.process_spotify_playlists()
            await self.process_youtube_transfer()
            return True
        elif status == 2:
            await self.process_youtube_transfer()
            return True
        else:
            logger.info("Transfer already completed or in invalid state")
            return None

async def main():
    """Main entry point for the application"""
    try:
        # Initialize the transfer manager
        transfer_manager = PlaylistTransferManager()
        
        # CHOOSE INITIALIZATION METHOD:
        # ------------------------------
        
        # Option 1: Initialize with existing user ID (Spotify auth only when needed)
        # Useful when you just want to access existing database without re-authenticating
        transfer_manager.initialize(user_id="wp07i46i1vp008d0bkpkc5z25")
        
        # Option 2: Initialize with new authentication (always authenticates with Spotify)
        # transfer_manager.initialize()
        
        # Ensure YouTube authentication is set up
        transfer_manager.youtube_manager.authenticate("browser.json")
        
        # CHOOSE PROCESSING METHOD:
        # ------------------------
        
        # Option A: Process all playlists from database (doesn't need Spotify auth)
        success = await transfer_manager.execute_transfer()
        
        # Option B: Process a single playlist (will trigger Spotify auth if needed)
        # playlist_url = "https://open.spotify.com/playlist/75mqVGr1vxj5ybqBjUDzoH"
        # success = await transfer_manager.process_playlist_from_url(playlist_url)
        
        if success:
            logger.info("Playlist transfer completed successfully")
        else:
            logger.error("Failed to transfer playlist")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())