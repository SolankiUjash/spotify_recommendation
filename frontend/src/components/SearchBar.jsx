import React, { useState } from 'react';
import { Search, Settings, Sparkles, Shield } from 'lucide-react';

const SearchBar = ({ onSearch, loading }) => {
  const [seedSong, setSeedSong] = useState('');
  const [count, setCount] = useState(10);
  const [verify, setVerify] = useState(true);
  const [showSettings, setShowSettings] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (seedSong.trim()) {
      onSearch(seedSong, count, verify);
    }
  };

  return (
    <div className="relative">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Main Search Bar */}
        <div className="relative group">
          <div className="absolute inset-0 bg-gradient-to-r from-spotify-green/30 via-green-500/20 to-spotify-green/30 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          
          <div className="relative flex items-center gap-3 bg-gradient-to-r from-white/10 to-white/5 backdrop-blur-xl rounded-2xl border border-white/10 group-hover:border-spotify-green/50 focus-within:border-spotify-green/50 transition-all duration-300 p-2">
            <div className="flex items-center justify-center w-12 h-12 bg-spotify-green/20 rounded-xl flex-shrink-0 ml-2">
              <Search className="w-5 h-5 text-spotify-green" />
            </div>
            
            <input
              type="text"
              value={seedSong}
              onChange={(e) => setSeedSong(e.target.value)}
              placeholder="Search for a song... (e.g., 'Starboy by The Weeknd')"
              className="flex-1 bg-transparent text-white placeholder-gray-400 outline-none focus:outline-none focus:ring-0 text-lg py-3 px-2"
              disabled={loading}
            />

            <button
              type="button"
              onClick={() => setShowSettings(!showSettings)}
              className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all hover:scale-105 active:scale-95 ${
                showSettings 
                  ? 'bg-spotify-green text-black' 
                  : 'bg-white/10 text-gray-400 hover:bg-white/20 hover:text-white'
              }`}
            >
              <Settings className={`w-5 h-5 ${showSettings ? 'animate-spin-slow' : ''}`} />
            </button>

            <button
              type="submit"
              disabled={loading || !seedSong.trim()}
              className="px-8 py-3 bg-spotify-green hover:bg-green-400 disabled:bg-gray-700 disabled:text-gray-500 rounded-xl font-bold text-black transition-all hover:scale-105 active:scale-95 disabled:cursor-not-allowed disabled:hover:scale-100 shadow-lg shadow-spotify-green/30 disabled:shadow-none flex items-center gap-2 mr-2"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  <span>Discover</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="animate-slide-down bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Number of Recommendations */}
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-3">
                  <Sparkles className="w-4 h-4 text-spotify-green" />
                  Number of Recommendations
                </label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="1"
                    max="100"
                    value={count}
                    onChange={(e) => setCount(parseInt(e.target.value))}
                    className="flex-1 h-2 bg-white/10 rounded-full appearance-none cursor-pointer slider"
                    disabled={loading}
                  />
                  <div className="w-16 h-12 bg-white/5 rounded-xl flex items-center justify-center border border-white/10">
                    <span className="text-xl font-bold text-white">{count}</span>
                  </div>
                </div>
                <div className="flex justify-between text-xs text-gray-500 mt-2">
                  <span>1</span>
                  <span>100</span>
                </div>
              </div>

              {/* AI Verification Toggle */}
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-3">
                  <Shield className="w-4 h-4 text-spotify-green" />
                  AI Verification
                </label>
                <button
                  type="button"
                  onClick={() => setVerify(!verify)}
                  disabled={loading}
                  className={`w-full h-12 rounded-xl font-semibold transition-all hover:scale-[1.02] active:scale-95 flex items-center justify-center gap-3 ${
                    verify
                      ? 'bg-gradient-to-r from-spotify-green to-green-400 text-black shadow-lg shadow-spotify-green/30'
                      : 'bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10'
                  }`}
                >
                  <Shield className={`w-5 h-5 ${verify ? 'fill-black' : ''}`} />
                  <span>{verify ? 'Enabled' : 'Disabled'}</span>
                  {verify && <Sparkles className="w-4 h-4" />}
                </button>
                <p className="text-xs text-gray-500 mt-2">
                  {verify 
                    ? 'AI will verify each recommendation for quality and relevance' 
                    : 'Show all recommendations without AI filtering'}
                </p>
              </div>
            </div>

            {/* Info */}
            <div className="mt-6 p-4 bg-spotify-green/10 rounded-xl border border-spotify-green/20">
              <div className="flex items-start gap-3">
                <Sparkles className="w-5 h-5 text-spotify-green flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm text-gray-300 leading-relaxed">
                    <span className="font-semibold text-white">AI-Powered Recommendations:</span> Our system analyzes genre, mood, energy, and artist style to find the perfect matches for your taste.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </form>
    </div>
  );
};

export default SearchBar;
