import { test, expect } from '@playwright/test';
import { SidebarPage } from './pages/sidebar-page';

test.describe('Navigation and Sidebar Filters E2E Tests', () => {
  test('can navigate between Dashboard and History views', async ({ page }) => {
    const sidebar = new SidebarPage(page);

    await sidebar.gotoDashboard();
    await expect(page).toHaveURL(/.*board/);

    // Navigate to History
    await sidebar.historyBtn.click();
    await expect(page).toHaveURL(/.*history/, { timeout: 10000 });

    // Navigate back to Dashboard
    await sidebar.dashboardBtn.click();
    await expect(page).toHaveURL(/.*board/, { timeout: 10000 });
  });

  test('sidebar refresh button triggers page reload/update', async ({ page }) => {
    const sidebar = new SidebarPage(page);

    await sidebar.gotoDashboard();
    await sidebar.refreshBtn.click();
    await page.waitForLoadState('networkidle');
  });
});
