import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, Alert } from 'react-native';
import { tasksApi } from '../api/tasks';

const TaskDetailScreen = ({ route }) => {
  const { taskId } = route.params;
  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTaskDetails();
  }, [taskId]);

  const fetchTaskDetails = async () => {
    try {
      const data = await tasksApi.getById(taskId);
      setTask(data);
    } catch (error) {
      console.error(error);
      Alert.alert('Error', 'No se pudieron cargar los detalles de la tarea');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#3498db" />
      </View>
    );
  }

  if (!task) {
    return (
      <View style={styles.center}>
        <Text>No se encontró la tarea.</Text>
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>{task.title}</Text>
      
      <View style={styles.statusContainer}>
        <View style={[styles.badge, task.is_completed ? styles.completedBadge : styles.pendingBadge]}>
          <Text style={styles.badgeText}>
            {task.is_completed ? 'Completada' : 'Pendiente'}
          </Text>
        </View>
        {task.has_reminder && (
          <View style={[styles.badge, styles.reminderBadge]}>
            <Text style={styles.badgeText}>Recordatorio</Text>
          </View>
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>Descripción</Text>
        <Text style={styles.text}>{task.description || 'Sin descripción'}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>Fecha de vencimiento</Text>
        <Text style={styles.text}>
          {task.due_date ? new Date(task.due_date).toLocaleString() : 'No establecida'}
        </Text>
      </View>

      {task.tags && task.tags.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.label}>Etiquetas</Text>
          <View style={styles.tagsContainer}>
            {task.tags.map(tag => (
              <View key={tag.id} style={[styles.tag, { backgroundColor: tag.color || '#95a5a6' }]}>
                <Text style={styles.tagText}>{tag.name}</Text>
              </View>
            ))}
          </View>
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { padding: 20, backgroundColor: '#fff', flexGrow: 1 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  title: { fontSize: 26, fontWeight: 'bold', color: '#2c3e50', marginBottom: 15 },
  statusContainer: { flexDirection: 'row', marginBottom: 20 },
  badge: { paddingHorizontal: 10, paddingVertical: 5, borderRadius: 5, marginRight: 10 },
  completedBadge: { backgroundColor: '#2ecc71' },
  pendingBadge: { backgroundColor: '#f1c40f' },
  reminderBadge: { backgroundColor: '#3498db' },
  badgeText: { color: '#fff', fontWeight: 'bold', fontSize: 12 },
  section: { marginBottom: 20 },
  label: { fontSize: 16, fontWeight: 'bold', color: '#7f8c8d', marginBottom: 5 },
  text: { fontSize: 16, color: '#34495e', lineHeight: 24 },
  tagsContainer: { flexDirection: 'row', flexWrap: 'wrap' },
  tag: { paddingHorizontal: 10, paddingVertical: 5, borderRadius: 15, marginRight: 8, marginBottom: 8 },
  tagText: { color: '#fff', fontWeight: '600', fontSize: 12 },
});

export default TaskDetailScreen;
