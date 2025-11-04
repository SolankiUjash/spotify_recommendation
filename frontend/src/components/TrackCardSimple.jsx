import React, { useState } from 'react';
import { Music, Sparkles, TrendingUp, ExternalLink, CheckCircle, Clock } from 'lucide-react';

const TrackCardSimple = ({ recommendation, index }) => {
  const { track, suggestion, verification, in_queue, verification_pending } = recommendation;
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div 
      className="group relative overflow-hidden rounded-2xl bg-gradient-to-b from-white/5 to-white/0 sm:hover:bg-white/10 border border-white/5 sm:hover:border-white/20 backdrop-blur-sm transition-all duration-300 sm:hover:scale-105 sm:hover:shadow-2xl sm:hover:shadow-spotify-green/10"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        animationDelay: `${index * 50}ms`,
        animation: 'fadeInUp 0.5s ease-out forwards'
      }}
    >
      {/* Album Art */}
      <div className="relative aspect-square overflow-hidden bg-gradient-to-br from-gray-800 to-gray-900">
        {track.image_url ? (
          <img 
            src={track.image_url} 
            alt={track.name}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <Music className="w-16 h-16 text-gray-600" />
          </div>
        )}
        
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/0 to-black/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

        {/* Queue Badge */}
        {in_queue && (
          <div className="absolute top-3 left-3 px-2 py-1 rounded-full bg-spotify-green/90 backdrop-blur-sm flex items-center gap-1.5">
            <CheckCircle className="w-3 h-3 text-black" />
            <span className="text-xs font-bold text-black">In Queue</span>
          </div>
        )}

        {/* Verification Badge */}
        {verification_pending && (
          <div className="absolute top-3 right-3 px-2 py-1 rounded-full bg-yellow-500/90 backdrop-blur-sm flex items-center gap-1.5">
            <Clock className="w-3 h-3 text-black animate-spin" />
            <span className="text-xs font-semibold text-black">Checking...</span>
          </div>
        )}

        {verification && !verification.is_valid && (
          <div className="absolute top-3 right-3 px-2 py-1 rounded-full bg-red-500/90 backdrop-blur-sm flex items-center gap-1.5">
            <span className="text-xs font-semibold text-white">Low Match</span>
          </div>
        )}

        {/* Popularity Badge */}
        {track.popularity >= 70 && (
          <div className="absolute bottom-3 left-3 px-2 py-1 rounded-full bg-black/50 backdrop-blur-sm flex items-center gap-1.5">
            <TrendingUp className="w-3 h-3 text-spotify-green" />
            <span className="text-xs font-bold text-white">Hot</span>
          </div>
        )}
      </div>

      {/* Track Info */}
      <div className="p-4 sm:p-5">
        <h3 className="text-white font-bold text-lg sm:text-base mb-1 truncate group-hover:text-spotify-green transition-colors">
          {track.name}
        </h3>
        
        <p className="text-gray-400 text-sm sm:text-sm text-xs mb-3 truncate">
          {Array.isArray(track.artists) ? track.artists.join(', ') : track.artists}
        </p>

        {/* Genre Tag */}
        {suggestion?.genre && (
          <div className="mb-3">
            <span className="inline-block px-2.5 py-1 rounded-full bg-white/5 border border-white/10 text-xs text-gray-300">
              {suggestion.genre}
            </span>
          </div>
        )}

        {/* AI Reason - Show on hover */}
        {isHovered && suggestion?.reason && (
          <div className="hidden sm:block mb-3 p-3 rounded-xl bg-black/40 border border-white/10 animate-fade-in">
            <p className="text-xs text-gray-300 leading-relaxed line-clamp-3">
              {suggestion.reason}
            </p>
          </div>
        )}

        {suggestion?.reason && (
          <div className="sm:hidden mb-3 p-3 rounded-xl bg-black/40 border border-white/10">
            <p className="text-xs text-gray-300 leading-relaxed line-clamp-4">
              {suggestion.reason}
            </p>
          </div>
        )}

        {/* Spotify Link */}
        <div className="flex items-center gap-2 mt-4">
          {track.id && (
            <a
              href={`https://open.spotify.com/track/${track.id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-white/5 hover:bg-white/10 rounded-lg border border-white/10 hover:border-spotify-green/50 transition-all sm:hover:scale-105 active:scale-95"
            >
              <ExternalLink className="w-4 h-4 text-white" />
              <span className="text-sm font-medium text-white">Open in Spotify</span>
            </a>
          )}
        </div>

        {/* Verification Score */}
        {verification && verification.is_valid && (
          <div className="mt-3 pt-3 border-t border-white/5">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">AI Match</span>
              <div className="flex items-center gap-2">
                <div className="w-20 h-1.5 bg-white/10 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-spotify-green to-green-400 rounded-full transition-all duration-500"
                    style={{ width: `${verification.confidence_score * 100}%` }}
                  />
                </div>
                <span className="text-xs font-semibold text-spotify-green">
                  {Math.round(verification.confidence_score * 100)}%
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Popularity Bar */}
        <div className="mt-2">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-gray-500">Popularity</span>
            <span className="text-xs font-semibold text-gray-400">{track.popularity}/100</span>
          </div>
          <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-500"
              style={{ width: `${track.popularity}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrackCardSimple;


