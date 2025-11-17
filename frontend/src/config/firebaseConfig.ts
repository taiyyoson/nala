import { initializeApp } from 'firebase/app';
import { initializeAuth, getReactNativePersistence } from 'firebase/auth';
import ReactNativeAsyncStorage from '@react-native-async-storage/async-storage';

const firebaseConfig = {
  apiKey: "AIzaSyDTfd9NgQ3HC6rzPtNv3RyWns6ED2SuLL0",
  authDomain: "nala-7f047.firebaseapp.com",
  projectId: "nala-7f047",
  storageBucket: "nala-7f047.appspot.com",
  messagingSenderId: "1028025860603",
  appId: "1:1028025860603:ios:1f81b922b6ad5d3c858b5e"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// ✅ Use initializeAuth instead of getAuth
const auth = initializeAuth(app, {
  persistence: getReactNativePersistence(ReactNativeAsyncStorage),
});

export { app, auth };