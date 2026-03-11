import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { signOut, onAuthStateChanged } from "firebase/auth";
import { auth } from "../config/firebaseConfig";
import { ApiService } from "../services/ApiService";

interface User {
  uid: string;
  email: string;
  displayName: string | null;
}

interface AuthContextType {
  loggedInUser: User | null;
  setLoggedInUser: (user: User | null) => void;
  hasCompletedOnboarding: boolean;
  setHasCompletedOnboarding: (completed: boolean) => void;
  loading: boolean;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [loggedInUser, setLoggedInUser] = useState<User | null>(null);
  const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        setLoggedInUser({
          uid: firebaseUser.uid,
          email: firebaseUser.email ?? "",
          displayName: firebaseUser.displayName,
        });
        try {
          const status = await ApiService.getUserStatus(firebaseUser.uid);
          setHasCompletedOnboarding(status?.onboarding_completed === true);
        } catch {
          setHasCompletedOnboarding(false);
        }
      } else {
        setLoggedInUser(null);
        setHasCompletedOnboarding(false);
      }
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  const logout = async () => {
    try {
      await signOut(auth);
      setLoggedInUser(null);
      setHasCompletedOnboarding(false);
      console.log("👋 Logged out");
    } catch (error) {
      console.error("❌ Logout failed:", error);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        loggedInUser,
        setLoggedInUser,
        hasCompletedOnboarding,
        setHasCompletedOnboarding,
        loading,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
};
