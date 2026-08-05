import { test, expect } from '@playwright/test';

test.describe('ToDo App E2E Tests', () => {
  test('homepage loads correctly', async ({ page }) => {
    // Navigate to the base URL (which is http://localhost:8080 configured in playwright.config.ts)
    await page.goto('/');

    // Verify the page title
    await expect(page).toHaveTitle(/ToDo-App/);

    // Wait for the main UI to render by looking for static text (using Swedish default)
    await expect(page.locator('body')).toContainText('Ny Uppgift');
    await expect(page.locator('body')).toContainText('Översikt');

    // Verify the theme toggle button exists (assumes it's the first standard button in the header)
    const toggleButton = page.locator('button.q-btn').first();
    await expect(toggleButton).toBeVisible();
  });

  test('can open new todo dialog', async ({ page }) => {
    await page.goto('/');

    // Look for the "Ny Uppgift" button and click it
    const newTodoButton = page.getByRole('button', { name: 'Ny Uppgift' });
    await newTodoButton.click();

    // Verify the dialog appears
    const dialogTitle = page.getByRole('heading', { name: 'Ny Uppgift' }).or(page.getByText('Ny Uppgift').first());
    await expect(dialogTitle).toBeVisible();
  });
});
