import pytest
from playwright.sync_api import expect, sync_playwright

pytestmark = pytest.mark.gui


def test_homepage_loads(gui_app_server: str):
    """Verify that the homepage loads correctly."""
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as e:
            if "Executable doesn't exist" in str(e):
                pytest.skip("Playwright browsers not installed in this environment. Skipping GUI test.")
            raise

        page = browser.new_page()

        # Navigate to the local background server
        page.goto(gui_app_server, timeout=10000)

        # Verify title
        expect(page).to_have_title("ToDo-App")

        # Wait for the main UI to render by looking for static text
        expect(page.locator("body")).to_contain_text("Ny Uppgift", timeout=5000)
        expect(page.locator("body")).to_contain_text("Översikt")

        # We can also check if the theme toggle button exists
        expect(page.locator("button.q-btn").first).to_be_visible()

        browser.close()
