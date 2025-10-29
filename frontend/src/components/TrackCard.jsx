import React, { useState, useEffect } from 'react';
import { Music, Sparkles, TrendingUp, ExternalLink, Plus, X } from 'lucide-react';

const TrackCard = ({ recommendation, index, onAddToQueue, onRemoveFromQueue }) => {
  const { track, suggestion, verification } = recommendation;
  const [isHovered, setIsHovered] = useState(false);
  const [isInQueue, setIsInQueue] = useState(!!recommendation?.in_queue);
  const [isAdding, setIsAdding] = useState(false);

  useEffect(() => {
    setIsInQueue(!!recommendation?.in_queue);
  }, [recommendation?.in_queue]);

  const handleAddToQueue = async () => {
    setIsAdding(true);
    try {
      await onAddToQueue(track.uri);
      setIsInQueue(true);
    } catch (error) {
      console.error('Failed to add to queue:', error);
    } finally {
      setIsAdding(false);
    }
  };

  const handleRemoveFromQueue = async () => {
    setIsAdding(true);
    try {
      await onRemoveFromQueue(track.uri);
      setIsInQueue(false);
    } catch (error) {
      console.error('Failed to remove from queue:', error);
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <div 
      className="group relative overflow-hidden rounded-2xl bg-gradient-to-b from-white/5 to-white/0 hover:bg-white/10 border border-white/5 hover:border-white/20 backdrop-blur-sm transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-spotify-green/10"
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

        {/* AI Badge */}
        <div className={`absolute top-3 right-3 px-2 py-1 rounded-full bg-purple-500/90 backdrop-blur-sm flex items-center gap-1.5 transition-all duration-300 ${
          isHovered ? 'translate-y-0 opacity-100' : '-translate-y-2 opacity-0'
        }`}>
          <Sparkles className="w-3 h-3 text-white" />
          <span className="text-xs font-semibold text-white">AI Match</span>
        </div>

        {/* Popularity Badge */}
        {track.popularity >= 70 && (
          <div className="absolute top-3 left-3 px-2 py-1 rounded-full bg-spotify-green/90 backdrop-blur-sm flex items-center gap-1.5">
            <TrendingUp className="w-3 h-3 text-black" />
            <span className="text-xs font-bold text-black">Hot</span>
          </div>
        )}
      </div>

      {/* Track Info */}
      <div className="p-5">
        <h3 className="text-white font-bold text-base mb-1 truncate group-hover:text-spotify-green transition-colors">
          {track.name}
        </h3>
        
        <p className="text-gray-400 text-sm mb-3 truncate">
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
          <div className="mb-3 p-3 rounded-xl bg-black/40 border border-white/10 animate-fade-in">
            <p className="text-xs text-gray-300 leading-relaxed line-clamp-3">
              {suggestion.reason}
            </p>
          </div>
        )}

        {/* Queue Actions */}
        <div className="flex items-center gap-2 mt-4">
          {!isInQueue ? (
            <button
              onClick={handleAddToQueue}
              disabled={isAdding}
              className="flex-1 px-4 py-2.5 bg-spotify-green hover:bg-green-400 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg text-sm font-bold text-black transition-all hover:scale-105 active:scale-95 flex items-center justify-center gap-2 disabled:cursor-not-allowed"
            >
              {isAdding ? (
                <>
                  <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                  <span>Adding...</span>
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4" />
                  <span>Add to Queue</span>
                </>
              )}
            </button>
          ) : (
            <button
              onClick={handleRemoveFromQueue}
              disabled={isAdding}
              className="flex-1 px-4 py-2.5 bg-red-500/20 hover:bg-red-500/30 disabled:bg-gray-700 disabled:text-gray-500 border border-red-500/50 hover:border-red-500 rounded-lg text-sm font-bold text-red-400 transition-all hover:scale-105 active:scale-95 flex items-center justify-center gap-2 disabled:cursor-not-allowed"
            >
              {isAdding ? (
                <>
                  <div className="w-4 h-4 border-2 border-red-400/30 border-t-red-400 rounded-full animate-spin" />
                  <span>Removing...</span>
                </>
              ) : (
                <>
                  <X className="w-4 h-4" />
                  <span>Remove</span>
                </>
              )}
            </button>
          )}
          
          {track.id && (
            <a
              href={`https://open.spotify.com/track/${track.id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-2.5 bg-white/5 hover:bg-white/10 rounded-lg border border-white/10 hover:border-white/30 transition-all hover:scale-105 active:scale-95"
              title="Open in Spotify"
            >
              <ExternalLink className="w-4 h-4 text-white" />
            </a>
          )}
        </div>

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

