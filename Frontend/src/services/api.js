/**
 * API client for communicating with the backend FastAPI server
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class APIClient {
  constructor(baseURL = API_URL) {
    this.baseURL = baseURL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Health check - verify backend is running
  async healthCheck() {
    return this.request('/health', { method: 'GET' });
  }

  async getIds() {
    return this.request('/ids', { method: 'GET' });
  }

  // Example: GET request
  async get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }

  // Example: POST request
  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Example: PUT request
  async put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // Example: DELETE request
  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
}

export default new APIClient();
