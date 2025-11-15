import { io } from "socket.io-client";

const baseUrl =
  process.env.REACT_APP_BACKEND_SOCKET_URL || "http://localhost:8000";

export const socket = io(baseUrl, {
  path: "/ws",
  autoConnect: false,
  transports: ["websocket"]
});
