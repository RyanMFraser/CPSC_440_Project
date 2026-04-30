// Quick Reference: How to Call Your Backend

// ============================================
// 1. IMPORT THE API CLIENT
// ============================================
import apiClient from './services/api';

// ============================================
// 2. BASIC USAGE IN COMPONENTS
// ============================================

import { useState, useEffect } from 'react';
import apiClient from './services/api';

function MyComponent() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch data on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Replace '/your-endpoint' with your actual FastAPI route
        const result = await apiClient.get('/your-endpoint');
        setData(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!data) return <div>No data</div>;

  return <div>{JSON.stringify(data)}</div>;
}

// ============================================
// 3. POSTING DATA TO BACKEND
// ============================================

async function submitForm(formData) {
  try {
    const response = await apiClient.post('/submit-data', {
      name: formData.name,
      club: formData.club,
      x: formData.x,
      y: formData.y,
    });
    console.log('Success:', response);
    return response;
  } catch (error) {
    console.error('Failed to submit:', error);
  }
}

// ============================================
// 4. UPDATING DATA
// ============================================

async function updateRecord(id, updatedData) {
  try {
    const response = await apiClient.put(`/records/${id}`, updatedData);
    console.log('Updated:', response);
    return response;
  } catch (error) {
    console.error('Failed to update:', error);
  }
}

// ============================================
// 5. DELETING DATA
// ============================================

async function deleteRecord(id) {
  try {
    await apiClient.delete(`/records/${id}`);
    console.log('Deleted successfully');
  } catch (error) {
    console.error('Failed to delete:', error);
  }
}

// ============================================
// 6. HEALTH CHECK (Backend Status)
// ============================================

async function checkBackendStatus() {
  try {
    const status = await apiClient.healthCheck();
    console.log('Backend is running:', status);
    return true;
  } catch (error) {
    console.log('Backend is offline:', error.message);
    return false;
  }
}

// ============================================
// 7. EXAMPLE: FETCH GOLF DATA
// ============================================

async function fetchGolfShots(playerName) {
  try {
    // Assuming your backend has an endpoint like GET /shots?name=Ryan
    const shots = await apiClient.get(`/shots?name=${playerName}`);
    console.log('Shots for', playerName, ':', shots);
    return shots;
  } catch (error) {
    console.error('Failed to fetch shots:', error);
  }
}

// ============================================
// 8. ERROR HANDLING EXAMPLE
// ============================================

async function robustApiCall(endpoint, method = 'GET', data = null) {
  try {
    let response;

    switch (method.toUpperCase()) {
      case 'GET':
        response = await apiClient.get(endpoint);
        break;
      case 'POST':
        response = await apiClient.post(endpoint, data);
        break;
      case 'PUT':
        response = await apiClient.put(endpoint, data);
        break;
      case 'DELETE':
        response = await apiClient.delete(endpoint);
        break;
      default:
        throw new Error(`Unknown method: ${method}`);
    }

    console.log('API Response:', response);
    return { success: true, data: response };
  } catch (error) {
    console.error('API Error:', error);
    return {
      success: false,
      error: error.message,
      timestamp: new Date().toISOString(),
    };
  }
}

// ============================================
// TIPS
// ============================================

/*
1. Always use try-catch when calling the API
2. Show loading state while fetching
3. Display errors to the user appropriately
4. Test endpoints in Postman/Insomnia first
5. Check browser DevTools (F12 → Network tab) for API calls
6. Backend API docs: http://localhost:8000/docs
7. Use relative URLs (e.g., '/endpoint') in development
   They'll automatically proxy to http://localhost:8000
*/
