import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const recommendationsAPI = {
  /**
   * Get song recommendations (sync version)
   * @param {string} seedSong - The seed song name
   * @param {number} count - Number of recommendations
   * @param {boolean} verify - Enable AI verification
   * @returns {Promise} Recommendation response
   */
  async getRecommendations(seedSong, count = 5, verify = true) {
    const response = await api.post('/recommendations', {
      seed_song: seedSong,
      count,
      verify,
    });
    return response.data;
  },

  /**
   * Get song recommendations (async version - faster)
   * @param {string} seedSong - The seed song name
   * @param {number} count - Number of recommendations
   * @param {boolean} verify - Enable AI verification
   * @returns {Promise} Recommendation response
   */
  async getRecommendationsAsync(seedSong, count = 5, verify = true) {
    const response = await api.post('/recommendations-async', {
      seed_song: seedSong,
      count,
      verify,
    });
    return response.data;
  },
};

export const spotifyAPI = {
  /**
   * Get Spotify authorization URL
   * @returns {Promise<string>} Authorization URL
   */
  async getAuthUrl() {
    const response = await api.get('/spotify/auth-url');
    return response.data.auth_url;
  },

  /**
   * Exchange authorization code for access token
   * @param {string} code - Authorization code from callback
   * @returns {Promise} Token information
   */
  async exchangeCode(code) {
    const response = await api.post('/spotify/callback', null, {
      params: { code },
    });
    return response.data;
  },

  /**
   * Add track to Spotify queue
   * @param {string} trackUri - Spotify track URI
   * @returns {Promise} Response
   */
  async addToQueue(trackUri) {
    const response = await api.post('/spotify/queue/add', { track_uri: trackUri });
    return response.data;
  },

  /**
   * Remove track from Spotify queue (not directly supported by Spotify API)
   * This is a placeholder - actual implementation would need to skip the track
   * @param {string} trackUri - Spotify track URI
   * @returns {Promise} Response
   */
  async removeFromQueue(trackUri) {
    // Note: Spotify doesn't support removing specific tracks from queue
    // This would need custom implementation
    const response = await api.post('/spotify/queue/remove', { track_uri: trackUri });
    return response.data;
  },
};

export const healthAPI = {
  /**
   * Check API health
   * @returns {Promise} Health status
   */
  async checkHealth() {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;

