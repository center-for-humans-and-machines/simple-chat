import { createTheme } from "@mui/material/styles";
// Create a custom theme
const CustomizedTheme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#1976d2"
    },
    secondary: {
      main: "#dc004e"
    },
    gray: {
      main: "#dcdcdc"
    }
  },
  typography: {
    fontFamily: "Roboto, Arial, sans-serif"
  }
});

export default CustomizedTheme;
