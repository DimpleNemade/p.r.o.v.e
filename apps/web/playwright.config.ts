import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "e2e",
  use: { baseURL: "http://localhost:5173", trace: "retain-on-failure" },
  webServer: [
    {
      command:
        "powershell.exe -NoProfile -ExecutionPolicy Bypass -File ../../scripts/start_e2e_api.ps1",
      url: "http://127.0.0.1:8000/api/v1/auth/csrf/",
      timeout: 120000,
      reuseExistingServer: true,
    },
    {
      command: "npm.cmd run dev -- --host 127.0.0.1",
      url: "http://localhost:5173",
      timeout: 120000,
      reuseExistingServer: true,
    },
  ],
});
