import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Alert, ActivityIndicator, KeyboardAvoidingView, Platform, TouchableWithoutFeedback, Keyboard, RefreshControl } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { usersApi } from '../api/users';
import Input from '../components/Input';
import Button from '../components/Button';

const ProfileScreen = ({ navigation }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [avatarName, setAvatarName] = useState('');
  const [updating, setUpdating] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const fetchUser = async () => {
    try {
      const userData = await usersApi.getMe();
      setUser(userData);
      if (userData.avatar_url) {
        setAvatarName(userData.avatar_url);
      }
    } catch (error) {
      console.error(error);
      if (error.status === 401) {
        Alert.alert('Sesión expirada', 'Por favor inicia sesión nuevamente.');
        handleLogout();
      } else {
        Alert.alert('Error', 'No se pudo cargar la información del usuario');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchUser();
    setRefreshing(false);
  };

  const handleUpdateAvatar = async () => {
    if (!avatarName.trim()) {
      Alert.alert('Error', 'Por favor ingresa un nombre para el avatar');
      return;
    }

    setUpdating(true);
    try {
      await usersApi.updateAvatar(avatarName);
      Alert.alert('Éxito', 'Avatar actualizado correctamente');
      await fetchUser();
    } catch (error) {
      const msg = error.message || 'No se pudo actualizar el avatar';
      Alert.alert('Error', msg);
    } finally {
      setUpdating(false);
    }
  };

  const handleLogout = async () => {
    await AsyncStorage.removeItem('userToken');
    navigation.reset({
      index: 0,
      routes: [{ name: 'Login' }],
    });
  };

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
    >
      <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
        <ScrollView
          contentContainerStyle={styles.container}
          keyboardShouldPersistTaps="handled"
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
          }
        >
          {loading ? (
            <View style={[styles.container, styles.center]}>
              <ActivityIndicator size="large" color="#3498db" />
            </View>
          ) : (
            <>
              <Text style={styles.title}>Perfil de Usuario</Text>

              {user && (
                <View style={styles.userInfo}>
                  <Text style={styles.label}>Nombre:</Text>
                  <Text style={styles.value}>{user.full_name || 'No especificado'}</Text>

                  <Text style={styles.label}>Correo:</Text>
                  <Text style={styles.value}>{user.email}</Text>

                  <Text style={styles.label}>Avatar Actual:</Text>
                  <Text style={styles.value}>{user.avatar_url || 'Sin avatar'}</Text>
                </View>
              )}

              <View style={styles.divider} />

              <Text style={styles.subtitle}>Cambiar Avatar</Text>
              <Text style={styles.description}>Ingresa el nombre o URL de tu nuevo avatar:</Text>

              <Input
                placeholder="Nombre del avatar (ej. Avatar1)"
                value={avatarName}
                onChangeText={setAvatarName}
                autoCapitalize="none"
              />

              <Button
                title="Actualizar Avatar"
                onPress={handleUpdateAvatar}
                loading={updating}
              />

              <View style={styles.divider} />

              <Button
                title="Cerrar Sesión"
                onPress={handleLogout}
                variant="secondary"
                style={{ marginTop: 20 }}
              />
            </>
          )}
        </ScrollView>
      </TouchableWithoutFeedback>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  flex: { flex: 1 },
  container: { flexGrow: 1, padding: 20, backgroundColor: '#fff', paddingTop: 10 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  title: { fontSize: 32, fontWeight: 'bold', textAlign: 'center', marginBottom: 16, color: '#2c3e50', marginTop: 8 },
  subtitle: { fontSize: 24, fontWeight: 'bold', marginBottom: 15, color: '#2c3e50' },
  userInfo: { marginBottom: 30, backgroundColor: '#f8f9fa', padding: 15, borderRadius: 10 },
  label: { fontSize: 16, color: '#7f8c8d', marginBottom: 5, fontWeight: '600' },
  value: { fontSize: 18, color: '#2c3e50', marginBottom: 15 },
  description: { fontSize: 14, color: '#7f8c8d', marginBottom: 15 },
  divider: { height: 1, backgroundColor: '#eee', marginVertical: 20 },
});

export default ProfileScreen;
