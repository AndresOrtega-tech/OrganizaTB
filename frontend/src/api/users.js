import client from './client';

export const usersApi = {
  getMe: async () => {
    return client('/users/me');
  },
  
  updateAvatar: async (avatarUrl) => {
    return client('/users/avatar', {
      method: 'PATCH',
      body: { avatar_url: avatarUrl }
    });
  }
};
