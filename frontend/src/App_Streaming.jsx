import React from 'react';
import { Music, Disc3, TrendingUp, Zap, CheckCircle, Radio } from 'lucide-react';
import { useStreamingRecommendations } from './hooks/useStreamingRecommendations';
import SearchBar from './components/SearchBar';
import RecommendationGrid from './components/RecommendationGrid';
import './App.css';

function App() {
  const {
    loading,
    seedTrack,
    recommendations,
    error,
    status,
    queuedCount,
    streamRecommendations,
  } = useStreamingRecommendations();

  const handleSearch = async (seedSong, count) => {
    await streamRecommendations(seedSong, count);
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
              <p className="text-sm text-gray-400">AI-powered music recommendations with auto-queue</p>
            </div>
            
            {queuedCount > 0 && (
              <div className="ml-auto flex items-center gap-2 px-4 py-2 bg-spotify-green/20 rounded-full border border-spotify-green/30">
                <CheckCircle className="w-5 h-5 text-spotify-green" />
                <span className="text-sm font-bold text-spotify-green">{queuedCount} in queue</span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative container mx-auto px-6 py-8 max-w-7xl">
        {/* Search Section */}
        <div className="mb-12">
          <SearchBar onSearch={handleSearch} loading={loading} />
        </div>

        {/* Status Bar */}
        {loading && status && (
          <div className="mb-8 p-4 bg-spotify-green/10 border border-spotify-green/20 rounded-2xl backdrop-blur-sm flex items-center gap-3">
            <Radio className="w-5 h-5 text-spotify-green animate-pulse" />
            <p className="text-spotify-green font-medium">{status}</p>
          </div>
        )}

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
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && !recommendations.length && (
          <div className="flex flex-col items-center justify-center py-24">
            <div className="relative">
              <div className="w-24 h-24 rounded-full bg-spotify-green/20 animate-ping absolute" />
              <div className="w-24 h-24 rounded-full bg-spotify-green/10 flex items-center justify-center relative">
                <Disc3 className="w-12 h-12 text-spotify-green animate-spin" />
              </div>
            </div>
            <p className="text-white text-xl font-medium mt-8">Analyzing your taste...</p>
            <p className="text-gray-400 text-sm mt-2">Finding perfect matches & adding to queue</p>
          </div>
        )}

        {/* Results */}
        {(seedTrack || recommendations.length > 0) && (
          <div className="space-y-8 animate-fade-in">
            {/* Seed Track */}
            {seedTrack && (
              <div className="p-6 bg-gradient-to-br from-spotify-green/20 via-green-600/10 to-black border border-spotify-green/30 rounded-2xl">
                <div className="flex items-center gap-3 mb-2">
                  <div className="px-3 py-1 rounded-full bg-spotify-green/20 border border-spotify-green/40">
                    <span className="text-xs font-semibold text-spotify-green uppercase tracking-wider">Seed Track</span>
                  </div>
                </div>
                <h2 className="text-3xl font-bold text-white mb-2">{seedTrack.name}</h2>
                <p className="text-xl text-gray-300">{seedTrack.artists}</p>
              </div>
            )}

            {/* Stats Bar */}
            {recommendations.length > 0 && (
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 backdrop-blur-sm rounded-2xl p-6 border border-white/5 hover:border-blue-500/30 transition-all">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center">
                      <TrendingUp className="w-6 h-6 text-blue-400" />
                    </div>
                    <div>
                      <p className="text-3xl font-bold text-white">{recommendations.length}</p>
                      <p className="text-sm text-gray-400">Tracks Found</p>
                    </div>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-green-500/10 to-green-600/5 backdrop-blur-sm rounded-2xl p-6 border border-white/5 hover:border-green-500/30 transition-all">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-green-500/20 flex items-center justify-center">
                      <CheckCircle className="w-6 h-6 text-green-400" />
                    </div>
                    <div>
                      <p className="text-3xl font-bold text-white">{queuedCount}</p>
                      <p className="text-sm text-gray-400">Added to Queue</p>
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
                        {recommendations.length > 0 ? Math.round((queuedCount / recommendations.length) * 100) : 0}%
                      </p>
                      <p className="text-sm text-gray-400">Queue Rate</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Recommendations Grid */}
            {recommendations.length > 0 && (
              <div>
                <div className="flex items-center gap-3 mb-6">
                  <h2 className="text-3xl font-bold text-white">Auto-Queued Tracks</h2>
                  <div className="px-3 py-1 rounded-full bg-spotify-green/20 border border-spotify-green/30">
                    <span className="text-sm font-medium text-spotify-green">{recommendations.length} tracks</span>
                  </div>
                </div>
                <RecommendationGrid recommendations={recommendations} hideQueueButtons={true} />
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {!loading && !seedTrack && !recommendations.length && !error && (
          <div className="text-center py-24">
            <div className="inline-flex items-center justify-center w-32 h-32 bg-gradient-to-br from-spotify-green/20 to-green-600/10 rounded-full mb-8 relative">
              <div className="absolute inset-0 bg-spotify-green/20 rounded-full animate-ping" />
              <Music className="w-16 h-16 text-spotify-green relative z-10" />
            </div>
            <h2 className="text-4xl font-bold text-white mb-4">Your personal DJ</h2>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto leading-relaxed">
              Powered by AI to find songs that match your vibe, energy, and mood.
              <br />
              <span className="text-spotify-green font-semibold">Songs automatically add to your Spotify queue!</span>
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
              <p className="text-gray-400 text-sm">Streaming with Google Gemini AI & Spotify Auto-Queue</p>
            </div>
            <p className="text-gray-500 text-sm">© 2024 Music Recommendation System</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;


