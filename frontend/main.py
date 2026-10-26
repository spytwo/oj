import os
from datetime import datetime

import flet as ft
import httpx

API_URL = os.getenv("API_URL", "http://oj:8018")


class OJApp:
    def __init__(self, page: ft.Page):
        self.app_page = page

        self.current_theme = None
        self.current_subtheme = None

        self.header = ft.Text(
            value="Темы",
            size=24,
            weight=ft.FontWeight.BOLD,
        )

        self.back_button = ft.TextButton(
            content="← Назад",
            visible=False,
            on_click=self.go_back,
        )

        self.input_field = ft.TextField(
            label="Название темы",
            expand=True,
            on_submit=self.add_item,
        )

        self.add_button = ft.Button(
            content="Добавить",
            on_click=self.add_item,
        )

        self.items_list = ft.ListView(
            expand=True,
            spacing=6,
        )

        self.status_text = ft.Text(
            value="",
            color="red",
            selectable=True,
        )

        self.build_ui()

        self.app_page.run_task(self.load_themes)

    # --------------------------------------------------
    # Интерфейс
    # --------------------------------------------------

    def build_ui(self):
        self.app_page.add(
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self.back_button,
                            self.header,
                        ],
                    ),
                    ft.Row(
                        controls=[
                            self.input_field,
                            self.add_button,
                        ],
                    ),
                    self.status_text,
                    ft.Divider(),
                    self.items_list,
                ],
                expand=True,
                spacing=12,
            )
        )

    def update_page(self):
        self.app_page.update()

    def show_error(self, message: str):
        self.status_text.value = message
        self.update_page()

    def clear_error(self):
        self.status_text.value = ""

    @staticmethod
    def format_date(value):
        if not value:
            return ""

        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return str(value)[:19].replace("T", " ")

    def set_header(
        self,
        title: str,
        input_label: str,
        show_back: bool,
    ):
        self.header.value = title
        self.input_field.label = input_label
        self.back_button.visible = show_back

    def clear_list(self):
        self.items_list.controls.clear()

    def make_item(
        self,
        name: str,
        created_at: str = "",
        on_click=None,
    ):
        row_controls = [
            ft.Text(
                value=name,
                expand=True,
                selectable=True,
            ),
        ]

        if created_at:
            row_controls.append(
                ft.Text(
                    value=self.format_date(created_at),
                    size=12,
                    color="grey",
                )
            )

        if on_click is not None:
            row_controls.append(ft.Icon(ft.Icons.CHEVRON_RIGHT))

        return ft.Button(
            content=ft.Row(
                controls=row_controls,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            on_click=on_click,
            expand=True,
        )

    # --------------------------------------------------
    # HTTP API
    # --------------------------------------------------

    async def api_get(self, path: str):
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}{path}")
            response.raise_for_status()
            return response.json()

    async def api_post(self, path: str, data: dict):
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{API_URL}{path}",
                json=data,
            )
            response.raise_for_status()
            return response.json()

    # --------------------------------------------------
    # Темы
    # --------------------------------------------------

    async def load_themes(self, e=None):
        self.current_theme = None
        self.current_subtheme = None

        self.set_header(
            "Темы",
            "Название темы",
            False,
        )

        self.input_field.value = ""
        self.clear_error()
        self.clear_list()
        self.update_page()

        try:
            themes = await self.api_get("/themes")
            self.render_themes(themes)

        except Exception as ex:
            self.show_error(f"Ошибка загрузки тем: {ex}")

        self.update_page()

    def render_themes(self, themes: list):
        for theme in themes:
            self.items_list.controls.append(
                self.make_item(
                    name=theme["name"],
                    created_at=theme.get("created_at", ""),
                    on_click=lambda e, t=theme: self.app_page.run_task(
                        self.load_subthemes, t
                    ),
                )
            )

    # --------------------------------------------------
    # Подтемы
    # --------------------------------------------------

    async def load_subthemes(self, theme: dict):
        self.current_theme = theme
        self.current_subtheme = None

        self.set_header(
            f"Подтемы — {theme['name']}",
            "Название подтемы",
            True,
        )

        self.input_field.value = ""
        self.clear_error()
        self.clear_list()
        self.update_page()

        try:
            subthemes = await self.api_get(f"/themes/{theme['id']}/subthemes")
            self.render_subthemes(subthemes)

        except Exception as ex:
            self.show_error(f"Ошибка загрузки подтем: {ex}")

        self.update_page()

    def render_subthemes(self, subthemes: list):
        for subtheme in subthemes:
            self.items_list.controls.append(
                self.make_item(
                    name=subtheme["name"],
                    created_at=subtheme.get("created_at", ""),
                    on_click=lambda e, s=subtheme: self.app_page.run_task(
                        self.load_records, s
                    ),
                )
            )

    # --------------------------------------------------
    # Записи
    # --------------------------------------------------

    async def load_records(self, subtheme: dict):
        self.current_subtheme = subtheme

        self.set_header(
            f"Записи — {subtheme['name']}",
            "Текст записи",
            True,
        )

        self.input_field.value = ""
        self.clear_error()
        self.clear_list()
        self.update_page()

        try:
            records = await self.api_get(f"/subthemes/{subtheme['id']}/records")
            self.render_records(records)

        except Exception as ex:
            self.show_error(f"Ошибка загрузки записей: {ex}")

        self.update_page()

    def render_records(self, records: list):
        for record in records:
            self.items_list.controls.append(
                self.make_item(
                    name=record["content"],
                    created_at=record.get("created_at", ""),
                )
            )

    # --------------------------------------------------
    # Навигация
    # --------------------------------------------------

    async def go_back(self, e=None):
        if self.current_subtheme is not None:
            if self.current_theme is not None:
                await self.load_subthemes(self.current_theme)
        else:
            await self.load_themes()

    # --------------------------------------------------
    # Добавление элементов
    # --------------------------------------------------

    async def add_item(self, e=None):
        text = (self.input_field.value or "").strip()

        if not text:
            return

        self.add_button.disabled = True
        self.clear_error()
        self.update_page()

        try:
            await self.create_item(text)

        except Exception as ex:
            self.show_error(f"Ошибка при добавлении: {ex}")

        finally:
            self.add_button.disabled = False
            self.update_page()

    async def create_item(self, text: str):
        if self.current_subtheme is not None:
            await self.create_record(text)

        elif self.current_theme is not None:
            await self.create_subtheme(text)

        else:
            await self.create_theme(text)

    async def create_theme(self, name: str):
        await self.api_post(
            "/themes",
            {"name": name},
        )
        await self.load_themes()

    async def create_subtheme(self, name: str):
        theme = self.current_theme

        await self.api_post(
            f"/themes/{theme['id']}/subthemes",
            {"name": name},
        )
        await self.load_subthemes(theme)

    async def create_record(self, content: str):
        subtheme = self.current_subtheme

        await self.api_post(
            f"/subthemes/{subtheme['id']}/records",
            {"content": content},
        )
        await self.load_records(subtheme)


async def main(page: ft.Page):
    page.title = "OJ"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    OJApp(page)


if __name__ == "__main__":
    ft.run(main)
