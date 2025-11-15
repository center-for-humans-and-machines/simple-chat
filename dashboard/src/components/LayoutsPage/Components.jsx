import React from "react";
import { Container, Typography } from "@mui/material";

function ContainersComponent() {
  return (
    <>
      <Container>
        <Typography variant="body1" sx={{ textAlign: "center" }}>
          Followings are different size of containers. Various sizes can be used
          in differnet pages or components, but using them in nested structure
          is not recommended.
        </Typography>
        <Typography variant="body1" sx={{ textAlign: "center" }}>
          For more details visit :{" "}
          <a
            href="https://mui.com/material-ui/react-container/"
            target="_blank"
            rel="noreferrer"
          >
            MUI - Container
          </a>
        </Typography>
      </Container>
      <Container
        maxWidth="xs"
        sx={{ textAlign: "center", backgroundColor: "#d1cdb6" }}
      >
        maxWidth="sm"
      </Container>
      <Container
        maxWidth="sm"
        sx={{ textAlign: "center", backgroundColor: "#c6d1b6" }}
      >
        maxWidth="sm"
      </Container>
      <Container
        maxWidth="md"
        sx={{ textAlign: "center", backgroundColor: "#b6d1c8" }}
      >
        maxWidth="md"
      </Container>
      <Container
        maxWidth="lg"
        sx={{ textAlign: "center", backgroundColor: "#b6d1c8" }}
      >
        maxWidth="lg"
      </Container>
      <Container
        maxWidth="xl"
        sx={{ textAlign: "center", backgroundColor: "#c5b6d1" }}
      >
        maxWidth="xl"
      </Container>
    </>
  );
}

export default ContainersComponent;
