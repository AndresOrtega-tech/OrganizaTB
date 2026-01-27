import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { TouchableOpacity, Text } from 'react-native';

// Importación de pantallas
import LoginScreen from './src/screens/LoginScreen';
import RegisterScreen from './src/screens/RegisterScreen';
import HomeScreen from './src/screens/HomeScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import TaskDetailScreen from './src/screens/TaskDetailScreen';
import CreateTaskScreen from './src/screens/CreateTaskScreen';

const Stack = createStackNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Login">
        <Stack.Screen
          name="Login"
          component={LoginScreen}
          options={{ headerShown: false }}
        />

        <Stack.Screen
          name="Register"
          component={RegisterScreen}
          options={{
            title: 'Crear Cuenta',
            headerTintColor: '#2c3e50',
            headerTitleStyle: { fontWeight: 'bold' },
          }}
        />

        <Stack.Screen
          name="Home"
          component={HomeScreen}
          options={({ navigation }) => ({
            title: 'logout',
            headerRight: () => (
              <TouchableOpacity
                style={{
                  marginRight: 15,
                  paddingHorizontal: 10,
                  paddingVertical: 6,
                  borderRadius: 20,
                  borderWidth: 1,
                  borderColor: '#3498db',
                }}
                onPress={() => navigation.navigate('Profile')}
              >
                <Text style={{ color: '#3498db', fontWeight: '600' }}>Usuario</Text>
              </TouchableOpacity>
            ),
          })}
        />

        <Stack.Screen
          name="Profile"
          component={ProfileScreen}
          options={{ title: 'Perfil de Usuario' }}
        />

        <Stack.Screen
          name="TaskDetail"
          component={TaskDetailScreen}
          options={{ title: 'Detalles de Tarea' }}
        />

        <Stack.Screen
          name="CreateTask"
          component={CreateTaskScreen}
          options={{ title: 'Crear Nueva Tarea' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
