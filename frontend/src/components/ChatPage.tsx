import React, { useState, ChangeEvent, FormEvent, useEffect } from "react";
import ChatContainer from "./ChatContainer";
import ChatInputForm from "./ChatInputForm";
import { Box } from "@mui/material";
import { Message } from "../types";
import BlinkingDots from "./BlinkingDots";
import { socket } from "../socket";

const ChatPage: React.FC = () => {
  const [sessionId, setSessionId] = useState("");
  const [participantId, setParticipantId] = useState("");
  const [messages, setMessages] = useState([]);

  const [newMessage, setNewMessage] = useState<string>("");
  const [isTyping, setIsTyping] = useState<boolean>(true);
  const [imageFile, setImageFile] = useState(null);

  const [urlParams, setUrlParams] = useState<{ [key: string]: any }>({});
  const [projectInfo, setProjectInfo] = useState(null);

  useEffect(() => {
    const searchParams = new URLSearchParams(window.location.search);
    let params: { [key: string]: any } = {};
    for (let [key, value] of searchParams) {
      params[key] = value;
    }
    console.log("url param info: ", params);
    setUrlParams(params);
  }, []);

  useEffect(() => {
    if (!urlParams.pid) return;
    socket.emit("fetch_project_info", { project_id: urlParams.pid });
  }, [urlParams.pid]);

  const sending_initial_message = async sessionId => {
    const location = window.location;
    const searchParams = new URLSearchParams(location.search);
    let params: { [key: string]: any } = {};
    for (let pair of searchParams) {
      const [key, value] = pair;
      params[key] = value;
    }

    // pid is project_id
    if ("pid" in params) {
      await socket.emit("initial_message_to_server", {
        data: params,
        session_id: sessionId
      });
    } else {
      alert("PID is not set.");
      console.log("pid is not set. params: ", params);
      setIsTyping(true);
    }
  };

  useEffect(() => {
    socket.connect();

    socket.on("connect", () => {
      console.log("socket connect is called");
    });

    socket.on("session_id", async data => {
      console.log("session_id event: ", data);
      setIsTyping(false); // user can send message after getting the session id.
      setSessionId(data.session_id);
      await sending_initial_message(data.session_id);
    });

    socket.on("set_participant_id", data => {
      console.log("set_participant_id event: ", data);
      setParticipantId(data.participant_id);
    });

    socket.on("message_to_client", data => {
      if (data.type === "message") {
        setIsTyping(true);
        setMessages(prevMessages => [...prevMessages, data.data]);
      } else if (data.type === "stream") {
        setMessages(prevMessages => {
          let updatedMessages = [...prevMessages];
          const lastMessage = updatedMessages[updatedMessages.length - 1];
          if (lastMessage) {
            updatedMessages[updatedMessages.length - 1] = {
              ...lastMessage,
              content: (lastMessage.content || "") + data.data.content
            };
          }
          return updatedMessages;
        });
      }
    });

    socket.on("pid_not_found", async data => {
      if (data.message.includes("deactivated")) {
        alert("This project is deactivated.");
      } else if (data.message.includes("not found")) {
        alert("PID not found.");
      } else {
        alert("This project is not accessible.");
      }
      console.log("project with this pid did not found", data);
      setIsTyping(true);
    });

    socket.on("project_info", data => {
      if (data.error) {
        console.error("Error:", data.error);
        return;
      }
      console.log("project_info event: ", data);
      setProjectInfo(data);
    });
  }, []);

  const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    setNewMessage(event.target.value);
  };

  const handleSendClick = async () => {
    // Check if newMessage length is greater than 0
    if (newMessage.length === 0) {
      return;
    }

    let message: Message = {
      role: "user",
      content: newMessage
    };

    if (imageFile) {
      message = {
        role: "user",
        content_type: "image",
        content: {
          prompt: newMessage,
          image: imageFile.split(",")[1] // base64
        }
      };
      const image_message_to_add_locally = {
        content: [
          { type: "text", text: newMessage },
          {
            type: "image_url",
            image_url: {
              url: imageFile
            }
          }
        ],
        role: "user",
        timestamp: Date.now(),
        type: "image"
      };

      setMessages(prevMessages => [
        ...prevMessages,
        image_message_to_add_locally
      ]);
      await socket.emit("image_message", {
        data: message,
        session_id: sessionId,
        participant_id: participantId
      });
    } else {
      const text_message_to_add_locally = {
        session_id: "local",
        content: message.content,
        role: "user",
        timestamp: Date.now(),
        experiment_id: "local",
        participant_id: "local",
        type: "text"
      };
      setMessages(prevMessages => [
        ...prevMessages,
        text_message_to_add_locally
      ]);
      await socket.emit("text_message", {
        data: message,
        session_id: sessionId,
        participant_id: participantId
      });
    }

    console.log("ChatPage.handleSendClick", message);

    // sendMessage(message);

    setImageFile(null);
    setNewMessage("");
    setIsTyping(true);
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    handleSendClick();
  };

  // useEffect(() => {
  //   const lastMessage = messages[messages.length - 1];
  //   if (messages.length && lastMessage.role === "assistant") {
  //     setIsTyping(false);
  //   }
  // }, [messages]);

  const setIsTypingFalse = () => {
    setIsTyping(false);
  };
  return (
    <>
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          height: "98vh",
          maxWidth: "800px",
          width: "100%",
          margin: "auto"
        }}
      >
        <ChatContainer
          messages={messages}
          setIsTypingFalse={setIsTypingFalse}
        />
        <div
          style={{
            display: "flex",
            justifyContent: "left",
            alignItems: "center",
            marginLeft: "1rem",
            marginBottom: "0.65rem"
          }}
        >
          {isTyping && (
            <>
              <span>{projectInfo?.loading_message}</span>
              <BlinkingDots />
            </>
          )}
        </div>
        <ChatInputForm
          newMessage={newMessage}
          handleInputChange={handleInputChange}
          handleSubmit={handleSubmit}
          isTyping={isTyping}
          setImageFile={setImageFile}
          imageFile={imageFile}
        />
      </Box>
    </>
  );
};

export default ChatPage;
