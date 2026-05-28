import { expect, test } from '@playwright/test'

import { ADMIN_EMAIL, loginAsAdmin } from './helpers/auth'

test.describe('Integration: authentication', () => {
  test('invalid login is rejected and stays on login page', async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel('Email').fill('wrong@example.com')
    await page.getByLabel('Password').fill('wrong-password')
    await page.getByRole('button', { name: 'Sign in' }).click()

    await expect(page.getByRole('alert')).toBeVisible()
    await expect(page).toHaveURL(/\/login$/)
    await expect(page.getByRole('heading', { name: 'Sign in to ZT Suite' })).toBeVisible()
  })

  test('valid admin login opens the dashboard', async ({ page }) => {
    await loginAsAdmin(page)

    await expect(page).toHaveURL(/\/dashboard$/)
    await expect(page.getByText(ADMIN_EMAIL).first()).toBeVisible()
  })
})
