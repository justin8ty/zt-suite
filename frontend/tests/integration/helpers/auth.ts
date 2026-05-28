import { expect, type Page } from "@playwright/test";

export const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL ?? "admin@example.com";
export const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? "admin123";

export async function loginAsAdmin(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(ADMIN_EMAIL);
  await page.getByLabel("Password").fill(ADMIN_PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(async () => {
    if (page.url().includes("/mfa")) {
      throw new Error(
        "Seeded admin requires MFA. Disable MFA for this integration account or provide a dedicated non-MFA admin account.",
      );
    }
    await expect(
      page.getByRole("heading", { name: "Security dashboard" }),
    ).toBeVisible();
  }).toPass();
}

export async function expectShellForSignedInUser(page: Page) {
  await expect(
    page.getByText("Zero-Trust Security Suite").first(),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: /logout/i })).toBeVisible();
}
