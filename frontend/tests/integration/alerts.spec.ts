import { expect, test } from '@playwright/test'

import { expectShellForSignedInUser, loginAsAdmin } from './helpers/auth'

test.describe('Integration: alerts', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page)
  })

  test('alerts page loads and acknowledges an open alert when one exists', async ({ page }) => {
    await page.getByRole('link', { name: 'Alerts' }).click()

    await expectShellForSignedInUser(page)
    await expect(page.getByRole('heading', { name: 'Alerts' })).toBeVisible()
    await expect(page.getByText('Triage reported anomalies')).toBeVisible()
    await expect(page.getByRole('combobox').first()).toBeVisible()

    const acknowledgeButton = page.getByRole('button', { name: 'Acknowledge' }).first()
    if (await acknowledgeButton.isVisible().catch(() => false)) {
      await acknowledgeButton.click()
      await expect(page.getByText('Acknowledged').first()).toBeVisible()
    } else {
      await expect(page.getByText(/No alerts found|Open|Acknowledged/).first()).toBeVisible()
    }
  })
})
