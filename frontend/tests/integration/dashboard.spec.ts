import { expect, test } from '@playwright/test'

import { expectShellForSignedInUser, loginAsAdmin } from './helpers/auth'

test.describe('Integration: dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page)
  })

  test('dashboard loads security metrics and data-health status', async ({ page }) => {
    await expectShellForSignedInUser(page)
    await expect(page.getByRole('heading', { name: 'Security dashboard' })).toBeVisible()
    await expect(page.getByLabel('Security metrics')).toBeVisible()

    await expect(page.getByText('Total devices')).toBeVisible()
    await expect(page.getByText('Open alerts')).toBeVisible()
    await expect(page.getByText('Recent traffic')).toBeVisible()
    await expect(page.getByText('Access failures')).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Data health' })).toBeVisible()
  })
})
