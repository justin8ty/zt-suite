import { expect, test } from '@playwright/test'

import { expectShellForSignedInUser, loginAsAdmin } from './helpers/auth'

test.describe('Integration: protected files', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page)
  })

  test('protected files page enforces the access gate from the frontend', async ({ page }) => {
    await page.getByRole('link', { name: 'Protected Files' }).click()

    await expectShellForSignedInUser(page)
    await expect(page.getByRole('heading', { name: 'Protected Files' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Access request' })).toBeVisible()

    const requestButton = page.getByRole('button', { name: 'Request files' })
    await expect(requestButton).toBeDisabled()

    const select = page.getByRole('combobox').first()
    if (await select.isVisible().catch(() => false)) {
      const optionCount = await select.locator('option').count()
      if (optionCount > 1) {
        await select.selectOption({ index: 1 })
        await expect(requestButton).toBeEnabled()
        await requestButton.click()
        await expect(page.getByText('Access Granted').or(page.getByRole('alert')).first()).toBeVisible()
      } else {
        await expect(page.getByText('Select compliant device')).toBeVisible()
      }
    } else {
      await page.getByPlaceholder('Compliant device ID').fill('999999')
      await expect(requestButton).toBeEnabled()
      await requestButton.click()
      await expect(page.getByRole('alert')).toBeVisible()
    }
  })
})
