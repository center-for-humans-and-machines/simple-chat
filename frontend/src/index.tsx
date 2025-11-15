// Sentry initialization should be imported first!
import "./instrument";
import React from "react";
import { createRoot } from "react-dom/client";
import ChatPage from "./components/ChatPage";

const container = document.getElementById("root");
const root = createRoot(container!);
root.render(
  <>
    <ChatPage />
  </>
);
