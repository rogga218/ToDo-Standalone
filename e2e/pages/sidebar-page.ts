import { Page, Locator } from '@playwright/test';

export class SidebarPage {
  readonly page: Page;
  readonly dashboardBtn: Locator;
  readonly historyBtn: Locator;
  readonly newTaskBtn: Locator;
  readonly managePersonsBtn: Locator;
  readonly themeToggleBtn: Locator;
  readonly languageToggleBtn: Locator;
  readonly refreshBtn: Locator;

  constructor(page: Page) {
    this.page = page;
    this.dashboardBtn = page.locator('button.q-btn').filter({ hasText: /Översikt|Dashboard/i });
    this.historyBtn = page.locator('button.q-btn').filter({ hasText: /Historik|History/i });
    this.newTaskBtn = page.locator('button.q-btn').filter({ hasText: /Ny Uppgift|New Task/i });
    this.managePersonsBtn = page.locator('button.q-btn').filter({ hasText: /HANTERA PERSONER|MANAGE PERSONS/i });
    this.themeToggleBtn = page.locator('button.q-btn').filter({
      has: page.locator('.q-icon').filter({ hasText: /dark_mode|light_mode/ }),
    }).first();
    this.languageToggleBtn = page.locator('button.q-btn').filter({ hasText: /🇸🇪|🇬🇧/ }).first();
    this.refreshBtn = page.locator('button.q-btn').filter({ hasText: /Uppdatera|Refresh/i });
  }

  async gotoDashboard() {
    await this.page.goto('/board');
    await this.page.waitForLoadState('domcontentloaded');
  }

  async gotoHistory() {
    await this.historyBtn.click();
    await this.page.waitForURL('**/history');
  }

  async openNewTaskDialog() {
    await this.page.waitForTimeout(300);
    await this.newTaskBtn.click();
    await this.page.waitForSelector('.q-dialog', { state: 'visible', timeout: 10000 });
  }

  async openManagePersonsDialog() {
    await this.page.waitForTimeout(300);
    await this.managePersonsBtn.click();
    await this.page.waitForSelector('.q-dialog', { state: 'visible', timeout: 10000 });
  }

  async toggleTheme() {
    await this.themeToggleBtn.click();
  }

  async toggleLanguage() {
    await this.languageToggleBtn.click();
  }

  async filterByPriority(priorityText: string) {
    const prioritySelect = this.page.locator('.q-select').filter({ hasText: /Prioritet|Priority/i }).first();
    await prioritySelect.click();
    await this.page.locator('.q-menu .q-item').filter({ hasText: priorityText }).first().click();
  }

  async filterByPerson(personText: string) {
    const personSelect = this.page.locator('.q-select').filter({ hasText: /Person/i }).first();
    await personSelect.click();
    await this.page.locator('.q-menu .q-item').filter({ hasText: personText }).first().click();
  }
}
