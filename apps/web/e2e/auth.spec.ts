import { Page, test, expect } from "@playwright/test";

async function login(page: Page) {
  await page.goto("/");
  await page.getByLabel("Username").fill("investigator@example.test");
  await page.getByLabel("Password").fill("ChangeMe-Phase3-only");
  await page.getByRole("button", { name: "Sign in" }).click();
}

test("core investigator workflow from login to audit history", async ({
  page,
}) => {
  page.on("pageerror", (error) => console.log(`PAGEERROR: ${error.message}`));
  await login(page);
  await expect(page.getByRole("heading", { name: "Cases" })).toBeVisible();
  await page.getByRole("button", { name: /DEMO-PHASE3-0001/ }).click();
  await expect(page).toHaveURL(/\/cases\/.*\/overview/);

  await page.getByRole("button", { name: "Evidence", exact: true }).click();
  await page
    .getByRole("button", { name: "Details", exact: true })
    .first()
    .click();
  await expect(page.getByText("EVIDENCE DETAIL")).toBeVisible();
  const verification = page.waitForResponse(
    (response) =>
      response.url().includes("/verify/") &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Verify integrity" }).click();
  expect((await verification).status()).toBe(200);
  await expect(page.getByText("EVIDENCE DETAIL")).toBeVisible();
  const processing = page.waitForResponse(
    (response) =>
      response.url().includes("/jobs/") &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Start processing" }).click();
  expect((await processing).status()).toBe(201);

  await page.getByRole("button", { name: "Artifacts", exact: true }).click();
  await page
    .getByRole("button", { name: /Open detail/ })
    .first()
    .click();
  await expect(page.getByText("ARTIFACT DETAIL")).toBeVisible();
  await expect(page.getByText("Provenance chain")).toBeVisible();

  await page.getByRole("button", { name: "Findings", exact: true }).click();
  await page
    .getByLabel("Finding text")
    .fill("The E2E workflow observed a synthetic metadata artifact.");
  await page.getByRole("button", { name: "Create draft finding" }).click();
  const e2eFinding = page
    .getByRole("button", { name: /The E2E workflow observed/ })
    .last();
  await expect(e2eFinding).toBeVisible();
  await e2eFinding.click();
  await expect(page.getByLabel("Support reference")).toBeVisible();
  await page.getByLabel("Support reference").selectOption({ index: 1 });
  await page.getByRole("button", { name: "Attach support" }).click();
  await expect(page.getByText("FINDING REVIEW")).toBeVisible();
  await page.getByRole("button", { name: "Submit revision", exact: true }).click();
  await expect(page.getByText("State:")).toContainText("submitted");
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await page.goto("/");
  await page.getByLabel("Username").fill("reviewer@example.test");
  await page.getByLabel("Password").fill("ChangeMe-Phase3-only");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.getByRole("button", { name: /DEMO-PHASE3-0001/ }).click();
  await page.getByRole("button", { name: "Findings", exact: true }).click();
  await page.getByRole("button", { name: /The E2E workflow observed/ }).click();
  await page.getByLabel("Review comments or revision reason").fill("Independently checked exact supporting metadata and provenance.");
  await page.getByRole("button", { name: "Start independent review", exact: true }).click();
  await page.getByRole("button", { name: "Approve revision", exact: true }).click();
  await expect(page.getByText("State:")).toContainText("approved");
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await login(page);
  await page.getByRole("button", { name: /DEMO-PHASE3-0001/ }).click();

  await page.getByRole("button", { name: "Report", exact: true }).click();
  await page.getByRole("button", { name: "Generate report preview" }).click();
  await expect(
    page.getByText("DEVELOPMENT DRAFT", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText(/Development draft\. Not court-ready/).last(),
  ).toBeVisible();

  await page.getByRole("button", { name: "Create export package", exact: true }).click();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("link", { name: "Download verified package" }).click();
  const download = await downloadPromise;
  await download.saveAs(test.info().outputPath("handoff.zip"));
  await page.getByRole("button", { name: "Audit", exact: true }).click();
  await expect(page.getByText("processing.completed").first()).toBeVisible();
  await expect(page.getByText("report.draft_generated").first()).toBeVisible();
});
