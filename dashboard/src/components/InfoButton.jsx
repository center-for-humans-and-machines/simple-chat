import React, { useState } from "react";
import { Box, IconButton, Popover, Typography } from "@mui/material";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import { infoStrings as text } from "../strings";

// info: { title, what, example, combined }
function InfoButton({ info }) {
  const [anchorEl, setAnchorEl] = useState(null);

  return (
    <>
      <IconButton
        size="small"
        aria-label={text.about(info.title)}
        onClick={e => setAnchorEl(e.currentTarget)}
      >
        <InfoOutlinedIcon fontSize="small" />
      </IconButton>
      <Popover
        open={Boolean(anchorEl)}
        anchorEl={anchorEl}
        onClose={() => setAnchorEl(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        transformOrigin={{ vertical: "top", horizontal: "right" }}
      >
        <Box sx={{ p: 2, maxWidth: 380 }}>
          <Typography variant="subtitle2" gutterBottom>
            {info.title}
          </Typography>
          <Typography variant="body2" sx={{ mb: 1.5 }}>
            {info.what}
          </Typography>
          <Typography variant="overline" color="text.secondary">
            {text.example}
          </Typography>
          <Typography variant="body2" sx={{ mb: 1.5 }}>
            {info.example}
          </Typography>
          <Typography variant="overline" color="text.secondary">
            {text.combined}
          </Typography>
          <Typography variant="body2">{info.combined}</Typography>
        </Box>
      </Popover>
    </>
  );
}

// a form field with its info button to the right
export function WithInfo({ info, sx, children }) {
  return (
    <Box sx={{ display: "flex", alignItems: "flex-start", gap: 0.5, ...sx }}>
      <Box sx={{ flex: 1, minWidth: 0 }}>{children}</Box>
      <Box sx={{ pt: 0.5 }}>
        <InfoButton info={info} />
      </Box>
    </Box>
  );
}

export default InfoButton;
