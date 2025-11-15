import { io } from "socket.io-client";

const baseUrl = process.env.REACT_APP_BACKEND_URL || "localhost:8000";

export const socket = io(baseUrl, {
  path: "/ws",
  transports: ["websocket"],
  autoConnect: false
});
