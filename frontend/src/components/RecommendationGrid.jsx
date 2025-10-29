import React from 'react';
import TrackCard from './TrackCard';
import TrackCardSimple from './TrackCardSimple';

const RecommendationGrid = ({ recommendations, onAddToQueue, onRemoveFromQueue, hideQueueButtons }) => {
  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="text-center py-12 px-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm">
        <p className="text-gray-400 text-lg">No recommendations found</p>
      </div>
    );
  }

  const CardComponent = hideQueueButtons ? TrackCardSimple : TrackCard;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {recommendations.map((rec, index) => (
        <CardComponent 
          key={rec.track?.id || index} 
          recommendation={rec}
          index={index}
          onAddToQueue={onAddToQueue}
          onRemoveFromQueue={onRemoveFromQueue}
        />
      ))}
    </div>
  );
};

export default RecommendationGrid;

