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
  const [user, setUser] = useState<UserProfile | null>(() => {
    if (typeof window !== "undefined" && window.localStorage) {
      try {
        const saved = window.localStorage.getItem("timetabling_auth_user");
        if (saved) return JSON.parse(saved);
      } catch {
        // ignore
      }
    }
    return null;
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    // Check active session on initial load
    api
      .get<{ user?: UserProfile } | UserProfile>("/api/v1/auth/me")
      .then((data) => {
        const profile = (data && "user" in data && data.user) ? data.user : (data as UserProfile);
        if (profile && profile.role) {
          const normalized: UserProfile = {
            id: profile.id,
            email: profile.email,
            fullName: profile.fullName || (profile as unknown as { full_name?: string }).full_name || "Staff Registrar",
            role: profile.role,
            departmentId: profile.departmentId || (profile as unknown as { department_id?: string }).department_id,
            studentId: profile.studentId || (profile as unknown as { student_id?: string }).student_id,
          };
          setUser(normalized);
          try {
            localStorage.setItem("timetabling_auth_user", JSON.stringify(normalized));
          } catch {
            // ignore
          }
        } else {
          setUser(null);
          try {
            localStorage.removeItem("timetabling_auth_user");
          } catch {
            // ignore
          }
        }
      })
      .catch(() => {
        try {
          const token = localStorage.getItem("timetabling_token");
          if (!token) {
            setUser(null);
            localStorage.removeItem("timetabling_auth_user");
          }
        } catch {
          setUser(null);
        }
      })
      .finally(() => setIsLoading(false));
  }, []);

  const login = (token: string, profile: UserProfile) => {
    try {
      localStorage.setItem("timetabling_auth_user", JSON.stringify(profile));
      if (token) {
        localStorage.setItem("timetabling_token", token);
      }
    } catch {
      // ignore
    }
    setUser(profile);
  };

  const logout = async () => {
    try {
      await api.post("/api/v1/auth/logout");
    } catch {
      // ignore network errors on logout
    } finally {
      try {
        localStorage.removeItem("timetabling_auth_user");
        localStorage.removeItem("timetabling_token");
      } catch {
        // ignore
      }
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
