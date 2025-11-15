import React, { useContext } from "react";
import { AppBar, Toolbar, Typography, Button, Box } from "@mui/material";
// import CustomizedTheme from "../theme";
// import { Link } from "react-router-dom";

import { AuthContext } from "../contexts/AuthContext";

// import Box from "@mui/material/Box";
// import Drawer from "@mui/material/Drawer";
// import List from "@mui/material/List";
// import Divider from "@mui/material/Divider";
// import ListItem from "@mui/material/ListItem";
// import ListItemButton from "@mui/material/ListItemButton";
// import ListItemIcon from "@mui/material/ListItemIcon";
// import ListItemText from "@mui/material/ListItemText";
// import InboxIcon from "@mui/icons-material/MoveToInbox";
// import MailIcon from "@mui/icons-material/Mail";

// const drawerWidth = 240;

function Header() {
  const { setAuthData } = useContext(AuthContext);

  const onLogout = () => {
    window.localStorage.removeItem("email");
    setAuthData({
      email: ""
    });
  };

  return (
    <>
      <AppBar
        position="static"
        sx={{
          backgroundColor: theme => theme.palette.gray.main,
          color: "#383838",
          zIndex: theme => theme.zIndex.drawer + 1
        }}
      >
        <Toolbar>
          {/* Flex container to space between title and logout */}
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6">Simple Chat - Admin Dashboard</Typography>
          </Box>

          {/* Logout Button */}
          <Button color="inherit" onClick={onLogout}>
            Logout
          </Button>
        </Toolbar>
      </AppBar>
      {/* <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: {
            width: drawerWidth,
            boxSizing: "border-box"
          }
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: "auto" }}>
          <List>
            {[{
              text: "Socket Restful call",
              to: "/call"
            }, {
              text: "Elements",
              to: "/elements"
            }, ].map((item, index) => (
              <ListItem key={item.text} disablePadding>
                <ListItemButton component={Link} to={item.to}>
                  <ListItemText primary={item.text} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
          <Divider />
        </Box>
      </Drawer> */}
    </>
  );
}

export default Header;
