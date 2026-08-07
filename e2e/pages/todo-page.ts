import { Page, Locator } from '@playwright/test';

export class TodoPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async createTask(opts: {
    title: string;
    description: string;
    personName?: string;
    priority?: string;
    deadline?: string;
  }) {
    const dialog = this.page.locator('.q-dialog');

    // Title
    const titleInput = dialog.locator('.q-field').filter({ hasText: /Titel|Title/i }).locator('input');
    await titleInput.click();
    await titleInput.fill(opts.title);

    // Description
    const descInput = dialog.locator('.q-field').filter({ hasText: /Beskrivning|Description/i }).locator('textarea');
    await descInput.click();
    await descInput.fill(opts.description);
    await descInput.press('Tab');

    // Select Person (select specified person if visible, otherwise first available person)
    const personSelect = dialog.locator('.q-select').filter({ hasText: /Person/i }).first();
    await personSelect.click();
    await this.page.waitForTimeout(300);

    if (opts.personName) {
      const namedItem = this.page.locator('.q-menu .q-item').filter({ hasText: opts.personName }).first();
      if (await namedItem.count() > 0 && await namedItem.isVisible()) {
        await namedItem.click();
      } else {
        await this.page.locator('.q-menu .q-item').first().click();
      }
    } else {
      await this.page.locator('.q-menu .q-item').first().click();
    }

    // Save
    const saveBtn = dialog.locator('button.q-btn').filter({ hasText: /Spara|Save/i }).first();
    await saveBtn.click();
    await dialog.waitFor({ state: 'hidden' });
  }

  getTaskCard(title: string): Locator {
    return this.page.locator('.q-card').filter({ hasText: title });
  }

  async editTask(oldTitle: string, newTitle: string, newDescription?: string) {
    const card = this.getTaskCard(oldTitle);

    const editBtn = card.locator('button.q-btn').filter({
      has: this.page.locator('.q-icon').filter({ hasText: 'edit' }),
    }).first();
    await editBtn.click();

    const dialog = this.page.locator('.q-dialog');
    await dialog.waitFor({ state: 'visible' });

    const titleInput = dialog.locator('.q-field').filter({ hasText: /Titel|Title/i }).locator('input');
    await titleInput.click();
    await titleInput.fill(newTitle);

    if (newDescription !== undefined) {
      const descInput = dialog.locator('.q-field').filter({ hasText: /Beskrivning|Description/i }).locator('textarea');
      await descInput.click();
      await descInput.fill(newDescription);
    }

    const saveBtn = dialog.locator('button.q-btn').filter({ hasText: /Spara|Save/i }).first();
    await saveBtn.click();
    await dialog.waitFor({ state: 'hidden' });
  }

  async toggleTaskComplete(title: string) {
    const card = this.getTaskCard(title);
    const toggleBtn = card.locator('button.q-btn').filter({
      has: this.page.locator('.q-icon').filter({ hasText: /check|replay/ }),
    }).first();
    await toggleBtn.click();
  }

  async deleteTask(title: string) {
    const card = this.getTaskCard(title);
    const deleteBtn = card.locator('button.q-btn').filter({
      has: this.page.locator('.q-icon').filter({ hasText: 'delete' }),
    }).last();
    await deleteBtn.click();
  }
}
