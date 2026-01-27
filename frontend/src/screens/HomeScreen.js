import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { tasksApi } from '../api/tasks';

const HomeScreen = ({ navigation }) => {
  const [refreshing, setRefreshing] = useState(false);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  const handleLogout = async () => {
    try {
      await AsyncStorage.removeItem('userToken');
      navigation.reset({
        index: 0,
        routes: [{ name: 'Login' }],
      });
    } catch (e) {
      console.error('Error al cerrar sesión:', e);
    }
  };

  const fetchTasks = useCallback(async () => {
    try {
      const data = await tasksApi.getAll();
      setTasks(data);
    } catch (error) {
      console.error('Error fetching tasks:', error);
      
      if (error.status === 401) {
        Alert.alert(
          'Sesión expirada',
          'Tu sesión ha caducado. Por favor, inicia sesión nuevamente.',
          [{ text: 'OK', onPress: handleLogout }]
        );
      } else {
        const errorMessage = error.message || 'No se pudieron cargar las tareas';
        Alert.alert('Error', errorMessage);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      fetchTasks();
    }, [fetchTasks])
  );

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchTasks();
    setRefreshing(false);
  }, [fetchTasks]);

  const handleTaskPress = (taskId) => {
    navigation.navigate('TaskDetail', { taskId });
  };

  const handleAddTask = () => {
    navigation.navigate('CreateTask');
  };

  return (
    <View style={styles.mainContainer}>
        <ScrollView
          style={styles.scroll}
          contentContainerStyle={styles.container}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        >
          <Text style={styles.header}>Mis Actividades Escolares</Text>
          
          {loading && !refreshing ? (
            <ActivityIndicator size="large" color="#3498db" style={{ marginTop: 20 }} />
          ) : (
            tasks.length === 0 ? (
                <Text style={styles.emptyText}>No tienes tareas pendientes.</Text>
            ) : (
                tasks.map(item => (
                <TouchableOpacity 
                    key={item.id} 
                    style={styles.item}
                    onPress={() => handleTaskPress(item.id)}
                >
                    <View style={styles.row}>
                        <Text style={[styles.title, item.is_completed && styles.completedTitle]}>
                            {item.title}
                        </Text>
                        {item.is_completed && (
                            <View style={styles.completedBadge}>
                                <Text style={styles.completedText}>✓</Text>
                            </View>
                        )}
                    </View>
                    
                    <Text style={styles.date}>
                        Vence: {item.due_date ? new Date(item.due_date).toLocaleDateString() : 'Sin fecha'}
                    </Text>

                    {item.tags && item.tags.length > 0 && (
                        <View style={styles.tagsContainer}>
                            {item.tags.map(tag => (
                                <View key={tag.id} style={[styles.tag, { backgroundColor: tag.color || '#95a5a6' }]}>
                                    <Text style={styles.tagText}>{tag.name}</Text>
                                </View>
                            ))}
                        </View>
                    )}
                </TouchableOpacity>
                ))
            )
          )}
        </ScrollView>

        <TouchableOpacity style={styles.fab} onPress={handleAddTask}>
            <Text style={styles.fabIcon}>+</Text>
        </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  mainContainer: { flex: 1, backgroundColor: '#f5f6fa' },
  scroll: { flex: 1 },
  container: { padding: 20, paddingTop: 8, paddingBottom: 100 },
  header: { fontSize: 24, fontWeight: 'bold', marginBottom: 16, marginTop: 4, color: '#2c3e50' },
  item: { backgroundColor: '#fff', padding: 15, borderRadius: 10, marginBottom: 10, elevation: 2, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.2, shadowRadius: 1.41 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 },
  title: { fontSize: 18, fontWeight: '600', color: '#2c3e50', flex: 1 },
  completedTitle: { textDecorationLine: 'line-through', color: '#7f8c8d' },
  completedBadge: { backgroundColor: '#2ecc71', borderRadius: 10, width: 20, height: 20, justifyContent: 'center', alignItems: 'center', marginLeft: 10 },
  completedText: { color: '#fff', fontSize: 12, fontWeight: 'bold' },
  date: { fontSize: 14, color: '#7f8c8d', marginBottom: 8 },
  tagsContainer: { flexDirection: 'row', flexWrap: 'wrap' },
  tag: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12, marginRight: 6, marginTop: 4 },
  tagText: { color: '#fff', fontSize: 10, fontWeight: 'bold' },
  emptyText: { textAlign: 'center', marginTop: 50, color: '#7f8c8d', fontSize: 16 },
  fab: {
      position: 'absolute',
      width: 60,
      height: 60,
      alignItems: 'center',
      justifyContent: 'center',
      right: 20,
      bottom: 20,
      backgroundColor: '#3498db',
      borderRadius: 30,
      elevation: 8,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.25,
      shadowRadius: 3.84,
  },
  fabIcon: {
      fontSize: 30,
      color: 'white',
      fontWeight: 'bold',
      marginTop: -2 
  }
});

export default HomeScreen;
