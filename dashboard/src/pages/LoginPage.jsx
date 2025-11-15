import React, { useState, useContext } from "react";
import { useNavigate } from "react-router";

import {
  Button,
  TextField,
  Box,
  Typography,
  Container,
  CssBaseline,
  Paper
} from "@mui/material";

import { AuthContext } from "../contexts/AuthContext";

export default function LoginPage() {
  const navigator = useNavigate();
  const [email, setEmail] = useState("");
  const [projectId, setProjectId] = useState("");

  const [error, setError] = useState("");

  const { setAuthData } = useContext(AuthContext);

  const handleSubmit = async event => {
    setError("");
    event.preventDefault();

    try {
      let backendURL =
        process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";
      const response = await fetch(
        `${backendURL}/dashboard/login/${email}/${projectId}`
      );

      if (!response.ok) {
        setError("Project not found OR Email is wrong.");
        throw new Error("Login failed");
      }

      const data = await response.json();
      console.log(`data`, data);
      if (data.admin == true) {
        setAuthData({
          email: email,
          admin: true
        });
        window.localStorage.setItem("admin", true);
      } else {
        setAuthData({
          email: email,
          admin: false
        });
        window.localStorage.setItem("admin", false);
      }

      window.localStorage.setItem("email", email);
      navigator("/");
      // You can save a token or user data in context/localStorage here
    } catch (error) {
      console.error("Error logging in:", error.message);
      setError("Project not found or Email is wrong.");
    }
  };

  return (
    <Container component="main" maxWidth="xs">
      <CssBaseline />
      <Paper elevation={6} sx={{ p: 4, mt: 8, borderRadius: 3 }}>
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center"
          }}
        >
          <Box sx={{ m: 1 }}>
            <img
              src="./logo512.png"
              alt="Logo"
              style={{ width: 60, height: 60, borderRadius: "50%" }}
            />
          </Box>
          <Typography align="center" component="h1" variant="h5">
            Simple Chat <br /> Admin Dashboard
          </Typography>
          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              label="MPG Email Address"
              type="email"
              autoFocus
              value={email}
              onChange={e => setEmail(e.target.value)}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              label="Project ID"
              type="text"
              value={projectId}
              onChange={e => setProjectId(e.target.value)}
            />
            {error && <Typography color="error">{error}</Typography>}

            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
            >
              Sign In
            </Button>
          </Box>
        </Box>
      </Paper>
    </Container>
  );
}
