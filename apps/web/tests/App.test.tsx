import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { afterEach, describe, expect, it, vi } from "vitest";
import App, { Login } from "../src/App";
import { api } from "../src/api";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("investigator workspace", () => {
  it("renders the unauthenticated login state", async () => {
    vi.spyOn(api, "me").mockRejectedValue(new Error("not signed in"));
    render(<App />);

    expect(await screen.findByRole("heading", { name: "Investigation workspace" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.getByText(/Synthetic data only/)).toBeInTheDocument();
  });

  it("surfaces a sign-in error without leaving the login screen", async () => {
    vi.spyOn(api, "login").mockRejectedValue(new Error("Invalid credentials."));
    render(<Login onLogin={vi.fn()} />);

    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid credentials.");
    expect(screen.getByRole("heading", { name: "Investigation workspace" })).toBeInTheDocument();
  });

  it("passes a successful login identity to the application shell", async () => {
    const onLogin = vi.fn();
    vi.spyOn(api, "login").mockResolvedValue({
      id: "user-1",
      username: "admin@example.test",
      displayName: "Admin",
      role: "administrator",
    });
    render(<Login onLogin={onLogin} />);

    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => expect(onLogin).toHaveBeenCalledWith(expect.objectContaining({ role: "administrator" })));
  });
});
