import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert, KeyboardAvoidingView, Platform, ScrollView, TouchableWithoutFeedback, Keyboard } from 'react-native';
import { authApi } from '../api/auth';
import Input from '../components/Input';
import Button from '../components/Button';

const RegisterScreen = ({ navigation }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    if (!name || !email || !password) {
      Alert.alert("Error", "Por favor completa todos los campos");
      return;
    }

    setLoading(true);
    try {
      await authApi.register({
        email,
        password,
        fullName: name,
        avatarUrl: ""
      });
      
      Alert.alert("¡Éxito!", "Usuario registrado exitosamente");
      navigation.navigate('Login');
    } catch (error) {
      const msg = error.message || "Error en el registro";
      Alert.alert("Error", msg);
    } finally {
      setLoading(false);
    }
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
        >
          <Text style={styles.title}>Crear Cuenta</Text>
          
          <Input 
            placeholder="Nombre completo" 
            value={name}
            onChangeText={setName}
          />

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
            title="Registrarse"
            onPress={handleRegister}
            loading={loading}
            variant="primary"
            style={{ marginTop: 10 }}
          />

          <TouchableOpacity onPress={() => navigation.navigate('Login')}>
            <Text style={styles.linkText}>¿Ya tienes cuenta? Inicia sesión</Text>
          </TouchableOpacity>
        </ScrollView>
      </TouchableWithoutFeedback>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  flex: { flex: 1 },
  container: { flexGrow: 1, justifyContent: 'center', padding: 20, backgroundColor: '#fff' },
  title: { fontSize: 28, fontWeight: 'bold', textAlign: 'center', marginBottom: 30, color: '#2c3e50' },
  linkText: { color: '#3498db', textAlign: 'center', marginTop: 20 }
});

// ESTO ES LO MÁS IMPORTANTE:
export default RegisterScreen;
