import React, { useState, useEffect, useRef } from 'react';
import { Search, Settings, Sparkles, Shield, Music, X } from 'lucide-react';
import { spotifyAPI } from '../services/api';

const SearchBar = ({ onSearch, loading }) => {
  const [seedSong, setSeedSong] = useState('');
  const [count, setCount] = useState(10);
  const [verify, setVerify] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [searching, setSearching] = useState(false);
  const [selectedTrack, setSelectedTrack] = useState(null);
  const [authRequired, setAuthRequired] = useState(false);
  const searchTimeoutRef = useRef(null);
  const dropdownRef = useRef(null);

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowResults(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounced search
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (seedSong.trim().length >= 2 && !selectedTrack) {
      setSearching(true);
      searchTimeoutRef.current = setTimeout(async () => {
        try {
          const results = await spotifyAPI.searchTracks(seedSong, 10);
          setSearchResults(results.tracks || []);
          setShowResults(true);
          setAuthRequired(false);
        } catch (error) {
          const status = error?.response?.status;
          if (status === 401) {
            setAuthRequired(true);
            setShowResults(true);
          } else {
            console.error('Search error:', error);
          }
          setSearchResults([]);
        } finally {
          setSearching(false);
        }
      }, 500);
    } else {
      setSearchResults([]);
      setShowResults(false);
      setSearching(false);
    }

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [seedSong, selectedTrack]);

  const handleSelectTrack = (track) => {
    setSelectedTrack(track);
    setSeedSong(`${track.name} - ${track.artists.join(', ')}`);
    setShowResults(false);
  };

  const handleClearSelection = () => {
    setSelectedTrack(null);
    setSeedSong('');
    setSearchResults([]);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (seedSong.trim()) {
      // Pass the actual track name or full string
      const searchQuery = selectedTrack 
        ? `${selectedTrack.name} ${selectedTrack.artists.join(' ')}`
        : seedSong;
      onSearch(searchQuery, count, verify);
      setShowResults(false);
    }
  };

  const handleConnectSpotify = async () => {
    try {
      const url = await spotifyAPI.getAuthUrl();
      window.location.href = url;
    } catch (e) {
      console.error('Failed to get Spotify auth URL', e);
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Main Search Bar */}
        <div className="relative group">
          <div className="absolute inset-0 bg-gradient-to-r from-spotify-green/30 via-green-500/20 to-spotify-green/30 rounded-xl sm:rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          
          <div className="relative flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3 bg-gradient-to-r from-white/10 to-white/5 backdrop-blur-xl rounded-xl sm:rounded-2xl border border-white/10 group-hover:border-spotify-green/50 focus-within:border-spotify-green transition-all duration-300 p-3 sm:p-2">
            {/* Mobile: Full width search */}
            <div className="flex items-center gap-3 flex-1">
              <div className="flex items-center justify-center w-10 h-10 sm:w-12 sm:h-12 bg-spotify-green/20 rounded-lg sm:rounded-xl flex-shrink-0">
                {searching ? (
                  <div className="w-4 h-4 sm:w-5 sm:h-5 border-2 border-spotify-green/30 border-t-spotify-green rounded-full animate-spin" />
                ) : (
                  <Search className="w-4 h-4 sm:w-5 sm:h-5 text-spotify-green" />
                )}
              </div>
              
              <input
                type="text"
                value={seedSong}
                onChange={(e) => {
                  setSeedSong(e.target.value);
                  setSelectedTrack(null);
                }}
                placeholder="Search for a song..."
                className="flex-1 bg-transparent text-white placeholder-gray-400 outline-none focus:outline-none focus:ring-0 text-base sm:text-lg py-2 sm:py-3 px-1"
                disabled={loading}
              />

              {selectedTrack && (
                <button
                  type="button"
                  onClick={handleClearSelection}
                  className="flex-shrink-0 p-1 hover:bg-white/10 rounded-lg transition-colors"
                >
                  <X className="w-4 h-4 text-gray-400 hover:text-white" />
                </button>
              )}
            </div>

            {/* Mobile: Buttons row */}
            <div className="flex items-center gap-2 sm:gap-3">
              <button
                type="button"
                onClick={() => setShowSettings(!showSettings)}
                className={`w-10 h-10 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl flex items-center justify-center transition-all hover:scale-105 active:scale-95 flex-shrink-0 ${
                  showSettings 
                    ? 'bg-spotify-green text-black' 
                    : 'bg-white/10 text-gray-400 hover:bg-white/20 hover:text-white'
                }`}
              >
                <Settings className={`w-4 h-4 sm:w-5 sm:h-5 ${showSettings ? 'animate-spin-slow' : ''}`} />
              </button>

              <button
                type="submit"
                disabled={loading || !seedSong.trim()}
                className="flex-1 sm:flex-none px-6 sm:px-8 py-2.5 sm:py-3 bg-spotify-green hover:bg-green-400 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg sm:rounded-xl font-bold text-black transition-all hover:scale-105 active:scale-95 disabled:cursor-not-allowed disabled:hover:scale-100 shadow-lg shadow-spotify-green/30 disabled:shadow-none flex items-center justify-center gap-2 text-sm sm:text-base"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 sm:w-5 sm:h-5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                    <span className="hidden sm:inline">Analyzing...</span>
                    <span className="sm:hidden">Wait...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 sm:w-5 sm:h-5" />
                    <span>Discover</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Search Results Dropdown */}
          {showResults && (
            <div className="absolute z-50 w-full mt-2 bg-gray-900/95 backdrop-blur-xl rounded-xl border border-white/10 shadow-2xl max-h-96 overflow-y-auto animate-slide-down">
              {authRequired && (
                <div className="p-4 border-b border-white/10">
                  <p className="text-sm text-gray-300 mb-3">Connect to Spotify to search tracks.</p>
                  <button
                    type="button"
                    onClick={handleConnectSpotify}
                    className="w-full px-4 py-2 bg-spotify-green hover:bg-green-400 text-black font-semibold rounded-lg transition-colors"
                  >
                    Connect Spotify
                  </button>
                </div>
              )}

              {searchResults.length === 0 && !authRequired && !searching && (
                <div className="p-4 text-sm text-gray-400">No results</div>
              )}

              {searchResults.map((track, index) => (
                <button
                  key={track.id}
                  type="button"
                  onClick={() => handleSelectTrack(track)}
                  className="w-full flex items-center gap-3 p-3 hover:bg-white/10 transition-colors border-b border-white/5 last:border-0"
                >
                  {track.image_url ? (
                    <img 
                      src={track.image_url} 
                      alt={track.name}
                      className="w-12 h-12 rounded-lg flex-shrink-0"
                    />
                  ) : (
                    <div className="w-12 h-12 rounded-lg bg-white/5 flex items-center justify-center flex-shrink-0">
                      <Music className="w-6 h-6 text-gray-400" />
                    </div>
                  )}
                  <div className="flex-1 text-left min-w-0">
                    <div className="text-white font-medium truncate">{track.name}</div>
                    <div className="text-sm text-gray-400 truncate">{track.artists.join(', ')}</div>
                  </div>
                  <div className="flex-shrink-0">
                    <Sparkles className="w-4 h-4 text-spotify-green" />
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="animate-slide-down bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl rounded-xl sm:rounded-2xl border border-white/10 p-4 sm:p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
              {/* Number of Recommendations */}
              <div>
                <label className="flex items-center gap-2 text-xs sm:text-sm font-medium text-gray-300 mb-3">
                  <Sparkles className="w-3 h-3 sm:w-4 sm:h-4 text-spotify-green" />
                  Number of Recommendations
                </label>
                <div className="flex items-center gap-3 sm:gap-4">
                  <input
                    type="range"
                    min="1"
                    max="100"
                    value={count}
                    onChange={(e) => setCount(parseInt(e.target.value))}
                    className="flex-1 h-2 bg-white/10 rounded-full appearance-none cursor-pointer slider"
                    disabled={loading}
                  />
                  <div className="w-14 h-10 sm:w-16 sm:h-12 bg-white/5 rounded-lg sm:rounded-xl flex items-center justify-center border border-white/10">
                    <span className="text-lg sm:text-xl font-bold text-white">{count}</span>
                  </div>
                </div>
                <div className="flex justify-between text-xs text-gray-500 mt-2">
                  <span>1</span>
                  <span>100</span>
                </div>
              </div>

              {/* AI Verification Toggle */}
              <div>
                <label className="flex items-center gap-2 text-xs sm:text-sm font-medium text-gray-300 mb-3">
                  <Shield className="w-3 h-3 sm:w-4 sm:h-4 text-spotify-green" />
                  AI Verification
                </label>
                <button
                  type="button"
                  onClick={() => setVerify(!verify)}
                  disabled={loading}
                  className={`w-full h-10 sm:h-12 rounded-lg sm:rounded-xl font-semibold transition-all hover:scale-[1.02] active:scale-95 flex items-center justify-center gap-2 sm:gap-3 text-sm sm:text-base ${
                    verify
                      ? 'bg-gradient-to-r from-spotify-green to-green-400 text-black shadow-lg shadow-spotify-green/30'
                      : 'bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10'
                  }`}
                >
                  <Shield className={`w-4 h-4 sm:w-5 sm:h-5 ${verify ? 'fill-black' : ''}`} />
                  <span>{verify ? 'Enabled' : 'Disabled'}</span>
                  {verify && <Sparkles className="w-3 h-3 sm:w-4 sm:h-4" />}
                </button>
                <p className="text-xs text-gray-500 mt-2">
                  {verify 
                    ? 'AI will verify each recommendation for quality and relevance' 
                    : 'Show all recommendations without AI filtering'}
                </p>
              </div>

              
            </div>

            {/* Info */}
            <div className="mt-4 sm:mt-6 p-3 sm:p-4 bg-spotify-green/10 rounded-lg sm:rounded-xl border border-spotify-green/20">
              <div className="flex items-start gap-2 sm:gap-3">
                <Sparkles className="w-4 h-4 sm:w-5 sm:h-5 text-spotify-green flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs sm:text-sm text-gray-300 leading-relaxed">
                    <span className="font-semibold text-white">AI-Powered:</span> Analyzes genre, mood, energy, and style for perfect matches.
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
