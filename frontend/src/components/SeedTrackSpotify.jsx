import React from 'react';
import { Play, Music, TrendingUp } from 'lucide-react';

const SeedTrackSpotify = ({ track }) => {
  return (
    <div className="group relative overflow-hidden rounded-3xl bg-gradient-to-br from-spotify-green/20 via-green-600/10 to-black border border-spotify-green/30 backdrop-blur-sm sm:hover:scale-[1.01] transition-all duration-300">
      {/* Glow Effect */}
      <div className="absolute inset-0 bg-gradient-to-r from-spotify-green/0 via-spotify-green/5 to-spotify-green/0 opacity-0 sm:group-hover:opacity-100 transition-opacity duration-500" />
      
      <div className="relative p-5 sm:p-8">
        <div className="flex flex-col sm:flex-row items-start gap-6">
          {/* Album Art */}
          <div className="relative flex-shrink-0">
            <div className="w-32 h-32 sm:w-40 sm:h-40 rounded-2xl overflow-hidden shadow-2xl shadow-black/50 ring-2 ring-white/10 sm:group-hover:ring-spotify-green/50 transition-all duration-300">
              {track.image_url ? (
                <img 
                  src={track.image_url} 
                  alt={track.name}
                  className="w-full h-full object-cover sm:group-hover:scale-110 transition-transform duration-500"
                />
              ) : (
                <div className="w-full h-full bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center">
                  <Music className="w-16 h-16 text-gray-600" />
                </div>
              )}
            </div>
            
            {/* Play Button Overlay */}
            <button className="hidden sm:flex absolute bottom-3 right-3 w-14 h-14 bg-spotify-green rounded-full items-center justify-center shadow-xl shadow-black/50 opacity-0 group-hover:opacity-100 transform translate-y-2 group-hover:translate-y-0 transition-all duration-300 hover:scale-110 active:scale-95">
              <Play className="w-6 h-6 text-black fill-black ml-1" />
            </button>
          </div>

          {/* Track Info */}
          <div className="flex-1 min-w-0 pt-4 sm:pt-2">
            <div className="flex flex-wrap items-center gap-2 sm:gap-3 mb-3">
              <div className="px-3 py-1 rounded-full bg-spotify-green/20 border border-spotify-green/40">
                <span className="text-xs font-semibold text-spotify-green uppercase tracking-wider">Seed Track</span>
              </div>
              <div className="px-3 py-1 rounded-full bg-white/5 border border-white/10">
                <span className="text-xs font-medium text-gray-300">Starting Point</span>
              </div>
            </div>

            <h2 className="text-2xl sm:text-4xl font-bold text-white mb-3 truncate group-hover:text-spotify-green transition-colors">
              {track.name}
            </h2>
            
            <p className="text-base sm:text-xl text-gray-300 mb-3 sm:mb-4">
              {Array.isArray(track.artists) ? track.artists.join(', ') : track.artists}
            </p>

            {track.album && (
              <p className="text-xs sm:text-sm text-gray-400 mb-4">
                {track.album}
              </p>
            )}

            {/* Stats */}
            <div className="flex flex-col sm:flex-row sm:items-center gap-4 sm:gap-6 mt-4 sm:mt-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-spotify-green" />
                </div>
                <div>
                  <p className="text-lg sm:text-2xl font-bold text-white">{track.popularity}</p>
                  <p className="text-xs text-gray-400">Popularity</p>
                </div>
              </div>

              {track.preview_url && (
                <a
                  href={track.preview_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full sm:w-auto px-6 py-3 bg-white/10 hover:bg-white/20 rounded-full text-sm font-medium text-white backdrop-blur-sm border border-white/10 hover:border-white/30 transition-all text-center"
                >
                  Preview
                </a>
              )}

              {track.uri && (
                <a
                  href={`https://open.spotify.com/track/${track.id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full sm:w-auto px-6 py-3 bg-spotify-green hover:bg-green-400 rounded-full text-sm font-bold text-black transition-all sm:hover:scale-105 active:scale-95 shadow-lg shadow-spotify-green/30 text-center"
                >
                  Open in Spotify
                </a>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SeedTrackSpotify;


