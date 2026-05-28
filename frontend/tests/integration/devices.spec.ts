import { expect, test } from '@playwright/test'

import { expectShellForSignedInUser, loginAsAdmin } from './helpers/auth'

test.describe('Integration: devices', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page)
  })

  test('devices page loads and can register a device through the frontend', async ({ page }) => {
    await page.getByRole('link', { name: 'Devices' }).click()

    await expectShellForSignedInUser(page)
    await expect(page.getByRole('heading', { name: 'Devices' })).toBeVisible()

    const hostname = `playwright-device-${Date.now()}`
    await page.getByPlaceholder('hostname').fill(hostname)
    await page.getByPlaceholder('OS version').fill('integration-test')
    await page.getByPlaceholder('Agent version').fill('playwright')
    await page.getByRole('button', { name: 'Register' }).click()

    await expect(page.getByText(hostname)).toBeVisible()
    await expect(page.getByText(/Compliant|Non-compliant/).first()).toBeVisible()
    await expect(page.getByRole('link', { name: 'Open' }).first()).toBeVisible()
  })
})
