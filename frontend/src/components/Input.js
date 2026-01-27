import React from 'react';
import { TextInput, StyleSheet, View } from 'react-native';

const Input = ({ value, onChangeText, placeholder, secureTextEntry, keyboardType, autoCapitalize, style }) => {
  return (
    <TextInput 
      style={[styles.input, style]} 
      placeholder={placeholder} 
      value={value}
      onChangeText={onChangeText}
      secureTextEntry={secureTextEntry}
      keyboardType={keyboardType}
      autoCapitalize={autoCapitalize}
      placeholderTextColor="#95a5a6"
    />
  );
};

const styles = StyleSheet.create({
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    padding: 15,
    borderRadius: 10,
    marginBottom: 15,
    backgroundColor: '#fff',
    fontSize: 16,
  },
});

export default Input;
