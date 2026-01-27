import Constants from 'expo-constants';

const getApiUrl = () => {
  // Prefer extra.apiUrl from app.json
  const apiUrl = Constants.expoConfig?.extra?.apiUrl;
  
  if (!apiUrl) {
    console.log('API URL not found in Expo config, using default Vercel URL');
    return 'https://organiza-t-git-development-andresortegatechs-projects.vercel.app/api';
  }
  
  return apiUrl;
};

export const API_URL = getApiUrl();
