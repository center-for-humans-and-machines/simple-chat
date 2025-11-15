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
    const isAdmin =
      window.localStorage.getItem("admin") == "true" ? true : false;
    console.log("useEffect in AuthContext", emailInLocalStorage);
    console.log("useEffect in isAdmin", isAdmin);

    if (emailInLocalStorage) {
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
