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
import { WithInfo } from "../components/InfoButton";

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

// shown by the info button next to each limit
const limitHelp = {
  max_conversations_per_participant: {
    title: "Max conversations per participant",
    what: "How many conversations one participant_id may send messages in, in this project. Opening the chat without sending a message (e.g. a page reload) does not count, and rounds 2, 3, ... of a multi-round study continue round 1. Not applied when the chat URL has no participant_id.",
    example:
      "1: a participant who has chatted and then reloads the survey page cannot start a second chat.",
    combined:
      "With a participant allowlist, only the listed IDs can chat, each at most once. The allowlist also makes the participant_id required, so this limit always applies."
  },
  max_turns: {
    title: "Max turns per conversation",
    what: "How many messages a participant may send in one conversation. In multi-round studies, messages copied from earlier rounds do not count. The chat closes after the last allowed message has been answered.",
    example: "10: after the 10th answered message the chat input closes.",
    combined:
      "With max conversations per participant 1, each participant gets at most 10 messages in total. With a token cap per conversation, whichever is reached first ends the chat."
  },
  max_tokens_per_conversation: {
    title: "Token cap per conversation",
    what: "Prompt and completion tokens one conversation may use. Each reply sends the whole chat history again, so usage grows with every turn.",
    example:
      "50000: a long chat ends once about 50,000 tokens are used, even if turns are left.",
    combined:
      "With max turns 20, it stops participants who paste long texts from making 20 turns expensive. Turns limit normal chats, the token cap limits unusual ones."
  },
  max_tokens_per_project: {
    title: "Token cap per project",
    what: "Total tokens all conversations of this project may use. Once reached, no new chats start and running chats end.",
    example:
      "5000000: the project stops at 5 million tokens. The usage table above shows how close you are and the estimated cost.",
    combined:
      "With a token cap per conversation of 50000, 5000000 covers at least 100 conversations that use their full cap. Set it to about participants × conversation cap, plus a margin."
  },
  rate_limit_messages: {
    title: "Rate limit",
    what: "How many conversation starts and messages are allowed within the rate limit window. Further attempts get a 'please wait' notice and the message returns to the input field.",
    example:
      "10 with a window of 60 seconds: at most 10 starts and messages per minute. A participant typing normally never hits this, a script sending messages does.",
    combined:
      "Counted per participant ID, each participant has their own limit. Counted per IP address, everyone behind the same IP shares it, so allow more for lab sessions on one network."
  },
  rate_limit_window_seconds: {
    title: "Rate limit window",
    what: "The time span the rate limit counts over, from 1 to 86400 seconds (one day). Only used when the rate limit is set. The window slides: a slot frees up as soon as the oldest counted message is older than the window.",
    example:
      "30 with a rate limit of 5: at most 5 starts and messages in any 30 seconds.",
    combined:
      "A rate limit of 100 with a window of 86400 is a daily quota of 100 starts and messages per participant, across all their conversations. It adds to max turns, which limits one conversation."
  },
  rate_limit_key: {
    title: "Rate limit counted per",
    what: "Participant ID counts per participant_id from the chat URL and falls back to the IP address when the URL has none. IP address always counts per IP.",
    example:
      "Participant ID for a Prolific study where every URL carries the participant's ID; IP address when the URL has no ID or anyone could invent one.",
    combined:
      "With a participant allowlist, Participant ID is the right choice because IDs cannot be invented. Behind a proxy or ingress, set TRUST_X_FORWARDED_FOR in the backend, or all participants share the proxy's IP."
  },
  participant_allowlist: {
    title: "Participant allowlist",
    what: "Participant IDs (e.g. Prolific IDs) allowed to start a conversation, one per line or comma-separated. Empty means everyone may join.",
    example:
      "Paste the Prolific IDs of your approved participants; a chat URL with any other ID, or without one, shows 'You are not registered for this study'.",
    combined:
      "With max conversations per participant 1, each listed participant chats exactly once. With allowed embedding origins, someone who copies the iframe to another site is blocked, and opening the link directly still needs a listed ID."
  },
  allowed_embed_origins: {
    title: "Allowed embedding origins",
    what: "Sites allowed to show the chat in an iframe, one origin per line. *. allows all subdomains. Empty means any site may embed it. Opening the chat link directly, e.g. the test chat, keeps working.",
    example:
      "https://*.qualtrics.com: the chat works inside your Qualtrics survey, but not when someone embeds it on their own site.",
    combined:
      "It stops other sites from using your chat and token budget, but not direct visits to the link. Add a participant allowlist and a rate limit for those."
  }
};

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
            <WithInfo key={key} info={limitHelp[key]}>
              <TextField
                fullWidth
                label={label}
                type="number"
                size="small"
                inputProps={{ min: 1, step: 1 }}
                value={limitsForm[key]}
                placeholder="No limit"
                InputLabelProps={{ shrink: true }}
                error={invalidFields.includes(key)}
                helperText={
                  invalidFields.includes(key)
                    ? "Must be a positive integer"
                    : " "
                }
                onChange={e =>
                  setLimitsForm({ ...limitsForm, [key]: e.target.value })
                }
              />
            </WithInfo>
          ))}
          <WithInfo info={limitHelp.rate_limit_window_seconds}>
            <TextField
              fullWidth
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
          </WithInfo>
          <WithInfo info={limitHelp.rate_limit_key}>
            <TextField
              fullWidth
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
          </WithInfo>
        </Box>

        <WithInfo info={limitHelp.participant_allowlist} sx={{ mt: 1 }}>
          <TextField
            label="Participant allowlist"
            multiline
            minRows={3}
            fullWidth
            size="small"
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
        </WithInfo>

        <WithInfo info={limitHelp.allowed_embed_origins} sx={{ mt: 2 }}>
          <TextField
            label="Allowed embedding origins"
            multiline
            minRows={2}
            fullWidth
            size="small"
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
        </WithInfo>

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
