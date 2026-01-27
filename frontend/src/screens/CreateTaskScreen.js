import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  TouchableWithoutFeedback,
  Keyboard,
  Switch,
  Alert,
  TouchableOpacity
} from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { tasksApi } from '../api/tasks';
import Input from '../components/Input';
import Button from '../components/Button';

const CreateTaskScreen = ({ navigation }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [dueDate, setDueDate] = useState(new Date());
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [dateSelected, setDateSelected] = useState(false);
  const [hasReminder, setHasReminder] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleCreate = async () => {
    if (!title.trim()) {
      Alert.alert('Error', 'El título es obligatorio');
      return;
    }

    setLoading(true);
    try {
      const newTask = {
        title,
        description,
        due_date: dateSelected ? dueDate.toISOString() : null,
        has_reminder: hasReminder,
        is_completed: false
      };

      await tasksApi.create(newTask);
      Alert.alert('Éxito', 'Tarea creada correctamente');
      navigation.goBack();
    } catch (error) {
      console.error(error);
      const msg = error.message || 'No se pudo crear la tarea';
      Alert.alert('Error', msg);
    } finally {
      setLoading(false);
    }
  };

  const onDateChange = (event, selectedDate) => {
    const currentDate = selectedDate || dueDate;
    setShowDatePicker(Platform.OS === 'ios');
    if (event.type !== 'dismissed') {
      setDueDate(currentDate);
      setDateSelected(true);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
    >
      <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
        <ScrollView contentContainerStyle={styles.container}>
          <Text style={styles.title}>Nueva Tarea</Text>

          <Input
            label="Título"
            placeholder="Ej. Estudiar Matemáticas"
            value={title}
            onChangeText={setTitle}
          />

          <Input
            label="Descripción"
            placeholder="Detalles adicionales..."
            value={description}
            onChangeText={setDescription}
            multiline
            numberOfLines={4}
            style={{ height: 100, textAlignVertical: 'top' }}
          />

          <View style={styles.dateContainer}>
            <Text style={styles.label}>Fecha de Vencimiento</Text>
            <TouchableOpacity 
              style={styles.dateButton} 
              onPress={() => setShowDatePicker(true)}
            >
              <Text style={styles.dateText}>
                {dateSelected ? dueDate.toLocaleDateString() : 'Seleccionar fecha'}
              </Text>
            </TouchableOpacity>
          </View>

          {showDatePicker && (
            <DateTimePicker
              testID="dateTimePicker"
              value={dueDate}
              mode="date"
              is24Hour={true}
              display="default"
              onChange={onDateChange}
            />
          )}

          <View style={styles.switchContainer}>
            <Text style={styles.switchLabel}>¿Activar recordatorio?</Text>
            <Switch
              value={hasReminder}
              onValueChange={setHasReminder}
              trackColor={{ false: "#767577", true: "#3498db" }}
              thumbColor={hasReminder ? "#f4f3f4" : "#f4f3f4"}
            />
          </View>

          <Button
            title="Crear Tarea"
            onPress={handleCreate}
            loading={loading}
            style={{ marginTop: 20 }}
          />
        </ScrollView>
      </TouchableWithoutFeedback>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  flex: { flex: 1 },
  container: { padding: 20, backgroundColor: '#fff', flexGrow: 1 },
  title: { fontSize: 24, fontWeight: 'bold', marginBottom: 20, color: '#2c3e50', textAlign: 'center' },
  label: { fontSize: 16, fontWeight: '600', color: '#2c3e50', marginBottom: 5, marginLeft: 2 },
  dateContainer: { marginBottom: 15 },
  dateButton: {
    borderWidth: 1,
    borderColor: '#ccc',
    padding: 15,
    borderRadius: 10,
    backgroundColor: '#fff',
  },
  dateText: { fontSize: 16, color: '#2c3e50' },
  switchContainer: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginVertical: 15, paddingHorizontal: 5 },
  switchLabel: { fontSize: 16, color: '#2c3e50', fontWeight: '500' },
});

export default CreateTaskScreen;
