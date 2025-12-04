import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyDTfd9NgQ3HC6rzPtNv3RyWns6ED2SuLL0",
  authDomain: "nala-7f047.firebaseapp.com",
  projectId: "nala-7f047",
  storageBucket: "nala-7f047.appspot.com",
  messagingSenderId: "1028025860603",
  appId: "1:1028025860603:ios:1f81b922b6ad5d3c858b5e",
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

export { app, auth };
