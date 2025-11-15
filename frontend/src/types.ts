// src/types.ts

export interface Message {
  session_id?: string;
  content_type?: "message" | "image";
  content: string | object;
  role: "assistant" | "user";
  timestamp?: string;
}
