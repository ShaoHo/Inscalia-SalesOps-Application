import { fireEvent, render, screen, within } from "@testing-library/react";
import { expect, test } from "vitest";

import App from "./App";

test("switching companies updates the contact panel", () => {
  render(<App />);

  fireEvent.click(
    screen.getByRole("button", { name: /Northwind Foods/i }),
  );

  const contactPanel = screen.getByTestId("contact-panel");

  expect(
    within(contactPanel).getByRole("heading", { name: "Elena Ramos" }),
  ).toBeInTheDocument();
  expect(within(contactPanel).getByText("Head of Sales")).toBeInTheDocument();
  expect(
    within(contactPanel).getByText("eramos@northwind.com"),
  ).toBeInTheDocument();
});

test("filters BANT records based on readiness", () => {
  render(<App />);

  fireEvent.change(screen.getByLabelText("BANT filter"), {
    target: { value: "Complete" },
  });

  const bantPanel = screen.getByTestId("bant-panel");

  expect(within(bantPanel).getByText("Atlas Logistics")).toBeInTheDocument();
  expect(
    within(bantPanel).queryByText("Inscalia Labs"),
  ).not.toBeInTheDocument();
});

test("editing BANT fields updates filter results", () => {
  render(<App />);

  fireEvent.change(screen.getByLabelText("BANT filter"), {
    target: { value: "Complete" },
  });

  const bantPanel = screen.getByTestId("bant-panel");
  const budgetSelect = within(bantPanel).getByLabelText(
    "Atlas Logistics budget",
  );
  fireEvent.change(budgetSelect, { target: { value: "Missing" } });

  expect(
    within(bantPanel).queryByText("Atlas Logistics"),
  ).not.toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("BANT filter"), {
    target: { value: "Needs attention" },
  });

  expect(within(bantPanel).getByText("Atlas Logistics")).toBeInTheDocument();
});
