import React, { createContext, useContext, useState, useEffect } from "react";
import { api } from "../services/api";

export type UserRole = "admin" | "coordinator" | "faculty" | "student";

export interface UserProfile {
  id: string;
  email: string;
  fullName: string;
  role: UserRole;
  departmentId?: string;
  studentId?: string;
}

interface AuthContextType {
  user: UserProfile | null;
  role: UserRole | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, profile: UserProfile) => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    // Check active session on initial load
    api
      .get<{ user: UserProfile }>("/api/v1/auth/me")
      .then((data) => setUser(data.user))
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false));
  }, []);

  const login = (_token: string, profile: UserProfile) => {
    setUser(profile);
  };

  const logout = async () => {
    try {
      await api.post("/api/v1/auth/logout");
    } finally {
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        role: user?.role || null,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
