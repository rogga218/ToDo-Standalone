---
name: playwright-testing
description: Utilize Playwright CLI to create, run, and debug end-to-end tests for the ToDo application. Use this skill when asked to write E2E tests, execute test suites, or debug failing browser tests.
license: MIT
compatibility: Requires Node.js and Playwright installed via npm (@playwright/test).
metadata:
  author: Antigravity
  version: "1.1"
---

# Playwright Testing Skill

Use this skill to create, run, and debug end-to-end (E2E) browser tests for the ToDo application using the Playwright CLI.

## Project Test Setup

- **Test Directory:** `e2e/` (e.g. `e2e/todo.spec.ts`)
- **Config File:** `playwright.config.ts`
- **Base URL:** `http://localhost:8080`
- **Server Lifecycle:** Playwright automatically starts the backend server (`python -m src.main`) via `webServer` config in `playwright.config.ts`. You do **not** need to manually launch the app before running tests.

## Core Commands

- **Run all E2E tests:** `npx playwright test`
- **Run a specific test file:** `npx playwright test e2e/todo.spec.ts`
- **Run tests in headed mode (visible browser):** `npx playwright test --headed`
- **Run tests in interactive UI mode:** `npx playwright test --ui`
- **Debug a test:** `npx playwright test --debug`
- **Show HTML test report:** `npx playwright show-report`

## Writing Tests

1. **Location & Naming:** Place test files in `e2e/` named `*.spec.ts`.
2. **Locators:** Use resilient locators (`getByRole`, `getByText`, `getByLabel`, `getByTestId`).
3. **Assertions:** Use web-first assertions (e.g., `await expect(locator).toBeVisible()`) which auto-wait.

### Example Test Structure (`e2e/todo.spec.ts`)

```typescript
import { test, expect } from '@playwright/test';

test.describe('ToDo App E2E Tests', () => {
  test('homepage loads and shows new task button', async ({ page }) => {
    await page.goto('/');

    // Verify page title
    await expect(page).toHaveTitle(/ToDo-App/);

    // Verify UI components and button
    const newTodoBtn = page.getByRole('button', { name: 'Ny Uppgift' });
    await expect(newTodoBtn).toBeVisible();
  });

  test('can open new todo dialog', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Ny Uppgift' }).click();

    // Verify modal dialog appears
    await expect(page.getByRole('heading', { name: 'Ny Uppgift' })).toBeVisible();
  });
});
```

## Debugging Workflow

If a test fails:
1. **Error Inspection:** Check locator timeouts or assertion mismatches in the terminal output.
2. **Review Traces & Screenshots:** Playwright records screenshots and traces on failure in `test-results/`.
3. **UI / Headed Mode:** Suggest running `npx playwright test --ui` to inspect page state interactively.
