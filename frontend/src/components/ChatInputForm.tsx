import React, { ChangeEvent, FormEvent } from "react";
import { TextField, Button, Box } from "@mui/material";
import UploadImage from "./UploadImage";

interface InputFormProps {
  newMessage: string;
  handleInputChange: (event: ChangeEvent<HTMLInputElement>) => void;
  handleSubmit: (event: FormEvent<HTMLFormElement>) => void;
  isTyping: boolean;
  setIsTyping: () => void;
  setImageFile: (src: string) => void;
  imageFile: string;
}
const InputForm: React.FC<InputFormProps> = ({
  newMessage,
  handleInputChange,
  handleSubmit,
  isTyping,
  setImageFile,
  imageFile
}) => {
  const removeImage = () => {
    setImageFile(null);
  };

  return (
    <Box sx={{}}>
      {imageFile && (
        <Box>
          <Box style={{ position: "relative", width: "250px" }}>
            <div
              data-testid="button-remove-preview"
              style={{
                position: "absolute",
                top: "4px",
                right: 0,
                background: "red",
                padding: "0px 3px",
                color: "white",
                cursor: "pointer"
              }}
              onClick={removeImage}
            >
              x
            </div>
            <img
              src={imageFile}
              alt="Preview"
              style={{
                marginLeft: "9px",
                width: "250px",
                objectFit: "cover",
                border: "1px solid #ccc",
                borderRadius: "5px",
                marginTop: "5px"
              }}
            />
          </Box>
        </Box>
      )}
      <Box
        component="form"
        sx={{
          display: "flex",
          alignItems: "center",
          padding: 1
        }}
        onSubmit={handleSubmit}
      >
        <TextField value={newMessage} onChange={handleInputChange} fullWidth />
        <Button type="submit" disabled={isTyping}>
          Send
        </Button>{" "}
        {/* Use isTyping here */}
        <UploadImage isTyping={isTyping} setImageFile={setImageFile} />
      </Box>
    </Box>
  );
};
export default InputForm;
export type { InputFormProps };
