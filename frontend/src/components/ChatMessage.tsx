import React, { FC, useEffect, useState, useRef, useMemo } from "react";
import { Box } from "@mui/material";
import Prism from "react-syntax-highlighter/dist/cjs/prism";
import { dark } from "react-syntax-highlighter/dist/cjs/styles/prism";

interface ChatMessageProps {
  content: string;
  role: "assistant" | "user";
  type?: "text" | "image";
  setIsTypingFalse: any;
}

/**
 * Utilities to convert bullet and numbered lists without duplication.
 */
function convertBulletLists(input: string): string {
  const lines = input.split(/\r?\n/);
  let output = "";
  let inList = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const match = line.match(/^[-*]\s+(.*)$/);
    if (match) {
      if (!inList) {
        output += "<ul>\n";
        inList = true;
      }
      output += `<li>${match[1]}</li>\n`;
    } else {
      if (inList) {
        output += "</ul>\n";
        inList = false;
      }
      output += line + "\n";
    }
  }
  if (inList) output += "</ul>\n";

  return output;
}

function convertNumberedLists(input: string): string {
  const lines = input.split(/\r?\n/);
  let output = "";
  let inList = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) {
      // Blank line: just add a newline without closing the list
      output += "\n";
      continue;
    }

    const match = line.match(/^(\d+)\.\s+(.*)$/);
    if (match) {
      // Start an <ol> if we aren't already in one
      if (!inList) {
        output += "<ol>\n";
        inList = true;
      }
      output += `<li>${match[2]}</li>\n`;
    } else {
      // If it's not a numbered item and we were in a <ol>, close it
      if (inList) {
        output += "</ol>\n";
        inList = false;
      }
      // Add this line as normal text
      output += line + "\n";
    }
  }

  // If we finish while still in a list, close it
  if (inList) output += "</ol>\n";

  return output;
}

/**
 * Pipeline function for transformations:
 * - hr
 * - listItems (using our bullet/numbered list converters)
 * - bold
 * - italic
 * - headings
 * - trim
 */
const processTextPipeline = (text: string, steps: string[]) => {
  const availableSteps: Record<string, (input: string) => string> = {
    hr: input => {
      const hrPattern = /^(?:[-*_]){3,}\s*$/gm;
      return input.replace(hrPattern, "<hr />");
    },
    listItems: input => {
      let result = convertBulletLists(input);
      result = convertNumberedLists(result);
      return result;
    },
    bold: input => {
      const parts = input.split(/(\*\*.*?\*\*)/);
      return parts
        .map(part => {
          if (part.startsWith("**") && part.endsWith("**")) {
            return `<strong>${part.slice(2, -2)}</strong>`;
          }
          return part;
        })
        .join("");
    },
    italic: input => {
      const parts = input.split(/(\*.*?\*)/);
      return parts
        .map(part => {
          if (part.startsWith("*") && part.endsWith("*")) {
            return `<em>${part.slice(1, -1)}</em>`;
          }
          return part;
        })
        .join("");
    },
    headings: input => {
      const headingPattern = /^(#{1,6})\s+(.*)$/gm;
      return input.replace(headingPattern, (_, hashes, headingContent) => {
        const level = hashes.length;
        return `<h${level}>${headingContent}</h${level}>`;
      });
    },
    trim: input => input.trim()
  };

  const pipeline = steps.map(step => availableSteps[step]);

  let result = text;
  for (const stepFn of pipeline) {
    if (stepFn) {
      result = stepFn(result);
    }
  }
  return result;
};

/**
 * Detects code blocks delimited by triple backticks and converts them
 * into { language, code } objects. Everything else remains as plain strings.
 */
const processText = (text: string, steps: string[]) => {
  const transformed = processTextPipeline(text, steps);

  const codeParts = transformed.split(/(```[\s\S]*?```)/);
  return codeParts.map(part => {
    if (part.startsWith("```") && part.endsWith("```")) {
      const codeContent = part.slice(3, -3).trim();
      const [language, ...codeLines] = codeContent.split("\n");
      const code = codeLines.join("\n");
      return { language: language.trim(), code };
    }
    return part;
  });
};

const ChatMessage: FC<ChatMessageProps> = ({
  content,
  type,
  role,
  setIsTypingFalse
}) => {
  const [displayedText, setDisplayedText] = useState("");
  const [index, setIndex] = useState(0);
  const lastTimeout = useRef<any | null>(null);

  // Typing effect
  useEffect(() => {
    if (!content) {
      console.warn("ChatMessage: `content` is empty or undefined.");
      return;
    }

    if (role === "user") {
      if (type == "image") {
        setDisplayedText(content[0].text);
      } else {
        setDisplayedText(content);
      }
      setIsTypingFalse?.();
    } else {
      if (index < content.length) {
        const timer = setTimeout(() => {
          setDisplayedText(prev => prev + content[index]);
          setIndex(prev => prev + 1);
        }, 20);
        lastTimeout.current = timer;
        return () => clearTimeout(timer);
      } else if (index === content.length && content.length > 0) {
        // ✅ Schedule one final timeout after the last character
        lastTimeout.current = setTimeout(() => {
          setIsTypingFalse?.();
        }, 100); // enough to ensure render completes
      }
    }

    // Cleanup in case component unmounts
    return () => {
      if (lastTimeout.current) clearTimeout(lastTimeout.current);
    };
  }, [index, content, role]);

  // Only apply the formatting pipeline if the role is "assistant"
  const pipelineSteps = ["hr", "bold", "italic", "headings", "trim"];

  const processedParts = useMemo(() => {
    if (role !== "assistant") {
      return [];
    }
    let tempDisplayedText = displayedText
      .replace("<think>\n\n</think>", "")
      .replace(/^\n\n/, "");

    return processText(tempDisplayedText, pipelineSteps);
  }, [displayedText, role, pipelineSteps]);
  return (
    <Box
      sx={{
        bgcolor: role === "user" ? "lightblue" : "lightyellow",
        color: "black",
        p: 3,
        m: 1,
        borderRadius: 5,
        wordWrap: "break-word",
        overflow: "visible",
        textOverflow: "ellipsis",
        whiteSpace: "pre-wrap"
      }}
    >
      <span style={{ fontFamily: "monospace" }}>
        <span style={{ fontWeight: "bold" }}>
          {role === "user" ? "You" : "Assistant"}:
        </span>{" "}
        {role === "assistant" &&
          processedParts.map((part, idx) => {
            // Regular text/HTML
            if (typeof part === "string") {
              return (
                <span key={idx} dangerouslySetInnerHTML={{ __html: part }} />
              );
            }
            // Code block object
            if (typeof part === "object" && part.language && part.code) {
              return (
                <Prism
                  key={idx}
                  language={part.language}
                  style={dark}
                  wrapLongLines
                >
                  {part.code}
                </Prism>
              );
            }
            return null;
          })}
        {role != "assistant" && type === "image" && (
          <div>
            <img
              src={content[1]["image_url"]["url"]}
              style={{ width: "200px" }}
              alt="Chat-generated visual"
            />
            <p>{displayedText}</p>
          </div>
        )}
        {role != "assistant" && type === "text" && <span>{displayedText}</span>}
      </span>
    </Box>
  );
};

export default ChatMessage;
