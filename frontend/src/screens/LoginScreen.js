import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert, KeyboardAvoidingView, Platform, ScrollView, TouchableWithoutFeedback, Keyboard } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { authApi } from '../api/auth';
import Input from '../components/Input';
import Button from '../components/Button';

// 1. Agregamos { navigation } como parámetro para poder usarlo
const LoginScreen = ({ navigation }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert("Error", "Por favor ingresa correo y contraseña");
      return;
    }

    setLoading(true);
    try {
      const data = await authApi.login(email, password);
      
      if (data.access_token) {
        await AsyncStorage.setItem('userToken', data.access_token);
      }
      
      Alert.alert("¡Éxito!", "Has iniciado sesión correctamente");
      // 2. Si el login es exitoso, nos movemos a la pantalla de Inicio
      navigation.navigate('Home');
    } catch (error) {
      const msg = error.message || "No se pudo conectar con el servidor backend";
      Alert.alert("Error", msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 40 : 0}
    >
      <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
        <ScrollView
          contentContainerStyle={styles.container}
          keyboardShouldPersistTaps="handled"
        >
          <Text style={styles.title}>OrganizaT</Text>
          
          <Input 
            placeholder="Correo electrónico" 
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
          />
          
          <Input 
            placeholder="Contraseña" 
            value={password}
            onChangeText={setPassword}
            secureTextEntry 
          />

          <Button 
            title="Iniciar Sesión"
            onPress={handleLogin}
            loading={loading}
          />

          <TouchableOpacity 
            style={styles.registerLink} 
            onPress={() => navigation.navigate('Register')}
          >
            <Text style={styles.linkText}>¿No tienes cuenta? Regístrate aquí</Text>
          </TouchableOpacity>
        </ScrollView>
      </TouchableWithoutFeedback>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  flex: { flex: 1 },
  container: { flexGrow: 1, justifyContent: 'center', padding: 20, backgroundColor: '#fff' },
  title: { fontSize: 32, fontWeight: 'bold', textAlign: 'center', marginBottom: 40, color: '#2c3e50' },
  // Estilos para el enlace de registro
  registerLink: { marginTop: 20, alignItems: 'center' },
  linkText: { color: '#3498db', fontWeight: '500' }
});

export default LoginScreen;
