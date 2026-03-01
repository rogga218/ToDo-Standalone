from nicegui import ui

from src.config import logger
from src.ui.controller import ToDoController
from src.ui.theme import inject_dark_mode_script


def setup_routes():
    @ui.page("/")
    def index():
        inject_dark_mode_script()
        ui.navigate.to("/board")

    @ui.page("/board")
    async def board_page(page: int = 0):
        try:
            inject_dark_mode_script()
            controller = ToDoController()
            await controller.initialize()
            await controller.render_layout("board", page)
        except Exception as e:
            logger.error(f"Error loading board page: {e}")
            ui.label(f"Ett fel uppstod vid laddning av sidan: {e}").classes("text-red-500")

    @ui.page("/history")
    async def history_page():
        try:
            inject_dark_mode_script()
            controller = ToDoController()
            await controller.initialize()
            await controller.render_layout("history")
        except Exception as e:
            logger.error(f"Error loading history page: {e}")
            ui.label(f"Ett fel uppstod vid laddning av sidan: {e}").classes("text-red-500")
