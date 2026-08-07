import { test, expect } from '@playwright/test';
import { SidebarPage } from './pages/sidebar-page';

test.describe('ToDo App Base Initialization', () => {
  test('homepage loads and shows navigation elements', async ({ page }) => {
    const sidebar = new SidebarPage(page);
    await sidebar.gotoDashboard();

    // Verify page title
    await expect(page).toHaveTitle(/ToDo-App/);

    // Verify key sidebar elements
    await expect(sidebar.dashboardBtn).toBeVisible();
    await expect(sidebar.historyBtn).toBeVisible();
    await expect(sidebar.newTaskBtn).toBeVisible();
    await expect(sidebar.managePersonsBtn).toBeVisible();
  });

  test('can open new todo dialog', async ({ page }) => {
    const sidebar = new SidebarPage(page);
    await sidebar.gotoDashboard();
    await sidebar.openNewTaskDialog();

    // Verify dialog appears
    const dialogTitle = page.getByRole('heading', { name: /Ny Uppgift|New Task/i }).or(
      page.getByText(/Ny Uppgift|New Task/i).first()
    );
    await expect(dialogTitle).toBeVisible();
  });
});
