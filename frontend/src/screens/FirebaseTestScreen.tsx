import React, { useState } from "react";
import { View, Text, TextInput, TouchableOpacity, StyleSheet } from "react-native";
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword } from "firebase/auth";

export default function FirebaseTestScreen() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [output, setOutput] = useState("");

  const auth = getAuth();

  const handleSignUp = async () => {
    try {
      const userCred = await createUserWithEmailAndPassword(auth, email, password);
      const token = await userCred.user.getIdToken();
      setOutput(`✅ Signed up!\nUID: ${userCred.user.uid}\nToken: ${token.slice(0, 40)}...`);
    } catch (err: any) {
      setOutput(`❌ ${err.message}`);
    }
  };

  const handleLogin = async () => {
    try {
      const userCred = await signInWithEmailAndPassword(auth, email, password);
      const token = await userCred.user.getIdToken();
      setOutput(`✅ Logged in!\nUID: ${userCred.user.uid}\nToken: ${token.slice(0, 40)}...`);
    } catch (err: any) {
      setOutput(`❌ ${err.message}`);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Firebase Auth Test</Text>

      <TextInput
        style={styles.input}
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
      />

      <TextInput
        style={styles.input}
        placeholder="Password"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
      />

      <TouchableOpacity style={styles.button} onPress={handleSignUp}>
        <Text style={styles.buttonText}>Sign Up</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.button} onPress={handleLogin}>
        <Text style={styles.buttonText}>Log In</Text>
      </TouchableOpacity>

      <Text style={styles.output}>{output}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", alignItems: "center", padding: 20 },
  title: { fontSize: 22, fontWeight: "bold", marginBottom: 20 },
  input: {
    borderWidth: 1, borderColor: "#ccc", width: "100%", padding: 12, borderRadius: 8, marginBottom: 10
  },
  button: {
    backgroundColor: "#48935F", padding: 12, borderRadius: 8, width: "100%", alignItems: "center", marginBottom: 10
  },
  buttonText: { color: "white", fontWeight: "bold" },
  output: { marginTop: 20, textAlign: "center", color: "#333" },
});
