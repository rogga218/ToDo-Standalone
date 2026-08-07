import { test, expect } from '@playwright/test';
import { SidebarPage } from './pages/sidebar-page';
import { PersonDialogPage } from './pages/person-dialog-page';

test.describe('Person Management E2E Tests', () => {
  test('can create a new person and see them in assignment list', async ({ page }) => {
    const sidebar = new SidebarPage(page);
    const personDialog = new PersonDialogPage(page);

    await sidebar.gotoDashboard();
    await sidebar.openManagePersonsDialog();

    // Valid person name (letters only according to validation rules)
    const personName = `Testperson ${Math.floor(Math.random() * 1000).toString().replace(/\d/g, (d) => String.fromCharCode(65 + parseInt(d)))}`;

    // Add new person
    await personDialog.addPerson(personName);

    // Verify person is listed in dialog
    await expect(page.locator('.q-dialog').getByText(personName, { exact: true })).toBeVisible();

    // Close dialog
    await personDialog.closeDialog();
  });
});
