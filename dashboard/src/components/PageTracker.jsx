import React from "react";
import { Box, Breadcrumbs, Button } from "@mui/material";
import { useNavigate } from "react-router-dom";

function PageTracker({ arr }) {
  const navigate = useNavigate();

  const goToPage = url => {
    navigate(url);
  };

  return (
    <Box sx={{ pl: 2, pt: 2 }}>
      <Breadcrumbs separator=" > ">
        <Button
          sx={{ textTransform: "none" }}
          onClick={() => {
            goToPage("/");
          }}
        >
          Projects List
        </Button>

        {/* Clickable project */}
        {arr.map(item => {
          return (
            <Button
              sx={{ textTransform: "none" }}
              onClick={() => {
                goToPage(item.link);
              }}
            >
              {item.title} {item.idToShow && `"${item.idToShow}"`}
            </Button>
          );
        })}
      </Breadcrumbs>
    </Box>
  );
}

export default PageTracker;
