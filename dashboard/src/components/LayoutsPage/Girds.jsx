import React from "react";
import { Container, Typography } from "@mui/material";
import Grid from "@mui/material/Grid2"; // since it is Grid V2 it cannot be imported from @mui/material like other elements

import Paper from "@mui/material/Paper";
import { styled } from "@mui/material/styles";

function GridsComponent() {
  const Item = styled(Paper)(({ theme }) => ({
    backgroundColor: "#fff",
    ...theme.typography.body2,
    padding: theme.spacing(1),
    textAlign: "center",
    color: theme.palette.text.secondary,
    ...theme.applyStyles("dark", {
      backgroundColor: "#1A2027"
    })
  }));
  return (
    <>
      <Container maxWidth="lg">
        <Typography variant="body1">
          The role of grid in layout is to specify the placement of content and
          elements. While container specifies how wide the elements should be on
          the page, grid specifies what proportion of the page width should be
          allocated to the content within that grid.
        </Typography>
        <Typography variant="body1">
          In this version of material UI Grid V2 is used, the previous version
          is depricated.
        </Typography>
        <Typography variant="body1">
          For more details visit :{" "}
          <a
            href="https://mui.com/material-ui/react-grid/"
            target="_blank"
            rel="noreferrer"
          >
            MUI - Grid V2
          </a>
        </Typography>

        <Typography variant="body1">
          In this example, the max width of the container is set for large
          screen (Like laptop). Even if the screen is larger than a laptop,
          container's width remained fix. If the this screen shows on mobile or
          small tablets, the width of container decrease propoerly.
        </Typography>

        <Grid container spacing={2} sx={{ mt: 5, mb: 5 }}>
          <Grid size={{ xs: 12, md: 8 }}>
            <Item>xs=12 & md=8</Item>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Item>xs=12 & md=4</Item>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Item>xs=12 & md=4</Item>
          </Grid>
          <Grid size={{ xs: 12, md: 8 }}>
            <Item>xs=12 & md=8</Item>
          </Grid>
          <Grid size={12}>
            <Item>size={12}</Item>
          </Grid>
        </Grid>

        <Typography variant="body1">
          In this example, the size of elements for medium size displays is set
          to 8 or 4. it means for all displays with larger size the ratio of
          this grids are the same. In for xs and sm all elements are equal to
          12, means the full width of the container.
        </Typography>
        <Typography variant="body1" sx={{ mb: 5 }}>
          The latest element has size equal to 12. It means regardless of the
          display size it occupies the full width of the container.
        </Typography>
      </Container>
    </>
  );
}

export default GridsComponent;
