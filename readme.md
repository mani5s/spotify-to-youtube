# Spotify to YouTube Music Playlist Transfer

This application allows users to transfer their Spotify playlists to YouTube Music. It authenticates with both services, reads playlist data from Spotify, and recreates those playlists in YouTube Music with matching songs.

## Features

- OAuth authentication with Spotify
- YouTube Music authentication 
- Playlist data extraction from Spotify API
- Intelligent song matching between platforms
- Batch processing with rate limiting
- Local SQLite database for tracking transfer progress
- Support for transferring single playlists or bulk transfers
- Web-based authentication flow

## Requirements

- Python 3.7+
- Flask
- ytmusicapi
- httpx
- dotenv

## Installation

1. Clone the repository
2. Install the requirements:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your Spotify API credentials:
   ```
   client_id=your_spotify_client_id
   client_secret=your_spotify_client_secret
   ```

## Usage

### Basic Usage

Run the main script to start the transfer process:

```
python main.py
```

This will:
1. Authenticate with Spotify (if needed)
2. Load your playlists
3. Allow you to select which playlists to transfer
4. Authenticate with YouTube Music
5. Create matching playlists in YouTube Music
6. Search for and add songs to the new playlists

### Advanced Usage

You can customize the transfer process by modifying the `main()` function in `main.py`. The application supports:

- Transferring specific playlists by URL
- Resuming transfers
- Using an existing database

## How It Works

1. **Authentication**: The app authenticates with Spotify using OAuth and with YouTube Music using browser cookies.
2. **Data Extraction**: Playlist and song data is extracted from Spotify and stored in a local SQLite database.
3. **Song Matching**: For each Spotify song, the app searches YouTube Music for the best match.
4. **Playlist Creation**: New playlists are created in YouTube Music with matching metadata.
5. **Song Addition**: Matched songs are added to the new playlists in batches to avoid rate limiting.

## File Structure

- `main.py` - Main application entry point
- `spotify_auth.py` - Spotify authentication server
- `spotify.py` - Spotify API client
- `youtube.py` - YouTube Music API client
- `database.py` - SQLite database manager
- `templates/` - HTML templates for authentication flow

## TODO

1. **YouTube auto auth** - Implement automatic authentication for YouTube Music without manual cookie capture
2. **Main function** - Improve the main script interface with better command-line options and user interaction
3. Add proper error handling for network failures
4. Implement playlist synchronization (keeping playlists updated)
5. Add support for transferring liked songs
6. Create a proper GUI
7. Add support for Apple Music
8. Implement better similarity matching for finding songs

## Troubleshooting

### Common Issues

- **Spotify Authentication Fails**: Ensure your client ID and secret are correct in the `.env` file
- **YouTube Music Authentication Fails**: You may need to manually capture cookies using the browser
- **Rate Limiting**: If you hit API rate limits, try increasing the delay between requests
- **Song Matching Issues**: Some songs may not find perfect matches - check the logs for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
