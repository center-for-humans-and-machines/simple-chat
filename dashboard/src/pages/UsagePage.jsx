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
import { limitHelp, limitsStrings as text, usageStrings } from "../strings";

const limitFields = Object.entries(text.fieldLabels).map(
  ([key, label]) => ({ key, label })
);

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

const splitList = value =>
  value
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
        alert(usageStrings.errorGettingUsage);
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
        alert(text.errorGetting);
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
            : text.saveFailed
        );
      }

      setLimitsForm(limitsToForm(await response.json()));
      alert(text.saved);
    } catch (error) {
      console.error("Error:", error.message);
      alert(text.errorSaving(error.message));
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
            title: text.breadcrumbProject,
            link: `/project/${project_id}`,
            idToShow: project_id
          },
          {
            title: text.breadcrumbUsage,
            link: `/project/${project_id}/usage`
          }
        ]}
      />

      <Container maxWidth="md" sx={{ pb: 6 }}>
        <Typography variant="h4" gutterBottom sx={{ mt: 0 }}>
          {text.pageTitle(project_id)}
        </Typography>

        <Typography variant="h6" sx={{ mt: 3, mb: 1 }}>
          {usageStrings.tokenUsage}
        </Typography>
        <UsageStats total={total} />
        {projectCap > 0 && total && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {usageStrings.projectCapUsed(
              formatTokens(total.total_tokens),
              formatTokens(projectCap),
              Math.round((total.total_tokens / projectCap) * 100)
            )}
          </Typography>
        )}

        <Typography variant="subtitle1" sx={{ mt: 2, mb: 1 }}>
          {usageStrings.perModel}
        </Typography>
        <UsageByModelTable rows={usage?.by_model || []} />

        <Typography variant="subtitle1" sx={{ mt: 2, mb: 1 }}>
          {usageStrings.perConversation}
        </Typography>
        <TableContainer
          component={Paper}
          variant="outlined"
          sx={{ mb: 1, maxHeight: 360 }}
        >
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>{usageStrings.columns.conversation}</TableCell>
                <TableCell>{usageStrings.columns.participant}</TableCell>
                <TableCell>{usageStrings.columns.model}</TableCell>
                <TableCell align="right">{usageStrings.columns.turns}</TableCell>
                <TableCell align="right">
                  {usageStrings.columns.totalTokens}
                </TableCell>
                <TableCell align="right">
                  {usageStrings.columns.estCost}
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(usage?.by_conversation || []).length === 0 && (
                <TableRow>
                  <TableCell colSpan={6}>{usageStrings.noUsage}</TableCell>
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
                    {row.has_unpriced_model
                      ? usageStrings.notAvailable
                      : formatCost(row)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        <Typography variant="caption" color="text.secondary" component="p">
          {usageStrings.countingNote} (<code>model_prices</code> in{" "}
          <code>configs.py</code>).
        </Typography>

        <Divider sx={{ my: 4 }} />

        <Typography variant="h6" sx={{ mb: 1 }}>
          {text.heading}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {text.intro}
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
                placeholder={text.noLimit}
                InputLabelProps={{ shrink: true }}
                error={invalidFields.includes(key)}
                helperText={
                  invalidFields.includes(key)
                    ? text.mustBePositive
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
              label={text.windowLabel}
              type="number"
              size="small"
              inputProps={{ min: 1, max: 86400, step: 1 }}
              value={limitsForm.rate_limit_window_seconds}
              placeholder={String(defaultRateLimitWindow)}
              InputLabelProps={{ shrink: true }}
              error={invalidWindow}
              helperText={
                invalidWindow ? text.windowInvalid : " "
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
              label={text.keyLabel}
              size="small"
              value={limitsForm.rate_limit_key}
              helperText=" "
              onChange={e =>
                setLimitsForm({ ...limitsForm, rate_limit_key: e.target.value })
              }
            >
              <MenuItem value="participant">{text.keyParticipant}</MenuItem>
              <MenuItem value="ip">{text.keyIp}</MenuItem>
            </TextField>
          </WithInfo>
        </Box>

        <WithInfo info={limitHelp.participant_allowlist} sx={{ mt: 1 }}>
          <TextField
            label={text.allowlistLabel}
            multiline
            minRows={3}
            fullWidth
            size="small"
            placeholder={text.allowlistPlaceholder}
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
            label={text.originsLabel}
            multiline
            minRows={2}
            fullWidth
            size="small"
            placeholder={text.originsPlaceholder}
            helperText={text.originsHelper}
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
          {text.save}
        </Button>
      </Container>
    </>
  );
}

export default UsagePage;
