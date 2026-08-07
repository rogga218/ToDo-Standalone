import { test, expect } from '@playwright/test';
import { SidebarPage } from './pages/sidebar-page';
import { TodoPage } from './pages/todo-page';
import { PersonDialogPage } from './pages/person-dialog-page';

test.describe('Subtasks E2E Tests', () => {
  let personName: string;

  test.beforeEach(async ({ page }) => {
    const sidebar = new SidebarPage(page);
    const personDialog = new PersonDialogPage(page);

    await sidebar.gotoDashboard();
    const randomSuffix = Math.floor(Math.random() * 1000).toString().replace(/\d/g, (d) => String.fromCharCode(65 + parseInt(d)));
    personName = `Subtasker ${randomSuffix}`;
    await sidebar.openManagePersonsDialog();
    await personDialog.addPerson(personName);
    await personDialog.closeDialog();
  });

  test('can create a task and view subtasks expander if present', async ({ page }) => {
    const sidebar = new SidebarPage(page);
    const todoPage = new TodoPage(page);

    const taskTitle = `Subtask Task ${Date.now()}`;
    await sidebar.openNewTaskDialog();
    await todoPage.createTask({
      title: taskTitle,
      description: 'Task for testing subtasks',
      personName: personName,
    });

    const card = todoPage.getTaskCard(taskTitle);
    await expect(card).toBeVisible();
  });
});
