import React, { useEffect, useState } from "react";
import {
  Typography,
  Container,
  Button,
  Box,
  TextField,
  List,
  ListItem,
  ListItemText,
  Divider
} from "@mui/material";
import { useNavigate, useParams } from "react-router-dom";

import PageTracker from "../components/PageTracker";

function ProjectPage() {
  const { project_id } = useParams();
  const navigate = useNavigate();

  const [projectInfo, setProjectInfo] = useState();
  const [projectId, setProjectId] = useState();
  const [conversationList, setConversationList] = useState([]);
  const [filteredList, setFilteredList] = useState([]);
  const [loadingText, setLoadingText] = useState("-");

  const searchFor = valueToSearch => {
    const keysToSearch = [
      "model",
      "participant_id",
      "experiment_id",
      "conversation_id",
      "_id"
    ];

    const filtered = conversationList.filter(item =>
      keysToSearch.some(key =>
        item[key]?.toLowerCase().includes(valueToSearch.toLowerCase())
      )
    );
    setFilteredList(filtered);
  };

  const goToPage = conversation_id => {
    navigate(`/project/${project_id}/conversation/${conversation_id}`);
  };

  const downloadConverstionsJSON = filtered => {
    let listToJson = conversationList;
    let nameExtention = "";
    if (filtered) {
      listToJson = filteredList;
      nameExtention = "withFilter";
    }

    const json = JSON.stringify(listToJson, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = `conversations-projectId_${projectId}-downloadDate_${new Date()}-${nameExtention}.json`;
    link.click();

    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    const getProjectId = () => {
      setProjectId(project_id);
      listTheConversations(project_id);
      getProjectInfo(project_id);
    };

    const getProjectInfo = async local_project_id => {
      try {
        let backendURL =
          process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";
        const response = await fetch(
          `${backendURL}/dashboard/project/${local_project_id}`
        );

        if (!response.ok) {
          throw new Error("failure!");
        }

        const data = await response.json();
        console.log("Projects:", data);
        setProjectInfo(data);
      } catch (error) {
        console.error("Error logging in:", error.message);
        alert("There was an error to get project info.");
      }
    };

    const listTheConversations = async local_project_id => {
      try {
        let backendURL =
          process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";
        const response = await fetch(
          `${backendURL}/dashboard/conversations/${local_project_id}`
        );

        if (!response.ok) {
          throw new Error("failure!");
        }

        const data = await response.json();
        console.log("Projects:", data);
        setConversationList(data);
        setFilteredList(data);
      } catch (error) {
        console.error("Error logging in:", error.message);
        alert("There was an error to get the list.");
      }
    };

    getProjectId();
  }, [project_id]);

  const toggleStatus = async () => {
    if (!window.confirm("Are you sure about this action?")) return;

    const oppositeStatus = !projectInfo?.active;

    try {
      let backendURL =
        process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";
      const response = await fetch(
        `${backendURL}/dashboard/toggle_status/${projectId}/${oppositeStatus}`
      );

      if (!response.ok) {
        throw new Error("failure!");
      }

      const data = await response.json();
      console.log("Projects status update:", data);
      window.location.reload();
    } catch (error) {
      console.error("Error logging in:", error.message);
      alert("There was an error in toggleStatus");
    }
  };

  const toggleOpenAiBackend = async () => {
    if (!window.confirm("Are you sure about this action?")) return;

    const oppositeStatus =
      projectInfo?.openai_backend === "azure" ? "openai" : "azure";
    console.log({ projectId, oppositeStatus });
    try {
      let backendURL =
        process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";
      const response = await fetch(
        `${backendURL}/dashboard/toggle_openai_backend/${projectId}/${oppositeStatus}`
      );

      if (!response.ok) {
        throw new Error("failure!");
      }

      const data = await response.json();
      console.log("Projects status update:", data);
      window.location.reload();
    } catch (error) {
      console.error("Error logging in:", error.message);
      alert("There was an error in toggleOpenAiBackend.");
    }
  };

  const handleEditClick = async () => {
    const userInput = prompt("Edit loading message:", loadingText);
    if (userInput !== null) {
      setLoadingText(userInput);

      try {
        const backendURL =
          process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";

        const response = await fetch(
          `${backendURL}/dashboard/update_loading_message`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify({
              project_id: projectId,
              loading_message: userInput
            })
          }
        );

        if (!response.ok) {
          throw new Error("Failed to update loading message!");
        }

        const data = await response.json();
        console.log("Updated loading message:", data);
        alert("Loading message updated successfully.");
      } catch (error) {
        console.error("Error:", error.message);
        alert("There was an error updating the loading message.");
      }
    }
  };

  return (
    <>
      <PageTracker
        arr={[
          {
            title: "Project",
            link: `/project/${projectId}`,
            idToShow: projectId
          }
        ]}
      />

      <Container maxWidth="md">
        <Typography variant="h4" gutterBottom sx={{ mt: 0 }}>
          Project "{projectId}"
        </Typography>

        <Typography variant="body1" gutterBottom sx={{ mt: 2 }}>
          Creation date : {projectInfo?.created_at}
        </Typography>

        <Typography variant="body1" gutterBottom sx={{ mt: 2 }}>
          Status : {projectInfo?.active ? "Active" : "Deactive"}
        </Typography>
        <Button
          variant="contained"
          sx={{ mb: 2, mr: 1 }}
          onClick={toggleStatus}
          color="warning"
          size="small"
        >
          {projectInfo?.active ? "deactivate" : "activate"}
        </Button>

        <Typography variant="body1" gutterBottom sx={{ mt: 2 }}>
          OpenAI backend : {projectInfo?.openai_backend}
        </Typography>
        <Button
          variant="contained"
          sx={{ mb: 2, mr: 1 }}
          onClick={toggleOpenAiBackend}
          color="warning"
          size="small"
        >
          {projectInfo?.openai_backend === "azure" ? "openai" : "azure"}
        </Button>

        <hr />

        <Typography variant="body1" gutterBottom sx={{ mt: 2 }}>
          System Message
        </Typography>

        <Box
          component="pre"
          variant="body1"
          gutterBottom
          sx={{
            p: 1,
            mt: 2,
            background: "#eee",
            wordWrap: "break-word",
            overflowWrap: "break-word",
            whiteSpace: "normal"
          }}
        >
          {projectInfo?.system_message}
        </Box>

        <Button
          variant="contained"
          sx={{ mt: 1, mb: 2, mr: 1 }}
          onClick={() => {
            navigate(`/systemmsg/${projectId}`);
          }}
        >
          Edit system message
        </Button>

        <hr />
        <div>
          <Typography variant="body1" gutterBottom sx={{ mt: 2 }}>
            Current Loading Message:
            <Box
              component="pre"
              variant="body1"
              gutterBottom
              sx={{ p: 1, mt: 2, background: "#eee" }}
            >
              {loadingText}
            </Box>
          </Typography>
          <Button
            variant="contained"
            sx={{ mt: 1, mb: 2 }}
            onClick={handleEditClick}
          >
            Edit Loading Message
          </Button>
        </div>
        <hr />

        <Button
          variant="contained"
          sx={{ mt: 3, mb: 2 }}
          onClick={() => downloadConverstionsJSON(false)}
        >
          Download Conversations as JSON
        </Button>

        <hr />

        <div style={{ padding: "20px 0px" }}>
          <TextField
            label="Search by Model, Participant ID, Experiment ID, Conversation ID"
            variant="outlined"
            fullWidth
            onChange={e => searchFor(e.target.value)}
          />

          <Button
            variant="contained"
            sx={{ mt: 1, mb: 2 }}
            onClick={() => downloadConverstionsJSON(true)}
          >
            Download Filtered Conversations as JSON
          </Button>
        </div>

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
          {filteredList.map((item, index) => {
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
                  onClick={() => goToPage(item.conversation_id)}
                >
                  <ListItemText
                    primary={`${item.conversation_id} - ${
                      item.created_at.split(" ")[0]
                    } - ${item.model}`}
                  />
                </ListItem>
                <Divider component="li" />
              </div>
            );
          })}
        </List>
      </Container>
    </>
  );
}

export default ProjectPage;
