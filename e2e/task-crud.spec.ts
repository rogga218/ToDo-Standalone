import { test, expect } from '@playwright/test';
import { SidebarPage } from './pages/sidebar-page';
import { TodoPage } from './pages/todo-page';
import { PersonDialogPage } from './pages/person-dialog-page';

test.describe('Task Lifecycle (CRUD) E2E Tests', () => {
  let personName: string;

  test.beforeEach(async ({ page }) => {
    test.setTimeout(60000); // 60s timeout for complete CRUD flow
    const sidebar = new SidebarPage(page);
    const personDialog = new PersonDialogPage(page);

    await sidebar.gotoDashboard();

    const randomSuffix = Math.floor(Math.random() * 1000).toString().replace(/\d/g, (d) => String.fromCharCode(65 + parseInt(d)));
    personName = `Tester ${randomSuffix}`;
    await sidebar.openManagePersonsDialog();
    await personDialog.addPerson(personName);
    await personDialog.closeDialog();
  });

  test('full task lifecycle: create, edit, complete, delete', async ({ page }) => {
    const sidebar = new SidebarPage(page);
    const todoPage = new TodoPage(page);

    const taskTitle = `Task ${Date.now()}`;
    const taskDesc = 'Automated test task description';

    // 1. Create Task
    await sidebar.openNewTaskDialog();
    await todoPage.createTask({
      title: taskTitle,
      description: taskDesc,
    });

    // Verify task card appears on the board
    const card = todoPage.getTaskCard(taskTitle);
    await expect(card).toBeVisible();

    // 2. Edit Task
    const updatedTitle = `${taskTitle} Updated`;
    const updatedDesc = 'Updated task description';
    await todoPage.editTask(taskTitle, updatedTitle, updatedDesc);

    // Verify updated task title on board
    const updatedCard = todoPage.getTaskCard(updatedTitle);
    await expect(updatedCard).toBeVisible();

    // 3. Delete Task
    await todoPage.deleteTask(updatedTitle);
    await expect(todoPage.getTaskCard(updatedTitle)).not.toBeVisible();
  });
});
