import { API_URL } from './config';

/**
 * Generic fetch wrapper to handle headers and errors
 */
const client = async (endpoint, options = {}) => {
  const url = `${API_URL}${endpoint}`;
  
  const defaultHeaders = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body);
  }

  try {
    const response = await fetch(url, config);
    let data;
    const text = await response.text();
    
    try {
      data = JSON.parse(text);
    } catch (e) {
      console.error(`API Error (${endpoint}) - Invalid JSON response:`, text.slice(0, 200)); // Log first 200 chars
      throw {
        status: response.status,
        message: 'El servidor devolvió una respuesta no válida (posiblemente HTML en lugar de JSON).',
        rawResponse: text
      };
    }

    if (!response.ok) {
      throw {
        status: response.status,
        message: data.detail || data.message || 'Error en la petición',
        data
      };
    }

    return data;
  } catch (error) {
    console.error(`API Error (${endpoint}):`, error);
    throw error;
  }
};

export default client;
