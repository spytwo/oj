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
        self.is_search_mode = False
        self.logo = ft.TextButton(
            content=ft.Text(
                "OJ",
                size=24,
                weight=ft.FontWeight.W_700,
                color=ft.Colors.INDIGO_800,
            ),
            on_click=lambda e: self.app_page.run_task(self.load_themes),
            style=ft.ButtonStyle(
                padding=ft.Padding.symmetric(horizontal=4, vertical=2),
                overlay_color=ft.Colors.with_opacity(0.08, ft.Colors.INDIGO),
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )

        self.section_title = ft.Text(
            value="",
            size=16,
            weight=ft.FontWeight.W_500,
            color=ft.Colors.GREY_700,
            visible=False,
        )

        self.back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK_ROUNDED,
            icon_size=20,
            icon_color=ft.Colors.INDIGO_600,
            tooltip="Назад",
            visible=False,
            on_click=self.go_back,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=8,
            ),
        )

        self.search_field = ft.TextField(
            hint_text="Поиск по заметкам…",
            width=320,
            filled=True,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border_color=ft.Colors.GREY_300,
            focused_border_color=ft.Colors.INDIGO_400,
            content_padding=ft.Padding.symmetric(horizontal=14, vertical=12),
            text_size=14,
            cursor_color=ft.Colors.INDIGO_600,
            prefix_icon=ft.Icons.SEARCH_ROUNDED,
            on_submit=self.do_search,
            height=48,
        )

        self.search_button = ft.FilledButton(
            content="Поиск",
            icon=ft.Icons.SEARCH_ROUNDED,
            on_click=self.do_search,
            height=48,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
                padding=ft.Padding.symmetric(horizontal=20, vertical=0),
            ),
        )

        self.input_field = ft.TextField(
            label="Название темы",
            expand=True,
            on_submit=self.add_item,
            filled=True,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border_color=ft.Colors.GREY_300,
            focused_border_color=ft.Colors.INDIGO_400,
            content_padding=ft.Padding.symmetric(horizontal=14, vertical=12),
            text_size=15,
            cursor_color=ft.Colors.INDIGO_600,
            height=48,
        )

        self.add_button = ft.FilledButton(
            content="Добавить",
            icon=ft.Icons.ADD_ROUNDED,
            on_click=self.add_item,
            height=48,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
                padding=ft.Padding.symmetric(horizontal=18, vertical=0),
            ),
        )

        self.items_list = ft.ListView(
            expand=True,
            spacing=8,
            padding=ft.Padding.only(top=4, bottom=8),
        )

        self.empty_state = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.INBOX_OUTLINED,
                        size=40,
                        color=ft.Colors.GREY_400,
                    ),
                    ft.Text(
                        "Пока пусто",
                        size=14,
                        color=ft.Colors.GREY_500,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
            visible=False,
        )

        self.status_text = ft.Text(
            value="",
            size=13,
            color=ft.Colors.RED_600,
            selectable=True,
        )

        self.build_ui()
        self.app_page.run_task(self.load_themes)

    def build_ui(self):
        self.app_page.add(
            ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                self.back_button,
                                self.logo,
                                self.section_title,
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=6,
                        ),
                        padding=ft.Padding.only(bottom=4),
                    ),
                    ft.Divider(height=1, color=ft.Colors.GREY_200),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                self.search_field,
                                self.search_button,
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                        ),
                        padding=ft.Padding.only(top=10, bottom=6),
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                self.input_field,
                                self.add_button,
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            spacing=10,
                        ),
                        padding=ft.Padding.only(top=4, bottom=4),
                    ),
                    self.status_text,
                    ft.Stack(
                        controls=[
                            self.items_list,
                            self.empty_state,
                        ],
                        expand=True,
                    ),
                ],
                expand=True,
                spacing=6,
            )
        )

    def update_page(self):
        self.app_page.update()

    def show_error(self, message: str):
        self.status_text.value = message
        self.status_text.color = ft.Colors.RED_600
        self.update_page()

    def clear_error(self):
        self.status_text.value = ""

    def update_empty_state(self, message: str = "Пока пусто"):
        is_empty = len(self.items_list.controls) == 0
        self.empty_state.visible = is_empty
        self.items_list.visible = not is_empty
        if (
            is_empty
            and self.empty_state.content
            and len(self.empty_state.content.controls) > 1
        ):
            self.empty_state.content.controls[1].value = message

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
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            local_time = parsed.astimezone(LOCAL_TIMEZONE)
            month = months[local_time.month - 1]
            return f"{local_time.day} {month} {local_time.year} г., {local_time:%H:%M}"
        except (ValueError, TypeError):
            return str(value)

    def set_header(
        self,
        section: str,
        input_label: str,
        show_back: bool,
        multiline: bool = False,
        show_add: bool = True,
    ):
        if section:
            self.section_title.value = section
            self.section_title.visible = True
        else:
            self.section_title.value = ""
            self.section_title.visible = False

        self.input_field.label = input_label
        self.back_button.visible = show_back

        self.input_field.multiline = multiline
        self.input_field.shift_enter = multiline
        self.input_field.hint_text = None

        if multiline:
            self.input_field.min_lines = 1
            self.input_field.max_lines = None
            self.input_field.height = None
        else:
            self.input_field.min_lines = 1
            self.input_field.max_lines = 1
            self.input_field.height = 48

        self.input_field.visible = show_add
        self.add_button.visible = show_add

    def clear_list(self):
        self.items_list.controls.clear()

    def make_item(
        self,
        item: dict,
        name: str,
        created_at: str = "",
        on_click=None,
        item_type: str = "theme",
    ):
        details = []
        if created_at:
            details.append(
                ft.Text(
                    value=self.format_date(created_at),
                    size=12,
                    color=ft.Colors.GREY_500,
                )
            )

        name_control = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        value=name,
                        size=15,
                        weight=ft.FontWeight.W_500,
                        color=ft.Colors.GREY_900,
                        selectable=True,
                    ),
                    *details,
                ],
                spacing=3,
            ),
            expand=True,
            ink=True,
            on_click=on_click,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=4, vertical=2),
        )

        edit_btn = ft.IconButton(
            icon=ft.Icons.EDIT_OUTLINED,
            icon_size=18,
            icon_color=ft.Colors.GREY_600,
            tooltip="Редактировать",
            on_click=lambda e, it=item, t=item_type: self.app_page.run_task(
                self.open_edit_dialog, it, t
            ),
        )

        delete_btn = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
            icon_size=18,
            icon_color=ft.Colors.RED_400,
            tooltip="Удалить",
            on_click=lambda e, it=item, t=item_type: self.app_page.run_task(
                self.confirm_delete, it, t
            ),
        )

        return ft.Container(
            content=ft.Row(
                controls=[name_control, edit_btn, delete_btn],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, ft.Colors.GREY_200),
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK),
                offset=ft.Offset(0, 1),
            ),
        )

    def make_record_item(
        self,
        record: dict,
        content: str,
        created_at: str = "",
        extra: str = "",
    ):
        controls = []
        if created_at or extra:
            meta_parts = []
            if extra:
                meta_parts.append(extra)
            if created_at:
                meta_parts.append(self.format_date(created_at))
            controls.append(
                ft.Text(
                    value=" · ".join(meta_parts),
                    size=12,
                    color=ft.Colors.GREY_500,
                )
            )

        controls.append(
            ft.Text(
                value=content,
                size=15,
                color=ft.Colors.GREY_900,
                selectable=True,
            )
        )

        edit_btn = ft.IconButton(
            icon=ft.Icons.EDIT_OUTLINED,
            icon_size=18,
            icon_color=ft.Colors.GREY_600,
            tooltip="Редактировать",
            on_click=lambda e, r=record: self.app_page.run_task(
                self.open_edit_dialog, r, "record"
            ),
        )

        delete_btn = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
            icon_size=18,
            icon_color=ft.Colors.RED_400,
            tooltip="Удалить",
            on_click=lambda e, r=record: self.app_page.run_task(
                self.confirm_delete, r, "record"
            ),
        )

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=controls,
                        spacing=6,
                        tight=True,
                        expand=True,
                    ),
                    edit_btn,
                    delete_btn,
                ],
                vertical_alignment=ft.CrossAxisAlignment.START,
                spacing=4,
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=12),
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, ft.Colors.GREY_200),
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK),
                offset=ft.Offset(0, 1),
            ),
        )

    async def api_get(self, path: str, params: dict | None = None):
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}{path}", params=params)
            response.raise_for_status()
            return response.json()

    async def api_post(self, path: str, data: dict):
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(f"{API_URL}{path}", json=data)
            response.raise_for_status()
            return response.json()

    async def api_patch(self, path: str, data: dict):
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.patch(f"{API_URL}{path}", json=data)
            response.raise_for_status()
            return response.json()

    async def api_delete(self, path: str):
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.delete(f"{API_URL}{path}")
            response.raise_for_status()
            return response

    def _edit_field_for(self, item: dict, item_type: str) -> ft.TextField:
        is_record = item_type == "record"
        value = item.get("content") if is_record else item.get("name", "")
        return ft.TextField(
            value=value or "",
            label="Текст заметки" if is_record else "Название",
            multiline=is_record,
            min_lines=1 if is_record else 1,
            max_lines=None if is_record else 1,
            expand=True,
            autofocus=True,
            border_radius=12,
        )

    async def _save_edit(self, item: dict, item_type: str, new_value: str):
        if item_type == "theme":
            await self.api_patch(f"/themes/{item['id']}", {"name": new_value})
            await self.load_themes()
        elif item_type == "subtheme":
            await self.api_patch(f"/subthemes/{item['id']}", {"name": new_value})
            if self.current_theme:
                await self.load_subthemes(self.current_theme)
        elif item_type == "record":
            await self.api_patch(f"/records/{item['id']}", {"content": new_value})
            if self.current_subtheme:
                await self.load_records(self.current_subtheme)
            elif self.is_search_mode:
                await self.do_search()

    def _close_dialog(self, dialog: ft.AlertDialog):
        dialog.open = False
        self.update_page()

    async def open_edit_dialog(self, item: dict, item_type: str):
        edit_field = self._edit_field_for(item, item_type)

        async def on_save(e):
            new_value = (edit_field.value or "").strip()
            if not new_value:
                return
            self._close_dialog(dialog)
            try:
                await self._save_edit(item, item_type, new_value)
            except Exception as ex:
                self.show_error(f"Ошибка сохранения: {ex}")

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Редактировать"),
            content=ft.Container(content=edit_field, width=400),
            actions=[
                ft.TextButton("Отмена", on_click=lambda e: self._close_dialog(dialog)),
                ft.FilledButton(
                    "Сохранить",
                    on_click=lambda e: self.app_page.run_task(on_save, e),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.app_page.overlay.append(dialog)
        dialog.open = True
        self.update_page()

    async def _do_delete(self, item: dict, item_type: str):
        if item_type == "theme":
            await self.api_delete(f"/themes/{item['id']}")
            await self.load_themes()
        elif item_type == "subtheme":
            await self.api_delete(f"/subthemes/{item['id']}")
            if self.current_theme:
                await self.load_subthemes(self.current_theme)
        elif item_type == "record":
            await self.api_delete(f"/records/{item['id']}")
            if self.current_subtheme:
                await self.load_records(self.current_subtheme)
            elif self.is_search_mode:
                await self.do_search()

    async def confirm_delete(self, item: dict, item_type: str):
        labels = {"theme": "тему", "subtheme": "подтему", "record": "заметку"}
        label = labels.get(item_type, "элемент")
        name = item.get("name") or (
            (item.get("content", "")[:40]) if item.get("content") else ""
        )

        async def on_delete(e):
            self._close_dialog(dialog)
            try:
                await self._do_delete(item, item_type)
            except Exception as ex:
                self.show_error(f"Ошибка удаления: {ex}")

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Удалить?"),
            content=ft.Text(f"Вы уверены, что хотите удалить {label}?\n\n«{name}»"),
            actions=[
                ft.TextButton("Отмена", on_click=lambda e: self._close_dialog(dialog)),
                ft.FilledButton(
                    "Удалить",
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.RED_600,
                        color=ft.Colors.WHITE,
                    ),
                    on_click=lambda e: self.app_page.run_task(on_delete, e),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.app_page.overlay.append(dialog)
        dialog.open = True
        self.update_page()

    async def do_search(self, e=None):
        query = (self.search_field.value or "").strip()
        if not query:
            return

        self.is_search_mode = True

        self.set_header(
            "",
            "",
            show_back=True,
            multiline=False,
            show_add=False,
        )

        self.clear_error()
        self.clear_list()
        self.update_page()

        try:
            results = await self.api_get("/search", params={"q": query})
            self.render_search_results(results)
        except Exception as ex:
            self.show_error(f"Ошибка поиска: {ex}")

        self.update_empty_state("Ничего не найдено")
        self.update_page()

    def render_search_results(self, results: list):
        for item in results:
            content = (
                item.get("content") or item.get("text") or item.get("name") or str(item)
            )
            created_at = item.get("created_at", "")
            extra = ""
            if item.get("theme_name") or item.get("subtheme_name"):
                parts = [
                    p for p in [item.get("theme_name"), item.get("subtheme_name")] if p
                ]
                extra = " / ".join(parts)

            self.items_list.controls.append(
                self.make_record_item(
                    record=item,
                    content=content,
                    created_at=created_at,
                    extra=extra,
                )
            )

    async def load_themes(self, e=None):
        self.current_theme = None
        self.current_subtheme = None
        self.is_search_mode = False
        self.search_field.value = ""

        self.set_header(
            "",
            "Название темы",
            False,
            multiline=False,
            show_add=True,
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

        self.update_empty_state()
        self.update_page()

    def render_themes(self, themes: list):
        for theme in themes:
            self.items_list.controls.append(
                self.make_item(
                    item=theme,
                    name=theme["name"],
                    created_at=theme.get("created_at", ""),
                    on_click=lambda e, t=theme: self.app_page.run_task(
                        self.load_subthemes, t
                    ),
                    item_type="theme",
                )
            )

    async def load_subthemes(self, theme: dict):
        self.current_theme = theme
        self.current_subtheme = None
        self.is_search_mode = False

        self.set_header(
            theme["name"],
            "Название подтемы",
            True,
            multiline=False,
            show_add=True,
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

        self.update_empty_state()
        self.update_page()

    def render_subthemes(self, subthemes: list):
        for subtheme in subthemes:
            self.items_list.controls.append(
                self.make_item(
                    item=subtheme,
                    name=subtheme["name"],
                    created_at=subtheme.get("created_at", ""),
                    on_click=lambda e, s=subtheme: self.app_page.run_task(
                        self.load_records, s
                    ),
                    item_type="subtheme",
                )
            )

    async def load_records(self, subtheme: dict):
        self.current_subtheme = subtheme
        self.is_search_mode = False

        theme_name = self.current_theme["name"] if self.current_theme else ""
        section = (
            f"{theme_name} - {subtheme['name']}" if theme_name else subtheme["name"]
        )

        self.set_header(
            section,
            "Текст заметки",
            True,
            multiline=True,
            show_add=True,
        )

        self.input_field.value = ""
        self.clear_error()
        self.clear_list()
        self.update_page()

        try:
            records = await self.api_get(f"/subthemes/{subtheme['id']}/records")
            self.render_records(records)
        except Exception as ex:
            self.show_error(f"Ошибка загрузки заметок: {ex}")

        self.update_empty_state()
        self.update_page()

    def render_records(self, records: list):
        for record in records:
            self.items_list.controls.append(
                self.make_record_item(
                    record=record,
                    content=record["content"],
                    created_at=record.get("created_at", ""),
                )
            )

    async def go_back(self, e=None):
        if self.is_search_mode:
            self.is_search_mode = False
            if self.current_subtheme is not None:
                await self.load_records(self.current_subtheme)
            elif self.current_theme is not None:
                await self.load_subthemes(self.current_theme)
            else:
                await self.load_themes()
            return

        if self.current_subtheme is not None:
            if self.current_theme is not None:
                await self.load_subthemes(self.current_theme)
            else:
                await self.load_themes()
        elif self.current_theme is not None:
            await self.load_themes()

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
        await self.api_post("/themes", {"name": name})
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
    page.bgcolor = ft.Colors.GREY_50
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.INDIGO,
        visual_density=ft.VisualDensity.COMFORTABLE,
    )
    page.padding = 20

    OJApp(page)


if __name__ == "__main__":
    ft.run(main)
