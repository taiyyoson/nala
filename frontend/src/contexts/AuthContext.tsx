import React, { createContext, useContext, useState, ReactNode } from "react";
import { signOut } from "firebase/auth";
import { auth } from "../config/firebaseConfig";

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
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [loggedInUser, setLoggedInUser] = useState<User | null>(null);
  const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState(false);

  //  logout 
  const logout = async () => {
    try {
      await signOut(auth);
      setLoggedInUser(null);
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
