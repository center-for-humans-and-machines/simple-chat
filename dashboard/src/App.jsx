import React, { useContext, useEffect, useState } from "react";
import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import CustomizedTheme from "./theme";
import Sidebar from "./components/Sidebar";
import {
  BrowserRouter as Router,
  Route,
  Navigate,
  Routes
} from "react-router-dom";

import { AuthContext } from "./contexts/AuthContext";

import LoginPage from "./pages/LoginPage";

import FirstPage from "./pages/FirstPage";
import ProjectPage from "./pages/ProjectPage";
import ConversationPage from "./pages/ConversationPage";
import SystemMessagePage from "./pages/SystemMessagePage";
import CreateNewProjectFormPage from "./pages/CreateNewProjectFormPage";

function App() {
  const { authData } = useContext(AuthContext);

  function DelayedRedirect({ to, delay = 100 }) {
    const [shouldRedirect, setShouldRedirect] = useState(false);

    useEffect(() => {
      const timer = setTimeout(() => {
        setShouldRedirect(true);
      }, delay);

      return () => clearTimeout(timer);
    }, [delay]);

    return shouldRedirect ? <Navigate to={to} replace /> : null;
  }

  return (
    <ThemeProvider theme={CustomizedTheme}>
      <CssBaseline />
      <Router>
        {authData.email && <Sidebar />}
        <Routes>
          <Route
            path="/login"
            element={
              !authData?.email ? <LoginPage /> : <Navigate to="/" replace />
            }
          />
          <Route
            path="/"
            element={
              authData?.email ? (
                <FirstPage />
              ) : (
                <DelayedRedirect to="/login" replace />
              )
            }
          />
          <Route
            path="/project/:project_id"
            element={
              authData?.email ? (
                <ProjectPage />
              ) : (
                <DelayedRedirect to="/login" replace />
              )
            }
          />
          <Route
            path="/new_project"
            element={
              authData?.email ? (
                <CreateNewProjectFormPage />
              ) : (
                <DelayedRedirect to="/login" replace />
              )
            }
          />
          <Route
            path="/project/:project_id/conversation/:conversation_id"
            element={
              authData?.email ? (
                <ConversationPage />
              ) : (
                <DelayedRedirect to="/login" replace />
              )
            }
          />
          <Route
            path="/systemmsg/:project_id"
            element={
              authData?.email ? (
                <SystemMessagePage />
              ) : (
                <DelayedRedirect to="/login" replace />
              )
            }
          />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
