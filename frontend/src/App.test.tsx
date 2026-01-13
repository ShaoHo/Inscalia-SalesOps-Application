import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import App from "./App";

test("renders core SalesOps screens", () => {
  render(<App />);

  expect(
    screen.getByRole("heading", { name: "SalesOps Frontend Console" }),
  ).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Text Console" })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Pipeline Kanban" })).toBeInTheDocument();
  expect(
    screen.getByRole("heading", { name: "DeadLetter Queue" }),
  ).toBeInTheDocument();
});

test("updates the recent intents when submitting text console input", () => {
  render(<App />);

  const input = screen.getByLabelText("Natural language input");
  fireEvent.change(input, {
    target: { value: "Draft outreach to Atlas Logistics" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Send" }));

  expect(
    screen.getByText("Draft outreach to Atlas Logistics"),
  ).toBeInTheDocument();
});
