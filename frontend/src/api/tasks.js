import client from './client';

export const tasksApi = {
  getAll: () => client('/tasks/'),
  getById: (id) => client(`/tasks/${id}`),
  create: (taskData) => client('/tasks/', {
    method: 'POST',
    body: taskData,
  }),
};
