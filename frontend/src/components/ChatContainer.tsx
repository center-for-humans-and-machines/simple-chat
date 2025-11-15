import React, { FC, useEffect, useRef } from "react";
import { Box } from "@mui/material";
import ChatMessage from "./ChatMessage";
import { Message } from "../types";

interface ChatContainerProps {
  messages: Message[];
  setIsTypingFalse: any;
}

const ChatContainer: FC<ChatContainerProps> = ({
  messages,
  setIsTypingFalse
}) => {
  const messagesContainerRef = useRef<null | HTMLDivElement>(null);

  useEffect(() => {
    if (messagesContainerRef.current) {
      const { scrollHeight } = messagesContainerRef.current;
      messagesContainerRef.current.scrollTop = scrollHeight;
    }
    // console.log("messages", messages);
  }, [messages]);

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "80vh",
        p: 2,
        overflow: "auto"
      }}
    >
      <Box
        ref={messagesContainerRef}
        sx={{
          flexGrow: 1,
          width: "100%",
          overflow: "auto"
        }}
      >
        {messages.map((message, index) => (
          <ChatMessage
            key={index}
            content={message.content}
            type={message.type}
            role={message.role}
            setIsTypingFalse={setIsTypingFalse}
          />
        ))}
      </Box>
    </Box>
  );
};

export default ChatContainer;
