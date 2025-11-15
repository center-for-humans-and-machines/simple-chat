import React, { useState, useRef, useEffect } from "react";

import { Button } from "@mui/material";

const ChatPage: React.FC = ({ isTyping, setImageFile }) => {
  const [showTheButton, setShowTheButton] = useState(false);

  useEffect(() => {
    const modelsSupportImageUpload = ["gpt-4o", "qwen2.5-72b-instruct"];
    const location = window.location;
    const queryParams = new URLSearchParams(location.search);
    const isModelSetInQueryParam = queryParams.has("model");

    if (isModelSetInQueryParam) {
      const modelName = queryParams.get("model");
      if (modelsSupportImageUpload.includes(modelName)) {
        setShowTheButton(true);
      }
      if (queryParams.has("upload_image")) {
        if (queryParams.get("upload_image") == "false") {
          setShowTheButton(false);
        }
      }
    }
  }, []);

  const fileInputRef = useRef(null);

  const handleUpload = event => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        setImageFile(reader.result);
        event.target.value = ""; // reset the input file.
        // setIsTyping(false)
      };
      reader.readAsDataURL(file);
    }
  };

  const clickOnFileInput = () => {
    document.getElementById("fileinput")?.click();
  };

  return (
    <div>
      {showTheButton && (
        <div>
          <input
            type="file"
            id="fileinput"
            data-testid="upload-image-input"
            ref={fileInputRef}
            onChange={handleUpload}
            style={{ display: "none" }}
            accept="image/*"
          />
          <Button
            color="primary"
            aria-label="upload picture"
            component="span"
            onClick={clickOnFileInput}
            disabled={isTyping}
          >
            <i className="fas fa-camera" style={{ fontSize: "22px" }}></i>
          </Button>
        </div>
      )}
    </div>
  );
};

export default ChatPage;
