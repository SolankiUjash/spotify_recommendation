import React, { useState } from 'react';
import { Sparkles, TrendingUp, ExternalLink, Plus } from 'lucide-react';

const TrackCard = ({ recommendation, index, onAddToQueue }) => {
  const { track, suggestion, verification } = recommendation;

  return (
    <div 
      className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-white/5 to-white/0 sm:hover:bg-white/10 border border-white/5 sm:hover:border-white/20 backdrop-blur-sm transition-all duration-300 sm:hover:scale-105 sm:hover:shadow-2xl sm:hover:shadow-spotify-green/10"
      style={{
        animationDelay: `${index * 50}ms`,
        animation: 'fadeInUp 0.5s ease-out forwards'
      }}
    >
      {/* Track Info */}
      <div className="p-4 sm:p-5">
        {/* Header with Badges */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div className="flex-1 min-w-0">
            <h3 className="text-white font-bold text-lg sm:text-base mb-1 truncate group-hover:text-spotify-green transition-colors">
              {track.name}
            </h3>
            <p className="text-gray-400 text-sm sm:text-sm text-xs truncate">
              {Array.isArray(track.artists) ? track.artists.join(', ') : track.artists}
            </p>
          </div>
          
          {/* Badges */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <div className="px-2 py-1 rounded-full bg-purple-500/90 backdrop-blur-sm flex items-center gap-1.5">
              <Sparkles className="w-3 h-3 text-white" />
              <span className="text-xs font-semibold text-white hidden sm:inline">AI</span>
            </div>
            
            {track.popularity >= 70 && (
              <div className="px-2 py-1 rounded-full bg-spotify-green/90 backdrop-blur-sm flex items-center gap-1.5">
                <TrendingUp className="w-3 h-3 text-black" />
                <span className="text-xs font-bold text-black hidden sm:inline">Hot</span>
              </div>
            )}
          </div>
        </div>

        {/* Genre Tag */}
        {suggestion?.genre && (
          <div className="mb-3">
            <span className="inline-block px-2.5 py-1 rounded-full bg-white/5 border border-white/10 text-xs text-gray-300">
              {suggestion.genre}
            </span>
          </div>
        )}

        {/* AI Reason removed - no hover text */}

        {track.id && (
          <div className="flex justify-between items-center mt-4">
            <a
              href={`https://open.spotify.com/track/${track.id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-3 py-2.5 bg-white/5 hover:bg-white/10 rounded-lg border border-white/10 hover:border-white/20 transition-all"
              title="Open in Spotify"
            >
              <ExternalLink className="w-4 h-4 text-white" />
              <span className="text-sm text-white/80">Open in Spotify</span>
            </a>
            {onAddToQueue && track.uri && (
              <AddButton onAdd={() => onAddToQueue(track.uri)} />
            )}
          </div>
        )}

        {/* Verification Score */}
        {verification && (
          <div className="mt-3 pt-3 border-t border-white/5">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">Match Score</span>
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

export default TrackCard;

// Local add button that disables permanently after one click
const AddButton = ({ onAdd }) => {
  const [disabled, setDisabled] = useState(false);

  const handleClick = async () => {
    if (disabled) return;
    setDisabled(true);
    try {
      await onAdd();
    } catch (e) {
      // Intentionally keep disabled as per requirement
      // console.error(e);
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={disabled}
      className={`inline-flex items-center gap-2 px-3 py-2.5 rounded-lg transition-all font-semibold ${
        disabled
          ? 'bg-white/10 text-gray-400 border border-white/10 cursor-not-allowed'
          : 'bg-spotify-green hover:bg-green-400 text-black'
      }`}
      title={disabled ? 'Added' : 'Add to Queue'}
    >
      <Plus className="w-4 h-4" />
      <span className="text-sm">{disabled ? 'Added' : 'Add'}</span>
    </button>
  );
};

