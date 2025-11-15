import React, { useEffect, useState } from "react";
import { Typography, Container, Box, Paper, Button } from "@mui/material";
// import { AuthContext } from "../contexts/AuthContext";
import { useParams } from "react-router-dom";
import PageTracker from "../components/PageTracker";

function ConversationPage() {
  const { project_id, conversation_id } = useParams();
  // const { authData, setAuthData } = useContext(AuthContext);
  const [conversationId, setConversationId] = useState();
  const [conversationInfo, setConversationInfo] = useState();

  const downloadConverstionJSON = () => {
    const json = JSON.stringify(conversationInfo, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = `conversation-conversationId_${conversationId}-downloadDate_${new Date()}.json`;
    link.click();

    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    const getConversationId = () => {
      setConversationId(conversation_id);
      getConversationInfo(conversation_id);
    };

    const getConversationInfo = async local_conversation_id => {
      try {
        let backendURL =
          process.env.REACT_APP_BACKEND_URL || "http://localhost:8000"; // process.env.REACT_APP_BACKEND_URL ||
        const response = await fetch(
          `${backendURL}/dashboard/conversation/${local_conversation_id}`
        );

        if (!response.ok) {
          throw new Error("failure!");
        }

        const data = await response.json();
        setConversationInfo(data);
      } catch (error) {
        console.error("Error logging in:", error.message);
        alert("There was an error to get conversation info.");
      }
    };

    getConversationId();
  }, [conversation_id]);

  const JsonSnippet = ({ data }) => {
    return (
      <Paper
        elevation={3}
        sx={{ p: 1, backgroundColor: "#f5f5f5", overflowX: "auto", mt: 3 }}
      >
        <Box
          component="pre"
          sx={{
            m: 0,
            fontFamily: "monospace",
            fontSize: "0.85rem",
            lineHeight: 1.4,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word"
          }}
        >
          <code>{JSON.stringify(data, null, 2)}</code>
        </Box>
      </Paper>
    );
  };

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
            title: "Conversation",
            link: ``,
            idToShow: conversation_id
          }
        ]}
      />
      <Container maxWidth="md">
        <Typography variant="h4" gutterBottom sx={{ mt: 0 }}>
          Conversation "{conversationId}"
          <Button
            variant="contained"
            sx={{ mt: 3, mb: 2 }}
            onClick={downloadConverstionJSON}
          >
            Download Conversation as JSON
          </Button>
          <JsonSnippet data={conversationInfo} />
        </Typography>
      </Container>
    </>
  );
}

export default ConversationPage;
