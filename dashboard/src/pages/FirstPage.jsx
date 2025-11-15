import React, { useContext, useEffect, useState } from "react";
import {
  Container,
  Typography,
  List,
  ListItem,
  ListItemText,
  Divider,
  Button,
  Box
} from "@mui/material";
import { useNavigate } from "react-router-dom";

import PageTracker from "../components/PageTracker";
import { AuthContext } from "../contexts/AuthContext";

function FirstPage() {
  const navigate = useNavigate();
  const { authData } = useContext(AuthContext);
  const [projectsList, setProjectsList] = useState([]);

  const goToPage = project_id => {
    navigate(`/project/${project_id}`);
  };

  useEffect(() => {
    const listThePorjects = async () => {
      try {
        let backendURL =
          process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";
        const response = await fetch(
          `${backendURL}/dashboard/projects/${authData.email}`
        );

        if (!response.ok) {
          throw new Error("failure!");
        }

        const data = await response.json();
        console.log("Projects:", data);
        setProjectsList(data);
      } catch (error) {
        console.error("Error logging in:", error.message);
        alert("There was an error to get the list.");
      }
    };
    listThePorjects();
  }, [authData.email]);

  return (
    <>
      <PageTracker arr={[]} />
      <Container maxWidth="md">
        <Typography variant="h4" gutterBottom sx={{ mt: 0 }}>
          List of your projects
        </Typography>

        {authData.admin && (
          <Box>
            <Button
              variant="contained"
              sx={{ mb: 2, mr: 1 }}
              color="success"
              size="small"
              onClick={() => {
                navigate(`/new_project`);
              }}
            >
              Create a new project
            </Button>
          </Box>
        )}

        <div>
          <List
            sx={{
              p: 0,
              width: "100%",
              borderRadius: 2,
              border: "1px solid",
              borderColor: "divider",
              backgroundColor: "background.paper"
            }}
            aria-label="mailbox folders"
          >
            {projectsList.map((item, index) => {
              return (
                <div key={index}>
                  <ListItem
                    sx={{
                      transition: "all 0.2s",
                      cursor: "pointer",
                      "&:hover": {
                        backgroundColor: "#eee"
                      }
                    }}
                    onClick={() => goToPage(item.project_id)}
                  >
                    <ListItemText
                      primary={`${item.project_id} - ${
                        item.active ? "active" : "deactive"
                      }`}
                    />
                  </ListItem>
                  <Divider component="li" />
                </div>
              );
            })}
          </List>
        </div>
      </Container>
    </>
  );
}

export default FirstPage;
