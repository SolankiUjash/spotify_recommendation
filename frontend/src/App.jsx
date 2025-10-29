import React, { useState } from 'react';
import { Music, Loader, Disc3, TrendingUp, Zap } from 'lucide-react';
import { recommendationsAPI, spotifyAPI } from './services/api';
import SearchBar from './components/SearchBar';
import SeedTrackSpotify from './components/SeedTrackSpotify';
import RecommendationGrid from './components/RecommendationGrid';
import './App.css';

function App() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleSearch = async (seedSong, count, verify) => {
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const data = await recommendationsAPI.getRecommendationsAsync(seedSong, count, verify);
      setResults(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to get recommendations');
    } finally {
      setLoading(false);
    }
  };

  const handleAddToQueue = async (trackUri) => {
    try {
      await spotifyAPI.addToQueue(trackUri);
    } catch (err) {
      console.error('Failed to add to queue:', err);
      throw err;
    }
  };

  const handleRemoveFromQueue = async (trackUri) => {
    try {
      await spotifyAPI.removeFromQueue(trackUri);
    } catch (err) {
      console.error('Failed to remove from queue:', err);
      throw err;
    }
  };

  return (
    <div className="min-h-screen bg-black">
      {/* Gradient Background */}
      <div className="fixed inset-0 bg-gradient-to-b from-spotify-green/10 via-black to-black pointer-events-none" />
      
      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-black/40 border-b border-white/5">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center justify-center w-12 h-12 bg-spotify-green rounded-full shadow-lg shadow-spotify-green/50">
              <Music className="w-6 h-6 text-black" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Discover</h1>
              <p className="text-sm text-gray-400">AI-powered music recommendations</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative container mx-auto px-6 py-8 max-w-7xl">
        {/* Search Section */}
        <div className="mb-12">
          <SearchBar onSearch={handleSearch} loading={loading} />
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-8 p-6 bg-red-500/10 border border-red-500/20 rounded-2xl backdrop-blur-sm">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center flex-shrink-0">
                <Zap className="w-5 h-5 text-red-400" />
              </div>
              <div>
                <h3 className="text-red-400 font-semibold text-lg">Something went wrong</h3>
                <p className="text-red-300/80 text-sm mt-1">{error}</p>
                {error.includes("No active device") && (
                  <div className="mt-3 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                    <p className="text-yellow-300 text-sm">
                      💡 <strong>Tip:</strong> Make sure Spotify is open and playing music on your device. 
                      The app needs an active Spotify session to add songs to your queue.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-24">
            <div className="relative">
              <div className="w-24 h-24 rounded-full bg-spotify-green/20 animate-ping absolute" />
              <div className="w-24 h-24 rounded-full bg-spotify-green/10 flex items-center justify-center relative">
                <Disc3 className="w-12 h-12 text-spotify-green animate-spin" />
              </div>
            </div>
            <p className="text-white text-xl font-medium mt-8">Analyzing your taste...</p>
            <p className="text-gray-400 text-sm mt-2">Finding perfect matches with AI</p>
          </div>
        )}

        {/* Results */}
        {results && !loading && (
          <div className="space-y-8 animate-fade-in">
            {/* Seed Track */}
            <SeedTrackSpotify track={results.seed_track} />

            {/* Stats Bar */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 backdrop-blur-sm rounded-2xl p-6 border border-white/5 hover:border-blue-500/30 transition-all">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-blue-400" />
                  </div>
                  <div>
                    <p className="text-3xl font-bold text-white">{results.total_found}</p>
                    <p className="text-sm text-gray-400">Tracks Found</p>
                  </div>
                </div>
              </div>

              <div className="bg-gradient-to-br from-green-500/10 to-green-600/5 backdrop-blur-sm rounded-2xl p-6 border border-white/5 hover:border-green-500/30 transition-all">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-green-500/20 flex items-center justify-center">
                    <Zap className="w-6 h-6 text-green-400" />
                  </div>
                  <div>
                    <p className="text-3xl font-bold text-white">{results.total_verified}</p>
                    <p className="text-sm text-gray-400">AI Verified</p>
                  </div>
                </div>
              </div>

              <div className="bg-gradient-to-br from-purple-500/10 to-purple-600/5 backdrop-blur-sm rounded-2xl p-6 border border-white/5 hover:border-purple-500/30 transition-all">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center">
                    <Music className="w-6 h-6 text-purple-400" />
                  </div>
                  <div>
                    <p className="text-3xl font-bold text-white">
                      {results.total_verified > 0 ? Math.round((results.total_verified / (results.total_verified + results.total_rejected)) * 100) : 0}%
                    </p>
                    <p className="text-sm text-gray-400">Match Rate</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Recommendations Grid */}
            <div>
              <div className="flex items-center gap-3 mb-6">
                <h2 className="text-3xl font-bold text-white">Recommended for you</h2>
                <div className="px-3 py-1 rounded-full bg-spotify-green/20 border border-spotify-green/30">
                  <span className="text-sm font-medium text-spotify-green">{results.recommendations.length} tracks</span>
                </div>
              </div>
              <RecommendationGrid 
                recommendations={results.recommendations}
                onAddToQueue={handleAddToQueue}
                onRemoveFromQueue={handleRemoveFromQueue}
              />
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && !results && !error && (
          <div className="text-center py-24">
            <div className="inline-flex items-center justify-center w-32 h-32 bg-gradient-to-br from-spotify-green/20 to-green-600/10 rounded-full mb-8 relative">
              <div className="absolute inset-0 bg-spotify-green/20 rounded-full animate-ping" />
              <Music className="w-16 h-16 text-spotify-green relative z-10" />
            </div>
            <h2 className="text-4xl font-bold text-white mb-4">Your personal DJ</h2>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto leading-relaxed">
              Powered by AI to find songs that match your vibe, energy, and mood.
              Enter any song above and let the magic happen.
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="relative mt-24 border-t border-white/5 backdrop-blur-xl bg-black/40">
        <div className="container mx-auto px-6 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-spotify-green rounded-full flex items-center justify-center">
                <Music className="w-4 h-4 text-black" />
              </div>
              <p className="text-gray-400 text-sm">Powered by Google Gemini AI & Spotify</p>
            </div>
            <p className="text-gray-500 text-sm">© 2024 Music Recommendation System</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
