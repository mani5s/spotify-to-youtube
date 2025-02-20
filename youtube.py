import asyncio
from typing import List, Tuple, Dict, Optional
from ytmusicapi import YTMusic, setup
from difflib import SequenceMatcher
from youtube_auth import capture_headers
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeManager:
    def __init__(self, db, batch_size: int = 5, max_retries: int = 3, retry_delay: int = 5):
        self.db = db
        self.yt = YTMusic()
        self.authenticated_yt = None
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def authenticate(self, oauth_file: str = "browser.json") -> None:
        """Initialize authenticated YouTube Music instance"""
        try:
            self.authenticated_yt = YTMusic(oauth_file)
            logger.info("Successfully authenticated with YouTube Music")
        except Exception as e:
            logger.error(f"Failed to authenticate with YouTube Music: {e}")
            raise


    async def setup(self):
         await capture_headers()
         with open("headers.txt", "r") as file:
            headers = file.read()
            setup(filepath="browser.json", headers_raw=headers)

    @staticmethod
    def sanitize_text(text: str, max_length: int = 150) -> str:
        """Sanitize text for YouTube API"""
        if not text:
            return ""
        
        # Remove or replace problematic characters
        text = re.sub(r'[^\w\s-]', '', text)
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Trim whitespace
        text = text.strip()
        # Truncate if too long
        return text[:max_length]

    async def create_playlist(self, name: str, description: str = "", retry_count: int = 0) -> Optional[str]:
        """Create a YouTube Music playlist with retry logic and input validation"""
        if not self.authenticated_yt:
            logger.error("YouTube Music not authenticated")
            return None

        try:
            # Sanitize inputs
            sanitized_name = self.sanitize_text(name, max_length=150)
            sanitized_description = self.sanitize_text(description, max_length=500)

            if not sanitized_name:
                logger.error("Invalid playlist name after sanitization")
                return None

            playlist_id = self.authenticated_yt.create_playlist(
                title=sanitized_name,
                description=sanitized_description,
                privacy_status="UNLISTED"
            )
            
            logger.info(f"Successfully created playlist: {sanitized_name}")
            return playlist_id

        except Exception as e:
            if retry_count < self.max_retries:
                logger.warning(f"Retrying playlist creation for {name} after error: {e}")
                await asyncio.sleep(self.retry_delay * (retry_count + 1))
                return await self.create_playlist(name, description, retry_count + 1)
            
            logger.error(f"Failed to create playlist {name}: {e}")
            return None

    async def add_songs_to_playlist(self, playlist_id: str, song_ids: List[str], 
                                  retry_count: int = 0) -> bool:
        """Add songs to a playlist with retry logic"""
        if not self.authenticated_yt or not playlist_id or not song_ids:
            return False

        try:
            # Filter out any None or empty song IDs
            valid_song_ids = [sid for sid in song_ids if sid]
            logging.info(valid_song_ids)
            if not valid_song_ids:
                return False

            self.authenticated_yt.add_playlist_items(playlist_id, valid_song_ids, duplicates=True)
            return True

        except Exception as e:
            if retry_count < self.max_retries:
                logger.warning(f"Retrying adding songs to playlist {playlist_id} after error: {e}")
                await asyncio.sleep(self.retry_delay * (retry_count + 1))
                return await self.add_songs_to_playlist(playlist_id, song_ids, retry_count + 1)
            
            logger.error(f"Failed to add songs to playlist {playlist_id}: {e}")
            return False


    async def search_song(self, song_name: str, artists: List[str], retry_count: int = 0) -> Optional[str]:
        """Search for a song with retry logic and similarity checking"""
        logger.info(f"Searching for {song_name}")
        if not song_name:
            return None

        search_query = f"{song_name} {' '.join(artists)}"
        try:
            results = self.yt.search(search_query, filter="songs")
            # return results
            if not results:
                return None

            # Check similarity of song name and artist
            best_match = None
            highest_similarity = 0
            # logging.info(f"results are {results}")

            for result in results[:3]:  # Check top 3 results
                name_similarity = SequenceMatcher(None, song_name.lower(), 
                                               result['title'].lower()).ratio()
                
                # Calculate artist similarity
                artist_similarities = [
                    SequenceMatcher(None, artist.lower(), 
                                  result_artist['name'].lower()).ratio() 
                    for artist in artists 
                    for result_artist in result['artists']
                ]
                artist_similarity = max(artist_similarities) if artist_similarities else 0
                
                combined_similarity = (name_similarity + artist_similarity) / 2
                if combined_similarity > highest_similarity:
                    highest_similarity = combined_similarity
                    best_match = result

            if highest_similarity > 0.6:  # Threshold for accepting a match
                return best_match["videoId"]
            
            return None

        except Exception as e:
            if retry_count < self.max_retries:
                logger.warning(f"Retrying search for {search_query} after error: {e}")
                await asyncio.sleep(self.retry_delay * (retry_count + 1))
                return await self.search_song(song_name, artists, retry_count + 1)
            
            logger.error(f"Failed to search for {search_query}: {e}")
            return None

    async def batch_search_songs(self, songs: List[Tuple]) -> Tuple[str, str, List]:
        """Process songs in batches with rate limiting"""
        yt_songs = []
        yt_spot_mappings = []
        failed_songs = []

        for i in range(0, len(songs), self.batch_size):
            batch = songs[i:i + self.batch_size]
            logger.info(f"Processing batch {i//self.batch_size + 1}/{len(songs)//self.batch_size + 1}")
            
            for song in batch:
                result = await self.search_song(song[1], song[2])
                
                if result:
                    yt_songs.append((result, song[1]))
                    yt_spot_mappings.append((song[0], result))
                else:
                    failed_songs.append(song)
                
                await asyncio.sleep(0.5)  # Rate limiting
            
            if i + self.batch_size < len(songs):
                await asyncio.sleep(2)  # Batch delay

        return yt_songs, yt_spot_mappings, failed_songs