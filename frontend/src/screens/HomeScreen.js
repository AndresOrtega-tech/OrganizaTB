import React from 'react';
import { View, Text, StyleSheet, FlatList } from 'react-native';

const HomeScreen = () => {
  // Datos de ejemplo (esto después vendrá del backend de tu compañero)
  const tareasEjemplo = [
    { id: '1', title: 'Proyecto de Facultad', status: 'Pendiente' },
    { id: '2', title: 'Tarea de Inglés', status: 'Completado' },
  ];

  return (
    <View style={styles.container}>
      <Text style={styles.header}>Mis Actividades Escolares</Text>
      <FlatList
        data={tareasEjemplo}
        keyExtractor={item => item.id}
        renderItem={({ item }) => (
          <View style={styles.item}>
            <Text style={styles.title}>{item.title}</Text>
            <Text>{item.status}</Text>
          </View>
        )}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: '#f5f6fa' },
  header: { fontSize: 24, fontWeight: 'bold', marginBottom: 20, marginTop: 40 },
  item: { backgroundColor: '#fff', padding: 15, borderRadius: 10, marginBottom: 10, elevation: 2 },
  title: { fontSize: 18, fontWeight: '600' }
});

export default HomeScreen;