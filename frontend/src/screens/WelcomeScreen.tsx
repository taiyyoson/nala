import React from 'react';
import {
  View,
  Text,
  Image,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { AuthStackParamList } from '../navigation/AuthStack';

type WelcomeScreenProps = {
  navigation: NativeStackNavigationProp<AuthStackParamList, 'Welcome'>;
};

export default function WelcomeScreen({ navigation }: WelcomeScreenProps) {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
          <Image
          source={require('./images/logo.png')} 
          style={styles.logoImage}
          resizeMode="contain"
        />
        <Text style={styles.logo}>NALA</Text>
        <Text style={styles.subtitle}>Your personal goal coach awaits.</Text>

        <View style={styles.buttonContainer}>
          <TouchableOpacity
            style={styles.signUpButton}
            onPress={() => navigation.navigate('SignUp')}
          >
            <Text style={styles.signUpButtonText}>Sign Up</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.logInButton}
            onPress={() => navigation.navigate('Login')}
          >
            <Text style={styles.logInButtonText}>Log In</Text>
          </TouchableOpacity>

          <Text style={styles.orText}>Or continue with</Text>

          <View style={styles.socialButtonsContainer}>
            <TouchableOpacity style={styles.socialButton}>
              <Text style={styles.socialButtonText}> Google</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.socialButton}>
              <Text style={styles.socialButtonText}> Apple</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  logoImage: {
    width: 100, 
    height: 100,
    marginBottom: 10, 
  },
  logo: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#000',
    marginBottom: 16,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 60,
    textAlign: 'center',
  },
  buttonContainer: {
    width: '100%',
    maxWidth: 350,
  },
  signUpButton: {
    backgroundColor: '#9ACDBF',
    paddingVertical: 16,
    borderRadius: 25,
    alignItems: 'center',
    marginBottom: 16,
  },
  signUpButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  logInButton: {
    backgroundColor: '#48935F',
    paddingVertical: 16,
    borderRadius: 25,
    alignItems: 'center',
    marginBottom: 32,
  },
  logInButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  orText: {
    textAlign: 'center',
    color: '#999',
    fontSize: 14,
    marginBottom: 16,
  },
  socialButtonsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  socialButton: {
    flex: 1,
    backgroundColor: '#e0e0da',
    paddingVertical: 14,
    borderRadius: 20,
    alignItems: 'center',
  },
  socialButtonText: {
    color: '#000',
    fontSize: 14,
    fontWeight: '500',
  },
});