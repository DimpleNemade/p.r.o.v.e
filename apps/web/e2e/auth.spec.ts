import { test, expect } from "@playwright/test";

test("login screen is available", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Investigation workspace" })).toBeVisible();
});
