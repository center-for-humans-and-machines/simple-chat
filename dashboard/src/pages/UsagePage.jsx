import React, { useEffect, useState } from "react";
import {
  Typography,
  Container,
  Button,
  Box,
  TextField,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Divider
} from "@mui/material";
import { useNavigate, useParams } from "react-router-dom";

import PageTracker from "../components/PageTracker";
import {
  UsageStats,
  UsageByModelTable,
  formatTokens,
  formatCost
} from "../components/UsageTables";

const limitFields = [
  {
    key: "max_conversations_per_participant",
    label: "Max conversations per participant"
  },
  { key: "max_turns", label: "Max turns per conversation" },
  { key: "max_tokens_per_conversation", label: "Token cap per conversation" },
  { key: "max_tokens_per_project", label: "Token cap per project" }
];

const emptyLimitsForm = {
  max_conversations_per_participant: "",
  max_turns: "",
  max_tokens_per_conversation: "",
  max_tokens_per_project: "",
  participant_allowlist: ""
};

const limitsToForm = limits => ({
  ...Object.fromEntries(
    limitFields.map(({ key }) => [key, limits?.[key] ?? ""])
  ),
  participant_allowlist: (limits?.participant_allowlist || []).join("\n")
});

const formToLimits = form => ({
  ...Object.fromEntries(
    limitFields.map(({ key }) => [
      key,
      form[key] === "" ? null : parseInt(form[key], 10)
    ])
  ),
  participant_allowlist: form.participant_allowlist
    .split(/[\n,]/)
    .map(item => item.trim())
    .filter(item => item.length > 0)
});

function UsagePage() {
  const { project_id } = useParams();
  const navigate = useNavigate();

  const [usage, setUsage] = useState();
  const [limitsForm, setLimitsForm] = useState(emptyLimitsForm);
  const [saving, setSaving] = useState(false);

  const backendURL =
    process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";

  useEffect(() => {
    const getUsage = async () => {
      try {
        const response = await fetch(
          `${backendURL}/dashboard/usage/${project_id}`
        );

        if (!response.ok) {
          throw new Error("failure!");
        }

        setUsage(await response.json());
      } catch (error) {
        console.error("Error getting usage:", error.message);
        alert("There was an error to get the token usage.");
      }
    };

    const getLimits = async () => {
      try {
        const response = await fetch(
          `${backendURL}/dashboard/limits/${project_id}`
        );

        if (!response.ok) {
          throw new Error("failure!");
        }

        setLimitsForm(limitsToForm(await response.json()));
      } catch (error) {
        console.error("Error getting limits:", error.message);
        alert("There was an error to get the limits.");
      }
    };

    getUsage();
    getLimits();
  }, [project_id, backendURL]);

  const invalidFields = limitFields
    .filter(({ key }) => limitsForm[key] !== "")
    .filter(({ key }) => !/^[1-9]\d*$/.test(String(limitsForm[key])))
    .map(({ key }) => key);

  const saveLimits = async () => {
    setSaving(true);
    try {
      const response = await fetch(
        `${backendURL}/dashboard/limits/${project_id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(formToLimits(limitsForm))
        }
      );

      if (!response.ok) {
        throw new Error("Failed to update limits!");
      }

      setLimitsForm(limitsToForm(await response.json()));
      alert("Limits updated successfully.");
    } catch (error) {
      console.error("Error:", error.message);
      alert("There was an error updating the limits.");
    } finally {
      setSaving(false);
    }
  };

  const total = usage?.total;
  const projectCap = parseInt(limitsForm.max_tokens_per_project, 10);

  return (
    <>
      <PageTracker
        arr={[
          {
            title: "Project",
            link: `/project/${project_id}`,
            idToShow: project_id
          },
          {
            title: "Usage & limits",
            link: `/project/${project_id}/usage`
          }
        ]}
      />

      <Container maxWidth="md" sx={{ pb: 6 }}>
        <Typography variant="h4" gutterBottom sx={{ mt: 0 }}>
          Usage & limits "{project_id}"
        </Typography>

        <Typography variant="h6" sx={{ mt: 3, mb: 1 }}>
          Token usage
        </Typography>
        <UsageStats total={total} />
        {projectCap > 0 && total && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {formatTokens(total.total_tokens)} of {formatTokens(projectCap)}{" "}
            project tokens used (
            {Math.round((total.total_tokens / projectCap) * 100)}%).
          </Typography>
        )}

        <Typography variant="subtitle1" sx={{ mt: 2, mb: 1 }}>
          Per model
        </Typography>
        <UsageByModelTable rows={usage?.by_model || []} />

        <Typography variant="subtitle1" sx={{ mt: 2, mb: 1 }}>
          Per conversation
        </Typography>
        <TableContainer
          component={Paper}
          variant="outlined"
          sx={{ mb: 1, maxHeight: 360 }}
        >
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>Conversation</TableCell>
                <TableCell>Participant</TableCell>
                <TableCell>Model</TableCell>
                <TableCell align="right">Turns</TableCell>
                <TableCell align="right">Total tokens</TableCell>
                <TableCell align="right">Est. cost</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(usage?.by_conversation || []).length === 0 && (
                <TableRow>
                  <TableCell colSpan={6}>No usage recorded yet.</TableCell>
                </TableRow>
              )}
              {(usage?.by_conversation || []).map(row => (
                <TableRow
                  key={row.conversation_id}
                  hover
                  sx={{ cursor: "pointer" }}
                  onClick={() =>
                    navigate(
                      `/project/${project_id}/conversation/${row.conversation_id}`
                    )
                  }
                >
                  <TableCell sx={{ fontFamily: "monospace" }}>
                    {row.conversation_id.slice(0, 12)}
                  </TableCell>
                  <TableCell>{row.participant_id}</TableCell>
                  <TableCell>{row.models.join(", ")}</TableCell>
                  <TableCell align="right">{row.calls}</TableCell>
                  <TableCell align="right">
                    {formatTokens(row.total_tokens)}
                  </TableCell>
                  <TableCell align="right">
                    {row.has_unpriced_model ? "n/a" : formatCost(row)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        <Typography variant="caption" color="text.secondary" component="p">
          Participant chat tokens are counted with tiktoken (cl100k_base) and
          are estimates; /llm API calls use provider-reported usage. Costs use
          the list prices configured in the backend (
          <code>model_prices</code> in <code>configs.py</code>).
        </Typography>

        <Divider sx={{ my: 4 }} />

        <Typography variant="h6" sx={{ mb: 1 }}>
          Limits
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Leave a field empty for no limit. The allowlist takes one participant
          ID per line; when it is empty every participant may join.
        </Typography>

        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", sm: "1fr 1fr" },
            gap: 2
          }}
        >
          {limitFields.map(({ key, label }) => (
            <TextField
              key={key}
              label={label}
              type="number"
              size="small"
              inputProps={{ min: 1, step: 1 }}
              value={limitsForm[key]}
              placeholder="No limit"
              InputLabelProps={{ shrink: true }}
              error={invalidFields.includes(key)}
              helperText={
                invalidFields.includes(key) ? "Must be a positive integer" : " "
              }
              onChange={e =>
                setLimitsForm({ ...limitsForm, [key]: e.target.value })
              }
            />
          ))}
        </Box>

        <TextField
          label="Participant allowlist"
          multiline
          minRows={3}
          fullWidth
          size="small"
          sx={{ mt: 1 }}
          placeholder="Everyone allowed"
          InputLabelProps={{ shrink: true }}
          value={limitsForm.participant_allowlist}
          onChange={e =>
            setLimitsForm({
              ...limitsForm,
              participant_allowlist: e.target.value
            })
          }
        />

        <Button
          variant="contained"
          sx={{ mt: 2 }}
          disabled={saving || invalidFields.length > 0}
          onClick={saveLimits}
        >
          Save limits
        </Button>
      </Container>
    </>
  );
}

export default UsagePage;
