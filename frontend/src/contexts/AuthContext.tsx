import React, { createContext, useContext, useState, ReactNode } from 'react';

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
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [loggedInUser, setLoggedInUser] = useState<User | null>(null);
  const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState(false);

  return (
    <AuthContext.Provider
      value={{
        loggedInUser,
        setLoggedInUser,
        hasCompletedOnboarding,
        setHasCompletedOnboarding,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;