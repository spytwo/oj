import os
from datetime import datetime, timedelta, timezone

import flet as ft
import httpx

API_URL = os.getenv("API_URL", "http://oj:8018")
LOCAL_TIMEZONE = timezone(timedelta(hours=5))


class OJApp:
    def __init__(self, page: ft.Page):
        self.app_page = page

        self.current_theme = None
        self.current_subtheme = None

        self.header = ft.Text(
            value="Темы",
            size=26,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.INDIGO_700,
        )

        self.back_button = ft.TextButton(
            content="← Назад",
            visible=False,
            on_click=self.go_back,
        )

        self.input_field = ft.TextField(
            label="Название темы",
            hint_text="Введите название...",
            expand=True,
            on_submit=self.add_item,
            filled=True,
            bgcolor=ft.Colors.GREY_50,
            border=ft.OutlineInputBorder(
                border_radius=14,
            ),
        )

        self.add_button = ft.Button(
            content="Добавить",
            icon=ft.Icons.ADD,
            on_click=self.add_item,
        )

        self.items_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=4,
        )

        self.status_text = ft.Text(
            value="",
            color=ft.Colors.RED,
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
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        controls=[
                            self.input_field,
                            self.add_button,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self.status_text,
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

        months = [
            "января",
            "февраля",
            "марта",
            "апреля",
            "мая",
            "июня",
            "июля",
            "августа",
            "сентября",
            "октября",
            "ноября",
            "декабря",
        ]

        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))

            # Если API вернул время без часового пояса,
            # считаем его временем UTC.
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)

            local_time = parsed.astimezone(LOCAL_TIMEZONE)
            month = months[local_time.month - 1]

            return f"{local_time.day} {month} {local_time.year} г., {local_time:%H:%M}"

        except (ValueError, TypeError):
            return str(value)

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

    # --------------------------------------------------
    # Карточки тем и подтем
    # --------------------------------------------------

    def make_item(
        self,
        name: str,
        created_at: str = "",
        on_click=None,
    ):
        details = []

        if created_at:
            details.append(
                ft.Text(
                    value=self.format_date(created_at),
                    size=12,
                    color=ft.Colors.OUTLINE,
                )
            )

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(
                                value=name,
                                size=16,
                                weight=ft.FontWeight.W_500,
                                selectable=True,
                            ),
                            *details,
                        ],
                        spacing=5,
                        expand=True,
                    ),
                    ft.Icon(
                        ft.Icons.CHEVRON_RIGHT,
                        color=ft.Colors.OUTLINE,
                    )
                    if on_click is not None
                    else ft.Container(),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=14,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(
                1,
                ft.Colors.GREY_200,
            ),
            border_radius=14,
            ink=True,
            on_click=on_click,
        )

    # --------------------------------------------------
    # Карточки заметок
    # --------------------------------------------------

    def make_record_item(
        self,
        content: str,
        created_at: str = "",
    ):
        controls = []

        if created_at:
            controls.append(
                ft.Text(
                    value=self.format_date(created_at),
                    size=12,
                    color=ft.Colors.OUTLINE,
                )
            )

        controls.append(
            ft.Text(
                value=content,
                size=16,
                selectable=True,
            )
        )

        return ft.Container(
            content=ft.Column(
                controls=controls,
                spacing=8,
                tight=True,
            ),
            padding=14,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(
                1,
                ft.Colors.GREY_200,
            ),
            border_radius=14,
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
            f"{theme['name']} — Подтемы",
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
    # Заметки
    # --------------------------------------------------

    async def load_records(self, subtheme: dict):
        self.current_subtheme = subtheme

        self.set_header(
            f"{subtheme['name']} — Записи",
            "Текст заметки",
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
                self.make_record_item(
                    content=record["content"],
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
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.Colors.WHITE
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.INDIGO)
    page.padding = 20

    OJApp(page)


if __name__ == "__main__":
    ft.run(main)
