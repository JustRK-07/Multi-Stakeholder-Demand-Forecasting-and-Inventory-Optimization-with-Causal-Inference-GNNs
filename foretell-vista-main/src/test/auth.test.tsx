import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "@/components/AuthProvider";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { apiGet, setAuthToken } from "@/api/client";

describe("auth flows", () => {
  it("redirects protected routes to login when no session exists", async () => {
    window.localStorage.removeItem("retailcast.auth.token");

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={["/dashboard"]}>
          <Routes>
            <Route path="/login" element={<div>Login Screen</div>} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <div>Dashboard</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByText("Login Screen")).toBeInTheDocument());
  });

  it("clears auth token on unauthorized api response", async () => {
    setAuthToken("stale-token");
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("{}", { status: 401, headers: { "Content-Type": "application/json" } }),
    );

    await expect(apiGet("/api/v1/auth/session")).rejects.toThrow();
    expect(window.localStorage.getItem("retailcast.auth.token")).toBeNull();

    fetchSpy.mockRestore();
  });
});
