import React from "react";

const BlinkingDots = () => {
  const dotStyle = {
    display: "inline-block",
    width: "10px",
    height: "10px",
    margin: "0 5px",
    borderRadius: "50%",
    backgroundColor: "black",
    animationName: "blink",
    animationDuration: "1.5s",
    animationIterationCount: "infinite",
    animationTimingFunction: "ease-in-out"
  };

  return (
    <>
      <style>
        {`
          @keyframes blink {
            0%, 80%, 100% { opacity: 0; }
            40% { opacity: 1; }
          }
        `}
      </style>
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center"
        }}
      >
        <span style={{ ...dotStyle, animationDelay: "0s" }}></span>
        <span style={{ ...dotStyle, animationDelay: "0.3s" }}></span>
        <span style={{ ...dotStyle, animationDelay: "0.6s" }}></span>
      </div>
    </>
  );
};

export default BlinkingDots;
