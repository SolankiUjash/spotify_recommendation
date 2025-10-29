import { useState, useCallback } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const useStreamingRecommendations = () => {
  const [loading, setLoading] = useState(false);
  const [seedTrack, setSeedTrack] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState('');
  const [queuedCount, setQueuedCount] = useState(0);

  const streamRecommendations = useCallback(async (seedSong, count) => {
    setLoading(true);
    setError(null);
    setSeedTrack(null);
    setRecommendations([]);
    setStatus('Initializing...');
    setQueuedCount(0);

    try {
      const response = await fetch(`${API_BASE_URL}/stream-and-queue`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          seed_song: seedSong,
          count: count,
          verify: true, // Always ON for background verification
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            
            switch (data.type) {
              case 'status':
                setStatus(data.message);
                break;
              
              case 'seed':
                setSeedTrack({
                  name: data.data.name,
                  artists: data.data.artists,
                });
                break;
              
              case 'track':
                setRecommendations(prev => [...prev, {
                  suggestion: {
                    title: data.data.name,
                    artists: data.data.artists,
                    genre: data.data.genre,
                    reason: data.data.reason,
                  },
                  track: {
                    id: data.data.id,
                    name: data.data.name,
                    artists: data.data.artists,
                    album: data.data.album,
                    uri: data.data.uri,
                    popularity: data.data.popularity,
                    preview_url: data.data.preview_url,
                    image_url: data.data.image_url,
                  },
                  in_queue: data.data.added_to_queue,
                  verification_pending: data.data.verification_pending,
                }]);
                if (data.data.added_to_queue) {
                  setQueuedCount(prev => prev + 1);
                }
                break;
              
              case 'verification':
                setRecommendations(prev => prev.map(rec => 
                  rec.track.id === data.data.track_id
                    ? {
                        ...rec,
                        verification: {
                          is_valid: data.data.valid,
                          confidence_score: data.data.confidence || 1.0,
                          reason: data.data.reason || '',
                        },
                        verification_pending: false,
                      }
                    : rec
                ));
                break;
              
              case 'skip':
                setStatus(`Skipped: ${data.data.title} - ${data.data.reason}`);
                break;
              
              case 'complete':
                setStatus(`Completed! Added ${data.data.added_to_queue} tracks to queue`);
                setLoading(false);
                break;
              
              case 'error':
                setError(data.error);
                setLoading(false);
                break;
            }
          }
        }
      }
    } catch (err) {
      setError(err.message || 'Failed to stream recommendations');
      setLoading(false);
    }
  }, []);

  const clearResults = useCallback(() => {
    setSeedTrack(null);
    setRecommendations([]);
    setError(null);
    setStatus('');
    setQueuedCount(0);
  }, []);

  return {
    loading,
    seedTrack,
    recommendations,
    error,
    status,
    queuedCount,
    streamRecommendations,
    clearResults,
  };
};


