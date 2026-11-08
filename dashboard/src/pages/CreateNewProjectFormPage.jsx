import React, { useContext, useEffect, useState } from "react";
import {
  Typography,
  Button,
  TextareaAutosize,
  Container,
  TextField,
  MenuItem,
  Box
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import PageTracker from "../components/PageTracker";
import { AuthContext } from "../contexts/AuthContext";
import { authFetch } from "../authHeaders";

const PASSWORD_MIN_LENGTH = 8;

function CreateNewProjectFormPage() {
  const { authData } = useContext(AuthContext);
  const [projectId, setProjectId] = useState("");
  const [email, setEmail] = useState(authData.email);
  const [systemMessage, setSystemMessage] = useState("");
  const [model, setModel] = useState("");
  const [modelOptions, setModelOptions] = useState([]);
  const navigate = useNavigate();
  const [error, setError] = useState("");
  // "project": the project form; "password": password for a new researcher
  const [step, setStep] = useState("project");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");

  const backendURL =
    process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";

  useEffect(() => {
    const getModels = async () => {
      try {
        const response = await fetch(`${backendURL}/project/models`);

        if (!response.ok) {
          throw new Error("failure!");
        }

        const data = await response.json();
        setModelOptions(data.models);
        setModel(data.default);
      } catch (error) {
        console.error("Error getting models:", error.message);
      }
    };
    getModels();
  }, [backendURL]);

  // first step: check the form, then ask for a password if the email is new
  const submitProjectForm = async () => {
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

    try {
      const response = await authFetch(
        `${backendURL}/dashboard/researchers/${encodeURIComponent(email.trim())}`
      );
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      if (data.exists) {
        await registerProject(null);
      } else {
        setStep("password");
      }
    } catch (error) {
      console.error("Error:", error);
      setError("Could not check the researcher email. Please try again.");
    }
  };

  // second step: set the password the new researcher logs in with
  const submitPassword = async () => {
    setError("");
    if (password.length < PASSWORD_MIN_LENGTH) {
      setError(
        `The password must have at least ${PASSWORD_MIN_LENGTH} characters.`
      );
      return;
    }
    if (password !== passwordConfirm) {
      setError("The passwords do not match.");
      return;
    }
    await registerProject(password);
  };

  const registerProject = async researcherPassword => {
    const payload = {
      project_id: projectId.trim(),
      requested_by: email.trim(),
      system_message: systemMessage.trim(),
      model: model,
      researcher_password: researcherPassword
    };

    try {
      const response = await authFetch(`${backendURL}/project/register`, {
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
        navigate(`/project/${payload.project_id}`);
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

        {step === "password" ? (
          <>
            <Typography variant="body1" gutterBottom sx={{ mt: 2 }}>
              <b>{email.trim()}</b> is a new researcher. Set the password they
              will use to log in to the dashboard (at least{" "}
              {PASSWORD_MIN_LENGTH} characters), and share it with them
              securely.
            </Typography>
            <TextField
              label="Password"
              type="password"
              autoComplete="new-password"
              variant="outlined"
              fullWidth
              sx={{ mt: 2 }}
              value={password}
              onChange={e => setPassword(e.target.value)}
            />
            <TextField
              label="Repeat password"
              type="password"
              autoComplete="new-password"
              variant="outlined"
              fullWidth
              sx={{ mt: 2 }}
              value={passwordConfirm}
              onChange={e => setPasswordConfirm(e.target.value)}
            />
            <Box sx={{ display: "flex", gap: 2, mt: 2, mb: 4 }}>
              <Button
                variant="outlined"
                onClick={() => {
                  setError("");
                  setStep("project");
                }}
              >
                Back
              </Button>
              <Button variant="contained" onClick={submitPassword}>
                Create the project
              </Button>
            </Box>
            <Box sx={{ color: "red" }}>{error}</Box>
          </>
        ) : (
          <>
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
              Model
            </Typography>
            <TextField
              select
              label="used when the chat URL has no model parameter"
              variant="outlined"
              fullWidth
              value={modelOptions.includes(model) ? model : ""}
              onChange={e => setModel(e.target.value)}
            >
              {modelOptions.map(option => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </TextField>

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
              onClick={submitProjectForm}
            >
              Create the project
            </Button>
            <Box sx={{ color: "red" }}>{error}</Box>
          </>
        )}
      </Container>
    </>
  );
}

export default CreateNewProjectFormPage;
