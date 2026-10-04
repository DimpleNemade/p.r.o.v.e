import { defineConfig } from "@playwright/test";
const python =
  process.platform === "win32"
    ? "..\\..\\.venv\\Scripts\\python.exe"
    : "../../.venv/bin/python";
const npm = process.platform === "win32" ? "npm.cmd" : "npm";
export default defineConfig({
  testDir: "e2e",
  use: { baseURL: "http://127.0.0.1:5187", trace: "retain-on-failure" },
  webServer: [
    {
      command: `${python} ../../scripts/start_e2e_api.py`,
      url: "http://127.0.0.1:8017/api/v1/auth/csrf/",
      timeout: 120000,
      reuseExistingServer: false,
    },
    {
      command: `${npm} run dev -- --host 127.0.0.1 --port 5187 --strictPort`,
      env: { PROVE_API_PROXY: "http://127.0.0.1:8017" },
      url: "http://127.0.0.1:5187",
      timeout: 120000,
      reuseExistingServer: false,
    },
  ],
});
