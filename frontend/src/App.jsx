import React, { useState, useEffect } from 'react';
import { Music, Loader, Disc3, TrendingUp, Zap, LogIn, Headphones } from 'lucide-react';
import { recommendationsAPI, spotifyAPI, healthAPI } from './services/api';
import SearchBar from './components/SearchBar';
import SeedTrackSpotify from './components/SeedTrackSpotify';
import RecommendationGrid from './components/RecommendationGrid';
import './App.css';

function App() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(null); // null = checking, true/false = determined
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [loadingStatus, setLoadingStatus] = useState(null);

  // Check auth status on mount
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    setCheckingAuth(true);
    try {
      // Try to hit a protected endpoint to verify cookies exist and are valid
      const response = await fetch(`${window.location.origin}/api/v1/spotify/queue/current`, {
        credentials: 'include',
      });
      
      if (response.ok) {
        setIsAuthenticated(true);
      } else if (response.status === 401) {
        setIsAuthenticated(false);
      } else {
        // Other errors, assume not authenticated
        setIsAuthenticated(false);
      }
    } catch (err) {
      console.error('Auth check failed:', err);
      setIsAuthenticated(false);
    } finally {
      setCheckingAuth(false);
    }
  };

  const handleSpotifyLogin = () => {
    const loginUrl = `${window.location.origin}/api/v1/spotify/login`;
    window.location.href = loginUrl;
  };

  const handleSearch = async (seedSong, count, verify) => {
    setLoading(true);
    setError(null);
    setResults(null);
    setLoadingStatus('Resolving seed song on Spotify...');

    try {
      const data = await (async () => {
        // Simulate step-by-step status updates around the single async call
        setLoadingStatus('Getting AI recommendations...');
        const res = await recommendationsAPI.getRecommendationsAsync(seedSong, count, verify);
        setLoadingStatus('Verifying recommendations...');
        return res;
      })();
      setResults(data);
      setLoadingStatus('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to get recommendations';
      
      // Check if auth error
      if (err.response?.status === 401) {
        setIsAuthenticated(false);
        setError('Session expired. Please reconnect your Spotify account.');
      } else {
        setError(errorMsg);
      }
    } finally {
      setLoading(false);
      setLoadingStatus(null);
    }
  };

  const handleAddToQueue = async (trackUri) => {
    try {
      await spotifyAPI.addToQueue(trackUri);
    } catch (err) {
      if (err.response?.status === 401) {
        setIsAuthenticated(false);
      }
      console.error('Failed to add to queue:', err);
      throw err;
    }
  };

  // Loading auth state
  if (checkingAuth) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <div className="relative inline-block">
            <div className="w-24 h-24 rounded-full bg-spotify-green/20 animate-ping absolute" />
            <div className="w-24 h-24 rounded-full bg-spotify-green/10 flex items-center justify-center relative">
              <Music className="w-12 h-12 text-spotify-green animate-pulse" />
            </div>
          </div>
          <p className="text-white text-xl font-medium mt-6">Loading...</p>
        </div>
      </div>
    );
  }

  // Not authenticated - show login screen
  if (isAuthenticated === false) {
    return (
      <div className="min-h-screen bg-black">
        {/* Gradient Background */}
        <div className="fixed inset-0 bg-gradient-to-b from-spotify-green/10 via-black to-black pointer-events-none" />
        
        <div className="relative min-h-screen flex flex-col items-center justify-center px-4 sm:px-6">
          <div className="max-w-md w-full text-center space-y-8">
            {/* Logo */}
            <div className="inline-flex items-center justify-center w-24 h-24 sm:w-32 sm:h-32 bg-gradient-to-br from-spotify-green/30 to-green-600/20 rounded-full relative">
              <div className="absolute inset-0 bg-spotify-green/20 rounded-full animate-ping" />
              <Headphones className="w-12 h-12 sm:w-16 sm:h-16 text-spotify-green relative z-10" />
            </div>

            {/* Title */}
            <div className="space-y-3">
              <h1 className="text-4xl sm:text-5xl font-bold text-white tracking-tight">
                Discover
              </h1>
              <p className="text-lg sm:text-xl text-gray-400">
                AI-powered music recommendations
              </p>
            </div>

            {/* Login Card */}
            <div className="bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6 sm:p-8 space-y-6">
              <div className="space-y-3">
                <h2 className="text-xl sm:text-2xl font-bold text-white">
                  Connect with Spotify
                </h2>
                <p className="text-sm sm:text-base text-gray-300 leading-relaxed">
                  To get personalized AI recommendations and add songs to your queue, connect your Spotify account.
                </p>
              </div>

              <button
                onClick={handleSpotifyLogin}
                className="w-full px-6 py-4 bg-spotify-green hover:bg-green-400 text-black font-bold rounded-xl transition-all hover:scale-105 active:scale-95 flex items-center justify-center gap-3 shadow-lg shadow-spotify-green/30 text-base sm:text-lg"
              >
                <LogIn className="w-5 h-5 sm:w-6 sm:h-6" />
                <span>Connect Spotify Account</span>
              </button>

              <div className="pt-4 border-t border-white/10">
                <div className="flex items-start gap-3 text-left">
                  <Zap className="w-5 h-5 text-spotify-green flex-shrink-0 mt-0.5" />
                  <div className="space-y-2">
                    <p className="text-xs sm:text-sm text-gray-400">
                      <strong className="text-white">Why connect?</strong>
                    </p>
                    <ul className="text-xs sm:text-sm text-gray-400 space-y-1">
                      <li>• Get AI-powered song recommendations</li>
                      <li>• Automatically add songs to your Spotify queue</li>
                      <li>• Personalized based on your music taste</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer note */}
            <p className="text-xs sm:text-sm text-gray-500">
              Powered by Google Gemini AI & Spotify
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Authenticated - show main app
  return (
    <div className="min-h-screen bg-black">
      {/* Gradient Background */}
      <div className="fixed inset-0 bg-gradient-to-b from-spotify-green/10 via-black to-black pointer-events-none" />
      
      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-black/40 border-b border-white/5">
        <div className="container mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3 sm:gap-4">
              <div className="flex items-center justify-center w-10 h-10 sm:w-12 sm:h-12 bg-spotify-green rounded-full shadow-lg shadow-spotify-green/50">
                <Music className="w-5 h-5 sm:w-6 sm:h-6 text-black" />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">Discover</h1>
                <p className="text-xs sm:text-sm text-gray-400 hidden sm:block">AI-powered music recommendations</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative container mx-auto px-4 sm:px-6 py-6 sm:py-8 max-w-7xl">
        {/* Search Section */}
        <div className="mb-8 sm:mb-12">
          <SearchBar onSearch={handleSearch} loading={loading} />
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 sm:mb-8 p-4 sm:p-6 bg-red-500/10 border border-red-500/20 rounded-xl sm:rounded-2xl backdrop-blur-sm">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-red-500/20 flex items-center justify-center flex-shrink-0">
                <Zap className="w-4 h-4 sm:w-5 sm:h-5 text-red-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-red-400 font-semibold text-base sm:text-lg">Something went wrong</h3>
                <p className="text-red-300/80 text-sm sm:text-base mt-1">{error}</p>
                {error.includes("No active device") && (
                  <div className="mt-3 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                    <p className="text-yellow-300 text-xs sm:text-sm">
                      💡 <strong>Tip:</strong> Make sure Spotify is open and playing music on your device. 
                      The app needs an active Spotify session to add songs to your queue.
                    </p>
                  </div>
                )}
                {error.includes("Session expired") && (
                  <button
                    onClick={handleSpotifyLogin}
                    className="mt-3 px-4 py-2 bg-spotify-green hover:bg-green-400 text-black font-semibold rounded-lg transition-all text-sm"
                  >
                    Reconnect Spotify
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-16 sm:py-24">
            <div className="relative">
              <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-full bg-spotify-green/20 animate-ping absolute" />
              <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-full bg-spotify-green/10 flex items-center justify-center relative">
                <Disc3 className="w-10 h-10 sm:w-12 sm:h-12 text-spotify-green animate-spin" />
              </div>
            </div>
            <p className="text-white text-lg sm:text-xl font-medium mt-6 sm:mt-8">{loadingStatus || 'Working...'}</p>
            <p className="text-gray-400 text-sm sm:text-base mt-2">This can take a few seconds</p>
          </div>
        )}

        {/* Results */}
        {results && !loading && (
          <div className="space-y-6 sm:space-y-8 animate-fade-in">
            {/* Seed Track */}
            <SeedTrackSpotify track={results.seed_track} />

            {/* Stats Bar */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
              <div className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 backdrop-blur-sm rounded-lg sm:rounded-2xl p-3 sm:p-6 border border-white/5 hover:border-blue-500/30 transition-all">
                <div className="flex flex-col sm:flex-row items-center gap-2 sm:gap-4">
                  <div className="w-8 h-8 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl bg-blue-500/20 flex items-center justify-center">
                    <TrendingUp className="w-4 h-4 sm:w-6 sm:h-6 text-blue-400" />
                  </div>
                  <div className="text-center sm:text-left">
                    <p className="text-xl sm:text-3xl font-bold text-white">{results.total_found}</p>
                    <p className="text-xs sm:text-sm text-gray-400">Tracks</p>
                  </div>
                </div>
              </div>

              <div className="bg-gradient-to-br from-green-500/10 to-green-600/5 backdrop-blur-sm rounded-lg sm:rounded-2xl p-3 sm:p-6 border border-white/5 hover:border-green-500/30 transition-all">
                <div className="flex flex-col sm:flex-row items-center gap-2 sm:gap-4">
                  <div className="w-8 h-8 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl bg-green-500/20 flex items-center justify-center">
                    <Zap className="w-4 h-4 sm:w-6 sm:h-6 text-green-400" />
                  </div>
                  <div className="text-center sm:text-left">
                    <p className="text-xl sm:text-3xl font-bold text-white">{results.total_verified}</p>
                    <p className="text-xs sm:text-sm text-gray-400">Verified</p>
                  </div>
                </div>
              </div>

              <div className="bg-gradient-to-br from-purple-500/10 to-purple-600/5 backdrop-blur-sm rounded-lg sm:rounded-2xl p-3 sm:p-6 border border-white/5 hover:border-purple-500/30 transition-all">
                <div className="flex flex-col sm:flex-row items-center gap-2 sm:gap-4">
                  <div className="w-8 h-8 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl bg-purple-500/20 flex items-center justify-center">
                    <Music className="w-4 h-4 sm:w-6 sm:h-6 text-purple-400" />
                  </div>
                  <div className="text-center sm:text-left">
                    <p className="text-xl sm:text-3xl font-bold text-white">
                      {results.total_verified > 0 ? Math.round((results.total_verified / (results.total_verified + results.total_rejected)) * 100) : 0}%
                    </p>
                    <p className="text-xs sm:text-sm text-gray-400">Match</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Recommendations Grid */}
            <div>
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-3 mb-4 sm:mb-6">
                <h2 className="text-2xl sm:text-3xl font-bold text-white">Recommended for you</h2>
                <div className="px-3 py-1 rounded-full bg-spotify-green/20 border border-spotify-green/30">
                  <span className="text-xs sm:text-sm font-medium text-spotify-green">{results.recommendations.length} tracks</span>
                </div>
              </div>
              <RecommendationGrid 
                recommendations={results.recommendations}
                onAddToQueue={handleAddToQueue}
              />
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && !results && !error && (
          <div className="text-center py-16 sm:py-24 px-4">
            <div className="inline-flex items-center justify-center w-24 h-24 sm:w-32 sm:h-32 bg-gradient-to-br from-spotify-green/20 to-green-600/10 rounded-full mb-6 sm:mb-8 relative">
              <div className="absolute inset-0 bg-spotify-green/20 rounded-full animate-ping" />
              <Music className="w-12 h-12 sm:w-16 sm:h-16 text-spotify-green relative z-10" />
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-3 sm:mb-4">Your personal DJ</h2>
            <p className="text-gray-400 text-base sm:text-lg max-w-2xl mx-auto leading-relaxed">
              Powered by AI to find songs that match your vibe, energy, and mood.
              Enter any song above and let the magic happen.
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="relative mt-16 sm:mt-24 border-t border-white/5 backdrop-blur-xl bg-black/40">
        <div className="container mx-auto px-4 sm:px-6 py-6 sm:py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-3 sm:gap-4">
            <div className="flex items-center gap-2 sm:gap-3">
              <div className="w-6 h-6 sm:w-8 sm:h-8 bg-spotify-green rounded-full flex items-center justify-center">
                <Music className="w-3 h-3 sm:w-4 sm:h-4 text-black" />
              </div>
              <p className="text-gray-400 text-xs sm:text-sm">Powered by Google Gemini AI & Spotify</p>
            </div>
            <p className="text-gray-500 text-xs sm:text-sm">© 2024 Music Recommendation System</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
