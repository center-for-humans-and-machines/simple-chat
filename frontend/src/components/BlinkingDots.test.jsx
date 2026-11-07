import React from "react";
import { render } from "@testing-library/react";
import BlinkingDots from "./BlinkingDots";

test("renders the typing indicator", () => {
  const { container } = render(<BlinkingDots />);

  expect(container.querySelectorAll("span")).toHaveLength(3);
});
