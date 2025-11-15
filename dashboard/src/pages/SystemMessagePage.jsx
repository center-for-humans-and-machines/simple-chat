import React, { useEffect, useState } from "react";
import { Typography, Button, TextareaAutosize, Container } from "@mui/material";
import { useParams } from "react-router-dom";

import PageTracker from "../components/PageTracker";

function SystemMessagePage() {
  const { project_id } = useParams();
  const [projectId, setProjectId] = useState("");
  const [systemMessage, setSystemMessage] = useState("");
  const [projectInfo, setProjectInfo] = useState("");

  const updateSystemMessage = async () => {
    if (
      !window.confirm(
        "Are you sure you want to update the system message? it is not revertible."
      )
    )
      return;

    try {
      let backendURL =
        process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";
      const response = await fetch(
        `${backendURL}/dashboard/update_system_message`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            project_id: projectId,
            message: systemMessage
          })
        }
      );

      if (!response.ok) {
        throw new Error("failure!");
      }

      const data = await response.json();
      console.log("Projects:", data);
      alert("it is updated successfully.");
    } catch (error) {
      console.error("Error logging in:", error.message);
      alert("There was an error to update system message.");
    }
  };
  useEffect(() => {
    const getProjectId = () => {
      setProjectId(project_id);
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
    getProjectId();
  }, [project_id]);

  return (
    <>
      <PageTracker
        arr={[
          {
            title: "Project",
            link: `/project/${projectId}`,
            idToShow: projectId
          },
          {
            title: "System Message",
            link: `/systemmsg/${projectId}`,
            idToShow: ""
          }
        ]}
      />
      <Container maxWidth="md">
        <Typography variant="h4" gutterBottom sx={{ mt: 0 }}>
          System Message
        </Typography>
        <Typography variant="body1" gutterBottom sx={{ mt: 2 }}>
          Project ID: {projectId}
        </Typography>

        <Typography variant="body1" gutterBottom sx={{ mt: 2 }}>
          System Message
        </Typography>

        <TextareaAutosize
          rows={10}
          maxRows={30}
          aria-label="maximum height"
          defaultValue={projectInfo.system_message}
          onChange={event => {
            setSystemMessage(event.target.value);
          }}
          style={{ width: "100%", height: 300 }}
        />

        <Button
          variant="contained"
          sx={{ mt: 1, mb: 2 }}
          onClick={updateSystemMessage}
        >
          Update system message
        </Button>
      </Container>
    </>
  );
}

export default SystemMessagePage;
