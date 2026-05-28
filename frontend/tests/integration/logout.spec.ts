import { expect, test } from '@playwright/test'

import { loginAsAdmin } from './helpers/auth'

test.describe('Integration: logout/session protection', () => {
  test('logout returns to login and protected routes are inaccessible', async ({ page }) => {
    await loginAsAdmin(page)

    await page.getByRole('button', { name: 'Logout' }).click()

    await expect(page).toHaveURL(/\/login$/)
    await expect(page.getByRole('heading', { name: 'Sign in to ZT Suite' })).toBeVisible()

    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/login$/)
    await expect(page.getByRole('heading', { name: 'Sign in to ZT Suite' })).toBeVisible()
  })
})
