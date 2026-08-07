import { test, expect } from '@playwright/test';
import { SidebarPage } from './pages/sidebar-page';

test.describe('Theme and Internationalization (i18n) E2E Tests', () => {
  test('can toggle dark mode and light mode', async ({ page }) => {
    const sidebar = new SidebarPage(page);
    await sidebar.gotoDashboard();

    // Click theme toggle button
    await sidebar.toggleTheme();

    // Toggle back
    await sidebar.toggleTheme();
    await expect(sidebar.themeToggleBtn).toBeVisible();
  });

  test('can toggle language between Swedish and English', async ({ page }) => {
    const sidebar = new SidebarPage(page);
    await sidebar.gotoDashboard();

    // Initially Swedish button label "Ny Uppgift"
    await expect(sidebar.newTaskBtn).toHaveText(/Ny Uppgift/i);

    // Switch language to English
    await sidebar.toggleLanguage();

    // Verify English button label "New Task"
    await expect(sidebar.newTaskBtn).toHaveText(/New Task/i);

    // Switch back to Swedish
    await sidebar.toggleLanguage();
    await expect(sidebar.newTaskBtn).toHaveText(/Ny Uppgift/i);
  });
});
