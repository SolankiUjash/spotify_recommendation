import React from 'react';
import { Music2, User, Tag, CheckCircle, BarChart3 } from 'lucide-react';

const RecommendationCard = ({ recommendation, index }) => {
  const { suggestion, track, verification } = recommendation;

  return (
    <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg p-5 border border-gray-700 hover:border-gray-600 transition-all card-hover animate-slide-in">
      <div className="flex items-start gap-4">
        {/* Index */}
        <div className="flex-shrink-0 w-8 h-8 bg-spotify-green/20 rounded-full flex items-center justify-center text-spotify-green font-bold">
          {index + 1}
        </div>

        {/* Album Art */}
        {track.image_url ? (
          <img
            src={track.image_url}
            alt={track.album}
            className="w-16 h-16 rounded-md shadow-md flex-shrink-0"
          />
        ) : (
          <div className="w-16 h-16 bg-gray-700 rounded-md flex items-center justify-center flex-shrink-0">
            <Music2 className="w-6 h-6 text-gray-500" />
          </div>
        )}

        {/* Track Info */}
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-white mb-1 truncate">
            {track.name}
          </h3>
          <p className="text-gray-300 text-sm flex items-center gap-2 mb-2">
            <User className="w-4 h-4 flex-shrink-0" />
            <span className="truncate">{track.artists.join(', ')}</span>
          </p>

          {/* Genre & Reason */}
          <div className="space-y-1">
            {suggestion.genre && (
              <p className="text-xs text-gray-400 flex items-center gap-2">
                <Tag className="w-3 h-3" />
                <span>{suggestion.genre}</span>
              </p>
            )}
            {suggestion.reason && (
              <p className="text-sm text-gray-400 italic">"{suggestion.reason}"</p>
            )}
          </div>

          {/* Verification Badge */}
          {verification && (
            <div className="mt-3 flex items-center gap-4">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span className="text-xs text-green-400 font-medium">Verified</span>
              </div>
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-blue-400" />
                <span className="text-xs text-blue-400">
                  {(verification.confidence_score * 100).toFixed(0)}% confidence
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Popularity */}
        <div className="flex-shrink-0 text-center">
          <div className="w-12 h-12 rounded-full bg-spotify-green/10 flex items-center justify-center border-2 border-spotify-green/30">
            <span className="text-lg font-bold text-spotify-green">{track.popularity}</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">Pop</p>
        </div>
      </div>
    </div>
  );
};

export default RecommendationCard;


