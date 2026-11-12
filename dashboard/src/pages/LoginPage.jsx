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
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");

  const { setAuthData } = useContext(AuthContext);

  const handleSubmit = async event => {
    setError("");
    event.preventDefault();

    try {
      const backendURL =
        process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";
      const response = await fetch(`${backendURL}/dashboard/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password })
      });

      if (!response.ok) {
        throw new Error("Login failed");
      }

      const data = await response.json();
      // use the email the token was issued for, so project requests match it
      const loggedInEmail = data.email || email.trim();
      setAuthData({
        email: loggedInEmail,
        admin: Boolean(data.admin)
      });
      window.localStorage.setItem("admin", Boolean(data.admin));
      window.localStorage.setItem("email", loggedInEmail);
      window.localStorage.setItem("token", data.token);
      navigator("/");
      // You can save a token or user data in context/localStorage here
    } catch (error) {
      console.error("Error logging in:", error.message);
      setError("Email or password is wrong.");
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
              label="Email Address"
              type="email"
              autoFocus
              value={email}
              onChange={e => setEmail(e.target.value)}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              label="Password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={e => setPassword(e.target.value)}
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
