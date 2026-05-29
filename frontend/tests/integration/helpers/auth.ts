import { expect, type Page } from '@playwright/test'

export const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL ?? 'testadmin@zt-suite.dev'
export const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? 'integration-test-pw-123!'

export async function loginAsAdmin(page: Page) {
  await page.goto('/login')
  await page.getByLabel('Email').fill(ADMIN_EMAIL)
  await page.getByLabel('Password').fill(ADMIN_PASSWORD)
  await page.getByRole('button', { name: 'Sign in' }).click()

  // Expect redirect to dashboard (no MFA interruption)
  await expect(async () => {
    await expect(page).toHaveURL(/\/dashboard$/, { timeout: 10_000 })
    await expect(page.getByRole('heading', { name: 'Security dashboard' })).toBeVisible()
  }).toPass({ timeout: 15_000 })
}

export async function expectShellForSignedInUser(page: Page) {
  await expect(page.getByText('Zero-Trust Security Suite').first()).toBeVisible()
  await expect(page.getByRole('button', { name: /logout/i })).toBeVisible()
}
