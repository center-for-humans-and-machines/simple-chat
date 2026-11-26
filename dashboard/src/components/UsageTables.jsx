import React from "react";
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography
} from "@mui/material";
import { usageStrings as text } from "../strings";

export const formatTokens = value => (value || 0).toLocaleString("en-US");

export const formatCost = bucket => {
  if (!bucket) return "-";
  const cost = `$${bucket.estimated_cost_usd.toFixed(4)}`;
  return bucket.has_unpriced_model ? `≥ ${cost}` : cost;
};

export function UsageStat({ label, value }) {
  return (
    <Paper
      variant="outlined"
      sx={{ p: 2, flex: "1 1 160px", minWidth: 160, borderRadius: 2 }}
    >
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="h5" sx={{ fontVariantNumeric: "tabular-nums" }}>
        {value}
      </Typography>
    </Paper>
  );
}

export function UsageStats({ total }) {
  return (
    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 2, mb: 2 }}>
      <UsageStat
        label={text.promptTokens}
        value={formatTokens(total?.prompt_tokens)}
      />
      <UsageStat
        label={text.completionTokens}
        value={formatTokens(total?.completion_tokens)}
      />
      <UsageStat
        label={text.totalTokens}
        value={formatTokens(total?.total_tokens)}
      />
      <UsageStat label={text.estimatedCostUsd} value={formatCost(total)} />
    </Box>
  );
}

const numberCell = { fontVariantNumeric: "tabular-nums" };

export function UsageByModelTable({ rows }) {
  return (
    <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>{text.columns.model}</TableCell>
            <TableCell align="right">{text.columns.calls}</TableCell>
            <TableCell align="right">{text.columns.prompt}</TableCell>
            <TableCell align="right">{text.columns.completion}</TableCell>
            <TableCell align="right">{text.columns.total}</TableCell>
            <TableCell align="right">{text.columns.estCost}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.length === 0 && (
            <TableRow>
              <TableCell colSpan={6}>{text.noUsage}</TableCell>
            </TableRow>
          )}
          {rows.map(row => (
            <TableRow key={row.model}>
              <TableCell>{row.model}</TableCell>
              <TableCell align="right" sx={numberCell}>
                {formatTokens(row.calls)}
              </TableCell>
              <TableCell align="right" sx={numberCell}>
                {formatTokens(row.prompt_tokens)}
              </TableCell>
              <TableCell align="right" sx={numberCell}>
                {formatTokens(row.completion_tokens)}
              </TableCell>
              <TableCell align="right" sx={numberCell}>
                {formatTokens(row.total_tokens)}
              </TableCell>
              <TableCell align="right" sx={numberCell}>
                {row.has_unpriced_model ? text.notAvailable : formatCost(row)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
