# 🎵 Spotify Music Recommendation System

An intelligent music recommendation system powered by **Google's Gemini AI** that suggests similar songs and automatically adds them to your Spotify queue.

## ✨ Features

- 🤖 **AI-Powered Recommendations**: Uses Gemini AI to suggest songs based on musical similarity, mood, and style
- ✅ **AI Verification**: Second Gemini agent validates recommendations for genre, artist, energy, and cultural context match
- 🎧 **Spotify Integration**: Seamlessly adds recommended songs to your Spotify queue
- 🎨 **Beautiful CLI Interface**: Rich terminal UI with progress indicators and formatted tables
- 🔄 **Auto-Retry Logic**: Robust error handling with automatic retries for API calls
- 📊 **Detailed Information**: Shows artist names, genres, and reasons for each recommendation
- 🧠 **Fuzzy Matching**: Intelligent song resolution even with slight title/artist variations
- 🎮 **Autoplay Support**: Optionally start playback automatically
- 🧪 **Dry Run Mode**: Preview recommendations without modifying your queue

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Spotify Premium account (required for playback control)
- Google API key for Gemini
- Spotify Developer credentials

### Installation

1. **Clone the repository**:
```bash
cd spotify_recommendation
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**:
```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
- `GOOGLE_API_KEY`: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- `SPOTIPY_CLIENT_ID` & `SPOTIPY_CLIENT_SECRET`: Create an app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- `SPOTIPY_REDIRECT_URI`: Set to `http://localhost:8888/callback` (must match your Spotify app settings)

### Getting API Credentials

#### Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key to your `.env` file

#### Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click "Create app"
4. Fill in the details:
   - **App name**: Spotify Recommendation System
   - **App description**: AI-powered music recommendations
   - **Redirect URI**: `http://localhost:8888/callback`
5. Copy the **Client ID** and **Client Secret** to your `.env` file

## 📖 Usage

### Basic Usage

Run the program and enter a song name when prompted:

```bash
python main.py
```

### Specify a Song Directly

```bash
python main.py --song "Bohemian Rhapsody"
```

### Get More Recommendations

```bash
python main.py --song "Shape of You" --count 10
```

### Dry Run (Preview Only)

Preview recommendations without adding them to your queue:

```bash
python main.py --song "Blinding Lights" --dry-run
```

### Auto-Play Mode

Automatically start playback of the seed song:

```bash
python main.py --song "Starboy" --autoplay
```

### Verbose Logging

Enable detailed logging for debugging:

```bash
python main.py --song "Levitating" --verbose
```

### Disable AI Verification

Skip the verification step (faster but may include irrelevant songs):

```bash
python main.py --song "Starboy" --no-verify
```

## 🎯 How It Works

1. **Input**: You provide a seed song name (e.g., "Lahore by Guru Randhawa")
2. **Spotify Resolution**: The system finds the exact track on Spotify and extracts metadata (artist, genre)
3. **AI Analysis**: Gemini AI receives the verified song details and suggests similar tracks based on:
   - Artist style and vocal characteristics
   - Genre and cultural context
   - Energy, rhythm, and production quality
4. **AI Verification** (enabled by default): A second Gemini agent validates each recommendation:
   - Artist Match (30%): Same artist or closely related artists
   - Genre/Culture Match (30%): Same genre and cultural context
   - Energy/Vibe Match (20%): Similar tempo, energy, mood
   - Popularity/Quality (10%): Well-known, high-quality tracks
   - Sonic Coherence (10%): Flows well in a playlist
5. **Fuzzy Matching**: The system uses intelligent fuzzy matching to find recommended songs on Spotify
6. **Queue Management**: Only verified, valid tracks are added to your Spotify queue
7. **Playback**: Optionally starts playback on your active device

## 🎨 Example Output

```
╭─────────────────────────────────────────────╮
│ 🎵 Spotify Music Recommendation System     │
│ Powered by Gemini AI                        │
╰─────────────────────────────────────────────╯

Seed Song: Blinding Lights

✓ Found: Blinding Lights by The Weeknd
✓ Received 5 suggestions from Gemini
✓ Resolved 5/5 tracks on Spotify

🎵 Recommended Songs
┏━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ # ┃ Song                       ┃ Artist(s)            ┃ Genre        ┃ Reason             ┃
┡━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ 1 │ Save Your Tears            │ The Weeknd           │ Synth-pop    │ Similar 80s vibe   │
│ 2 │ I Feel It Coming           │ The Weeknd, Daft ... │ Synth-pop    │ Smooth synth beats │
│ 3 │ Starboy                    │ The Weeknd, Daft ... │ Pop          │ Same artist style  │
│ 4 │ Levitating                 │ Dua Lipa             │ Disco-pop    │ Upbeat dance track │
│ 5 │ Don't Start Now            │ Dua Lipa             │ Disco-pop    │ Energetic pop song │
└───┴────────────────────────────┴──────────────────────┴──────────────┴────────────────────┘

✓ Successfully added 5/5 songs to queue

ℹ Songs added to queue. Start playback on your Spotify device.

Done! Enjoy your music! 🎶
```

## 🛠️ Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--song SONG` | Seed song title (prompted if not provided) | None |
| `--count N` | Number of recommendations to request | 5 |
| `--dry-run` | Preview recommendations without modifying queue | False |
| `--autoplay` | Automatically start playback | False |
| `--verify` | Enable AI verification of recommendations | True |
| `--no-verify` | Disable AI verification (faster, less accurate) | False |
| `--redirect-uri URI` | Override redirect URI for Spotify OAuth | From .env |
| `--verbose, -v` | Enable verbose logging | False |

## 🔧 Advanced Configuration

### Custom Gemini Model

Edit `main.py` and change the model name in the `GeminiAgent` initialization:

```python
gemini = GeminiAgent(google_key, model_name="gemini-1.5-pro")
```

### Adjust Generation Parameters

Modify the `generation_config` in the `GeminiAgent.__init__` method:

```python
generation_config={
    "temperature": 0.6,  # Higher = more creative
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
}
```

## 🐛 Troubleshooting

### "No active Spotify device found"

Make sure you have Spotify open and playing on at least one device (computer, phone, etc.)

### "Missing required environment variable"

Ensure your `.env` file exists and contains all required variables

### "Could not resolve seed song on Spotify"

Try using the full song name or including the artist name

### Authentication Issues

Delete the `.cache-spotify` file and run the program again to re-authenticate

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## 🎵 Enjoy!

Happy listening! If you find this useful, consider starring the repository.


