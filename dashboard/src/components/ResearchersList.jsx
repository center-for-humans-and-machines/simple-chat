import React, { useEffect, useState } from "react";
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography
} from "@mui/material";
import { useNavigate } from "react-router-dom";

import { authFetch } from "../authHeaders";

const PASSWORD_MIN_LENGTH = 8;

// Admin only: researchers with their projects, and a password reset
function ResearchersList() {
  const navigate = useNavigate();
  const [researchers, setResearchers] = useState([]);
  // researcher whose password is being set, or null
  const [selected, setSelected] = useState(null);
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const backendURL =
    process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";

  const loadResearchers = async () => {
    try {
      const response = await authFetch(`${backendURL}/dashboard/researchers`);
      if (!response.ok) {
        throw new Error("failure!");
      }
      setResearchers(await response.json());
    } catch (error) {
      console.error("Error getting researchers:", error.message);
      alert("There was an error to get the list of researchers.");
    }
  };

  useEffect(() => {
    loadResearchers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const openDialog = researcher => {
    setSelected(researcher);
    setPassword("");
    setPasswordConfirm("");
    setError("");
  };

  const savePassword = async () => {
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

    setSaving(true);
    try {
      const response = await authFetch(
        `${backendURL}/dashboard/researchers/${encodeURIComponent(
          selected.email
        )}/password`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ password })
        }
      );
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(
          typeof body.detail === "string"
            ? body.detail
            : "Failed to set the password."
        );
      }
      const email = selected.email;
      setSelected(null);
      await loadResearchers();
      alert(`Password for ${email} saved. Share it with them securely.`);
    } catch (error) {
      setError(error.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h5" gutterBottom>
        Researchers
      </Typography>

      {researchers.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          No researchers yet. They are added when you create a project for
          their e-mail.
        </Typography>
      ) : (
        <TableContainer
          sx={{ border: "1px solid", borderColor: "divider", borderRadius: 2 }}
        >
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>E-mail</TableCell>
                <TableCell>Projects</TableCell>
                <TableCell align="right">Password</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {researchers.map(researcher => (
                <TableRow key={researcher.email}>
                  <TableCell>
                    {researcher.email}
                    {!researcher.has_account && (
                      <Chip
                        label="no password"
                        size="small"
                        color="warning"
                        variant="outlined"
                        sx={{ ml: 1 }}
                      />
                    )}
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                      {researcher.projects.length === 0 && "–"}
                      {researcher.projects.map(project => (
                        <Chip
                          key={project.project_id}
                          label={project.project_id}
                          size="small"
                          variant={project.active ? "filled" : "outlined"}
                          onClick={() =>
                            navigate(`/project/${project.project_id}`)
                          }
                        />
                      ))}
                    </Box>
                  </TableCell>
                  <TableCell align="right">
                    <Button size="small" onClick={() => openDialog(researcher)}>
                      {researcher.has_account
                        ? "Reset password"
                        : "Set password"}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog
        open={selected !== null}
        onClose={() => setSelected(null)}
        fullWidth
        maxWidth="xs"
      >
        <DialogTitle>
          {selected?.has_account ? "Reset password" : "Set password"}
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            New password for <b>{selected?.email}</b> (at least{" "}
            {PASSWORD_MIN_LENGTH} characters). Their current password stops
            working.
          </DialogContentText>
          <TextField
            label="New password"
            type="password"
            autoComplete="new-password"
            fullWidth
            sx={{ mt: 2 }}
            value={password}
            onChange={e => setPassword(e.target.value)}
          />
          <TextField
            label="Repeat password"
            type="password"
            autoComplete="new-password"
            fullWidth
            sx={{ mt: 2 }}
            value={passwordConfirm}
            onChange={e => setPasswordConfirm(e.target.value)}
          />
          {error && (
            <Typography color="error" sx={{ mt: 2 }}>
              {error}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelected(null)}>Cancel</Button>
          <Button variant="contained" onClick={savePassword} disabled={saving}>
            Save password
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default ResearchersList;
