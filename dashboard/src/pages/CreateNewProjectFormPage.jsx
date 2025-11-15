import React, { useState } from "react";
import {
  Typography,
  Button,
  TextareaAutosize,
  Container,
  TextField,
  Box
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import PageTracker from "../components/PageTracker";

function CreateNewProjectFormPage() {
  const [projectId, setProjectId] = useState("");
  const [email, setEmail] = useState("");
  const [systemMessage, setSystemMessage] = useState("");
  const navigate = useNavigate();
  const [error, setError] = useState("");

  const createSystemMessage = async () => {
    setError("");
    // --- Basic Validation ---
    if (!projectId.trim()) {
      alert("Please enter a project name.");
      return;
    }
    const validProjectId = /^[a-z0-9_]+$/;
    if (!validProjectId.test(projectId)) {
      alert(
        "Project name must contain only lowercase letters, numbers, and underscores (no spaces or special characters)."
      );
      return;
    }
    if (!email.trim() || !email.includes("@")) {
      alert("Please enter a valid email address.");
      return;
    }
    if (!systemMessage.trim()) {
      alert("Please enter a system message.");
      return;
    }

    const payload = {
      project_id: projectId.trim(),
      requested_by: email.trim(),
      system_message: systemMessage.trim()
    };

    try {
      let backendURL =
        process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";
      const response = await fetch(`${backendURL}/project/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        let errorText = `HTTP error! Status: ${response.status}`;

        // Try to extract error message from backend if provided
        try {
          const errorData = await response.json();
          if (errorData?.detail) {
            setError(errorData?.detail);
          }
        } catch {
          // ignore if body isn’t JSON
        }

        throw new Error(errorText);
      }

      const data = await response.json();

      if (data.status === true) {
        alert("✅ Project created successfully!");
        navigate("/");
      } else {
        // alert("⚠️ Failed to create project. Please try again. ");
        setError(data.detail);
      }
    } catch (error) {
      console.error("Error:", error);
      console.log(
        "❌ Something went wrong. Please check the console for details."
      );
    }
  };

  return (
    <>
      <PageTracker
        arr={[
          {
            title: "Create New Project",
            link: `#`,
            idToShow: ""
          }
        ]}
      />
      <Container maxWidth="md">
        <Typography variant="h4" gutterBottom sx={{ mt: 0 }}>
          Create a new project
        </Typography>

        <Typography variant="body1" gutterBottom sx={{ mt: 2 }}>
          Project ID
        </Typography>
        <TextField
          label="small letters, no space (use underscore instead)"
          variant="outlined"
          fullWidth
          value={projectId}
          onChange={e => setProjectId(e.target.value)}
        />

        <Typography variant="body1" gutterBottom sx={{ mt: 2 }}>
          E-mail
        </Typography>
        <TextField
          label="E-mail"
          variant="outlined"
          fullWidth
          value={email}
          onChange={e => setEmail(e.target.value)}
        />

        <Typography variant="body1" gutterBottom sx={{ mt: 2 }}>
          System Message
        </Typography>

        <TextareaAutosize
          minRows={5}
          maxRows={20}
          aria-label="system message"
          value={systemMessage}
          onChange={e => setSystemMessage(e.target.value)}
          style={{ width: "100%", padding: "10px" }}
        />

        <Button
          variant="contained"
          sx={{ mt: 2, mb: 4 }}
          onClick={createSystemMessage}
        >
          Create the project
        </Button>
        <Box sx={{ color: "red" }}>{error}</Box>
      </Container>
    </>
  );
}

export default CreateNewProjectFormPage;
