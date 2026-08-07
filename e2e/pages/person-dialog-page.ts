import { Page, Locator } from '@playwright/test';

export class PersonDialogPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async addPerson(name: string) {
    const dialog = this.page.locator('.q-dialog');
    const nameInput = dialog.locator('input').first();
    await nameInput.click();
    await nameInput.fill(name);
    await nameInput.press('Tab');

    const addBtn = dialog.locator('button.q-btn').filter({
      has: this.page.locator('.q-icon').filter({ hasText: 'add' }),
    }).first();
    await addBtn.click();

    // Wait for local list refresh inside dialog
    await this.page.locator('.q-dialog').getByText(name, { exact: true }).waitFor({ state: 'visible' });
    await this.page.waitForTimeout(500);
  }

  async closeDialog() {
    const dialog = this.page.locator('.q-dialog');
    const doneBtn = dialog.locator('button.q-btn').filter({ hasText: /Klart|Done/i }).first();
    await doneBtn.click();
    await dialog.waitFor({ state: 'hidden' });

    // Wait for controller refresh() and layout re-render to complete on backend
    await this.page.waitForTimeout(1000);
  }
}
