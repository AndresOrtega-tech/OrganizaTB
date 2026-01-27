import client from './client';

export const authApi = {
  login: async (email, password) => {
    return client('/auth/login', {
      method: 'POST',
      body: { email, password },
    });
  },

  register: async (userData) => {
    return client('/users', {
      method: 'POST',
      body: {
        email: userData.email,
        password: userData.password,
        full_name: userData.fullName,
        avatar_url: userData.avatarUrl || "",
      },
    });
  },
};
