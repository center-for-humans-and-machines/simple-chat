import React, { createContext, useEffect, useState } from "react";

// Create the context
export const AuthContext = createContext();

// Create a provider component
export const AuthProvider = ({ children }) => {
  const [authData, setAuthData] = useState({
    email: "",
    admin: false
  });

  useEffect(() => {
    const emailInLocalStorage = window.localStorage.getItem("email");
    const isAdmin = window.localStorage.getItem("admin") === "true";
    console.log("useEffect in AuthContext", emailInLocalStorage);
    console.log("useEffect in isAdmin", isAdmin);

    // logins from before the dashboard used tokens have to sign in again
    if (emailInLocalStorage && window.localStorage.getItem("token")) {
      if (emailInLocalStorage.includes("@")) {
        setAuthData({
          email: emailInLocalStorage,
          admin: isAdmin
        });
      }
    }
  }, []);

  return (
    <AuthContext.Provider value={{ authData, setAuthData }}>
      {children}
    </AuthContext.Provider>
  );
};
