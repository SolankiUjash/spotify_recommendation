import React from 'react';
import RecommendationCard from './RecommendationCard';
import { Music } from 'lucide-react';

const RecommendationList = ({ recommendations }) => {
  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="text-center py-8 text-gray-400">
        <Music className="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p>No recommendations found</p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
        <Music className="w-6 h-6 text-spotify-green" />
        Recommended Songs
        <span className="text-base font-normal text-gray-400">({recommendations.length})</span>
      </h2>

      <div className="grid grid-cols-1 gap-4">
        {recommendations.map((rec, index) => (
          <RecommendationCard key={index} recommendation={rec} index={index} />
        ))}
      </div>
    </div>
  );
};

export default RecommendationList;


