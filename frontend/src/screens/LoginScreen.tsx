import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { AuthStackParamList } from '../navigation/AuthStack';
import { useAuth } from '../contexts/AuthContext';

type LoginScreenProps = {
  navigation: NativeStackNavigationProp<AuthStackParamList, 'Login'>;
};

export default function LoginScreen({ navigation }: LoginScreenProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { setLoggedInUser } = useAuth();

  const handleLogin = async () => {
    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }

    setIsLoading(true);
    setError('');

    // Simulate API call delay
    setTimeout(() => {
      // Naive validation - any email/password works for testing
      if (email.includes('@') && password.length >= 6) {
        // Create a mock user object
        const mockUser = {
          uid: 'mock-user-123',
          email: email,
          displayName: null,
        };
        setLoggedInUser(mockUser);
      } else {
        setError('Invalid email or password must be 6+ characters');
      }
      setIsLoading(false);
    }, 1000);
  };

  return (
    <SafeAreaView style={styles.container}>
      
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        
        <View style={styles.content}>
          <View style={styles.backButtonContainer}>
            <TouchableOpacity onPress={() => navigation.goBack()}>
            <Text style={styles.backButtonText}>← </Text>
            </TouchableOpacity>
          </View>
          <Text style={styles.title}>Welcome back!</Text>
          <Text style={styles.subtitle}>Log in to continue your journey with NALA.</Text>

          <View style={styles.form}>
            <Text style={styles.label}>Email</Text>
            <View style={styles.inputContainer}>
              <TextInput
                style={styles.input}
                placeholder="Enter your email"
                placeholderTextColor="#999"
                keyboardType="email-address"
                autoCapitalize="none"
                value={email}
                onChangeText={setEmail}
              />
            </View>

            <Text style={styles.label}>Password</Text>
            <View style={styles.inputContainer}>
              <TextInput
                style={styles.input}
                placeholder="Enter your password"
                placeholderTextColor="#999"
                secureTextEntry={!showPassword}
                value={password}
                onChangeText={setPassword}
              />
              <TouchableOpacity onPress={() => setShowPassword(!showPassword)}>
                <Text style={styles.eyeIcon}>{showPassword ? '👁️' : '👁️‍🗨️'}</Text>
              </TouchableOpacity>
            </View>

            <TouchableOpacity>
              <Text style={styles.forgotPassword}>Forgot Password?</Text>
            </TouchableOpacity>

            {error ? <Text style={styles.errorText}>{error}</Text> : null}

            <TouchableOpacity
              style={styles.loginButton}
              onPress={handleLogin}
              disabled={isLoading}
            >
              {isLoading ? (
                <ActivityIndicator color="#FFF" />
              ) : (
                <Text style={styles.loginButtonText}>Log In</Text>
              )}
            </TouchableOpacity>

            <View style={styles.signUpContainer}>
              <Text style={styles.signUpText}>Don't have an account? </Text>
              <TouchableOpacity onPress={() => navigation.navigate('SignUp')}>
                <Text style={styles.signUpLink}>Sign Up</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  keyboardView: {
    flex: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 30,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#000',
    marginBottom: 8,
    marginTop: 90,

  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 40,
    textAlign: 'center',
  },
  form: {
    width: '100%',
    maxWidth: 400,
  },
  label: {
    fontSize: 14,
    color: '#333',
    marginBottom: 8,
    fontWeight: '500',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF',
    borderRadius: 12,
    paddingHorizontal: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  inputIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  input: {
    flex: 1,
    paddingVertical: 16,
    fontSize: 16,
    color: '#000',
  },
  eyeIcon: {
    fontSize: 20,
  },
  forgotPassword: {
    textAlign: 'right',
    color: '#FF6B35',
    fontSize: 14,
    marginBottom: 24,
  },
  errorText: {
    color: '#FF3B30',
    fontSize: 14,
    marginBottom: 16,
    textAlign: 'center',
  },
  loginButton: {
    backgroundColor: '#48935F',
    paddingVertical: 16,
    borderRadius: 25,
    alignItems: 'center',
    marginBottom: 20,
  },
  loginButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  signUpContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  signUpText: {
    color: '#666',
    fontSize: 14,
  },
  signUpLink: {
    color: '#FF6B35',
    fontSize: 14,
    fontWeight: '600',
  },
  backButtonContainer: {
    width: '100%',
    alignItems: 'flex-start',
    marginTop: -200,
  },
  backButtonText: {
    fontSize: 16,
    color: '#48935F', 
    fontWeight: '900',
  },
});