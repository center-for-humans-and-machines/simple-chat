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
  Divider,
  MenuItem
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
  { key: "max_tokens_per_project", label: "Token cap per project" },
  {
    key: "rate_limit_messages",
    label: "Rate limit (starts and messages per window)"
  }
];

const defaultRateLimitWindow = 60;

const emptyLimitsForm = {
  max_conversations_per_participant: "",
  max_turns: "",
  max_tokens_per_conversation: "",
  max_tokens_per_project: "",
  rate_limit_messages: "",
  rate_limit_window_seconds: defaultRateLimitWindow,
  rate_limit_key: "participant",
  participant_allowlist: "",
  allowed_embed_origins: ""
};

const limitsToForm = limits => ({
  ...Object.fromEntries(
    limitFields.map(({ key }) => [key, limits?.[key] ?? ""])
  ),
  rate_limit_window_seconds:
    limits?.rate_limit_window_seconds ?? defaultRateLimitWindow,
  rate_limit_key: limits?.rate_limit_key || "participant",
  participant_allowlist: (limits?.participant_allowlist || []).join("\n"),
  allowed_embed_origins: (limits?.allowed_embed_origins || []).join("\n")
});

const splitList = text =>
  text
    .split(/[\n,]/)
    .map(item => item.trim())
    .filter(item => item.length > 0);

const formToLimits = form => ({
  ...Object.fromEntries(
    limitFields.map(({ key }) => [
      key,
      form[key] === "" ? null : parseInt(form[key], 10)
    ])
  ),
  rate_limit_window_seconds:
    form.rate_limit_window_seconds === ""
      ? defaultRateLimitWindow
      : parseInt(form.rate_limit_window_seconds, 10),
  rate_limit_key: form.rate_limit_key,
  participant_allowlist: splitList(form.participant_allowlist),
  allowed_embed_origins: splitList(form.allowed_embed_origins)
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
  const invalidWindow =
    limitsForm.rate_limit_window_seconds !== "" &&
    !(
      /^[1-9]\d*$/.test(String(limitsForm.rate_limit_window_seconds)) &&
      limitsForm.rate_limit_window_seconds <= 86400
    );

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
        const body = await response.json().catch(() => ({}));
        throw new Error(
          typeof body.detail === "string"
            ? body.detail
            : "Failed to update limits!"
        );
      }

      setLimitsForm(limitsToForm(await response.json()));
      alert("Limits updated successfully.");
    } catch (error) {
      console.error("Error:", error.message);
      alert(`There was an error updating the limits: ${error.message}`);
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
          ID per line; when it is empty every participant may join. The rate
          limit counts conversation starts and messages within the window, per
          participant ID (or per IP address when the chat URL has no participant
          ID) or per IP address.
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
          <TextField
            label="Rate limit window (seconds)"
            type="number"
            size="small"
            inputProps={{ min: 1, max: 86400, step: 1 }}
            value={limitsForm.rate_limit_window_seconds}
            placeholder={String(defaultRateLimitWindow)}
            InputLabelProps={{ shrink: true }}
            error={invalidWindow}
            helperText={
              invalidWindow ? "Must be between 1 and 86400 seconds" : " "
            }
            onChange={e =>
              setLimitsForm({
                ...limitsForm,
                rate_limit_window_seconds: e.target.value
              })
            }
          />
          <TextField
            select
            label="Rate limit counted per"
            size="small"
            value={limitsForm.rate_limit_key}
            helperText=" "
            onChange={e =>
              setLimitsForm({ ...limitsForm, rate_limit_key: e.target.value })
            }
          >
            <MenuItem value="participant">Participant ID</MenuItem>
            <MenuItem value="ip">IP address</MenuItem>
          </TextField>
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

        <TextField
          label="Allowed embedding origins"
          multiline
          minRows={2}
          fullWidth
          size="small"
          sx={{ mt: 2 }}
          placeholder="Any site may embed the chat"
          helperText="One origin per line, e.g. https://*.qualtrics.com. Only these sites may show the chat in an iframe."
          InputLabelProps={{ shrink: true }}
          value={limitsForm.allowed_embed_origins}
          onChange={e =>
            setLimitsForm({
              ...limitsForm,
              allowed_embed_origins: e.target.value
            })
          }
        />

        <Button
          variant="contained"
          sx={{ mt: 2 }}
          disabled={saving || invalidFields.length > 0 || invalidWindow}
          onClick={saveLimits}
        >
          Save limits
        </Button>
      </Container>
    </>
  );
}

export default UsagePage;
