import React from 'react';
import { Music2, User, Disc } from 'lucide-react';

const SeedTrack = ({ track }) => {
  return (
    <div className="bg-gradient-to-r from-spotify-green/10 to-green-600/5 rounded-xl p-6 border border-spotify-green/30 animate-slide-in">
      <h2 className="text-lg font-semibold text-gray-300 mb-4 flex items-center gap-2">
        <Music2 className="w-5 h-5 text-spotify-green" />
        Seed Track
      </h2>

      <div className="flex items-center gap-4">
        {/* Album Art */}
        {track.image_url ? (
          <img
            src={track.image_url}
            alt={track.album}
            className="w-20 h-20 rounded-lg shadow-lg"
          />
        ) : (
          <div className="w-20 h-20 bg-gray-700 rounded-lg flex items-center justify-center">
            <Disc className="w-8 h-8 text-gray-500" />
          </div>
        )}

        {/* Track Info */}
        <div className="flex-1">
          <h3 className="text-xl font-bold text-white mb-1">{track.name}</h3>
          <p className="text-gray-300 flex items-center gap-2">
            <User className="w-4 h-4" />
            {track.artists.join(', ')}
          </p>
          <p className="text-sm text-gray-400 mt-1">{track.album}</p>
        </div>

        {/* Popularity Badge */}
        <div className="text-center">
          <div className="w-16 h-16 rounded-full bg-spotify-green/20 flex items-center justify-center border-4 border-spotify-green/30">
            <span className="text-2xl font-bold text-spotify-green">{track.popularity}</span>
          </div>
          <p className="text-xs text-gray-400 mt-1">Popularity</p>
        </div>
      </div>
    </div>
  );
};

export default SeedTrack;


