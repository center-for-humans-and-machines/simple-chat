import React, { useContext } from "react";
import {
  Typography,
  Button,
  ButtonGroup,
  List,
  ListItem,
  Box
} from "@mui/material";
import { AuthContext } from "../contexts/AuthContext";

function SamplePage() {
  const { authData, setAuthData } = useContext(AuthContext);

  return (
    <>
      <Typography variant="h4" gutterBottom sx={{ mt: 5 }}>
        SamplePage
      </Typography>
    </>
  );
}

export default SamplePage;
