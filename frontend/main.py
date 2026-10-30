import asyncio
import base64
import os
import re
from datetime import datetime, timedelta, timezone

import flet as ft
import httpx
from parser import fetch_title

API_URL = os.getenv("API_URL", "http://oj:8018")

API_USER = os.getenv("USERNAME")
API_PASSWORD = os.getenv("PASSWORD")

if not API_USER or not API_PASSWORD:
    raise RuntimeError("USERNAME и PASSWORD должны быть заданы в окружении")

AUTH_HEADER = (
    "Basic " + base64.b64encode(f"{API_USER}:{API_PASSWORD}".encode()).decode()
)

LOCAL_TIMEZONE = timezone(timedelta(hours=5))
URL_PATTERN = re.compile(r"(https?://[^\s]+)")

AUTH_KEY = "oj.authenticated"


async def show_login(page: ft.Page, prefs: ft.SharedPreferences):
    page.clean()

    username_field = ft.TextField(
        label="Логин",
        autofocus=True,
        border_radius=12,
        width=320,
    )
    password_field = ft.TextField(
        label="Пароль",
        password=True,
        can_reveal_password=True,
        border_radius=12,
        width=320,
        on_submit=lambda e: page.run_task(try_login),
    )
    error_text = ft.Text(value="", color=ft.Colors.RED_600, size=13)

    async def try_login(e=None):
        username = (username_field.value or "").strip()
        password = password_field.value or ""

        if username == API_USER and password == API_PASSWORD:
            await prefs.set(AUTH_KEY, True)
            page.clean()
            OJApp(page, prefs)
        else:
            error_text.value = "Неверный логин или пароль"
            page.update()

    login_button = ft.FilledButton(
        "Войти",
        width=320,
        height=48,
        on_click=lambda e: page.run_task(try_login),
    )

    page.add(
        ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Our Journal",
                        size=28,
                        weight=ft.FontWeight.W_700,
                        color=ft.Colors.INDIGO_800,
                    ),
                    ft.Container(height=24),
                    username_field,
                    password_field,
                    error_text,
                    ft.Container(height=8),
                    login_button,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            alignment=ft.Alignment.TOP_CENTER,
            padding=ft.Padding.only(top=120),
            expand=True,
        )
    )


class OJApp:
    def __init__(self, page: ft.Page, prefs: ft.SharedPreferences):
        self.app_page = page
        self.prefs = prefs

        self.current_theme = None
        self.current_subtheme = None
        self.is_search_mode = False

        self.logo = ft.TextButton(
            content=ft.Text(
                "Our Journal",
                size=26,
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

        self.logout_button = ft.IconButton(
            icon=ft.Icons.LOGOUT_ROUNDED,
            icon_size=22,
            icon_color=ft.Colors.INDIGO_800,
            tooltip="Выйти",
            on_click=lambda e: self.app_page.run_task(self.logout),
            height=44,
            width=44,
        )

        self.breadcrumbs_row = ft.Row(
            controls=[],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
            wrap=True,
        )

        self.search_field = ft.TextField(
            hint_text="Поиск по заметкам…",
            expand=True,
            filled=True,
            bgcolor=ft.Colors.WHITE,
            border=ft.OutlineInputBorder(
                border_radius=12,
                side=ft.BorderSide(1, ft.Colors.GREY_300),
            ),
            content_padding=ft.Padding.symmetric(horizontal=14, vertical=12),
            text_size=14,
            cursor_color=ft.Colors.INDIGO_600,
            on_submit=self.do_search,
            height=48,
        )

        self.search_button = ft.IconButton(
            icon=ft.Icons.SEARCH_ROUNDED,
            icon_size=24,
            icon_color=ft.Colors.INDIGO_800,
            tooltip="Поиск",
            on_click=self.do_search,
            height=48,
            width=48,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=12),
                padding=ft.Padding.all(12),
                side=ft.BorderSide(1, ft.Colors.GREY_300),
            ),
        )

        self.add_button = ft.IconButton(
            icon=ft.Icons.ADD_ROUNDED,
            icon_size=24,
            icon_color=ft.Colors.INDIGO_800,
            tooltip="Добавить",
            on_click=lambda e: self.app_page.run_task(self.open_add_dialog),
            height=48,
            width=48,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=12),
                padding=ft.Padding.all(12),
                side=ft.BorderSide(1, ft.Colors.GREY_300),
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
        main_column = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Row(
                        controls=[
                            self.logo,
                            ft.Container(expand=True),
                            self.logout_button,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding.only(bottom=6),
                ),
                ft.Container(
                    content=self.breadcrumbs_row,
                    height=28,
                    alignment=ft.Alignment.CENTER_LEFT,
                    margin=ft.Margin.only(bottom=16),
                ),
                ft.Container(
                    content=ft.Row(
                        controls=[
                            self.search_field,
                            self.search_button,
                            self.add_button,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=ft.Padding.only(top=2, bottom=6),
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
            spacing=4,
        )

        centered_container = ft.Container(
            content=main_column,
            width=650,
            alignment=ft.Alignment.TOP_CENTER,
            expand=True,
        )

        page_wrapper = ft.Container(
            content=centered_container,
            alignment=ft.Alignment.TOP_CENTER,
            expand=True,
            padding=ft.Padding.symmetric(horizontal=20, vertical=10),
        )

        self.app_page.clean()
        self.app_page.add(page_wrapper)

    async def logout(self):
        # Удаляем только флаг входа; логин и пароль в браузере не сохраняются.
        await self.prefs.remove(AUTH_KEY)
        await show_login(self.app_page, self.prefs)

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

    def update_breadcrumbs(self):
        self.breadcrumbs_row.controls.clear()

        if self.is_search_mode:
            self.breadcrumbs_row.controls.append(
                ft.Text("/ Поиск", size=16, color=ft.Colors.GREY_500)
            )
            return

        if self.current_subtheme and self.current_theme:
            theme = self.current_theme
            subtheme = self.current_subtheme

            self.breadcrumbs_row.controls.append(
                ft.Text("/", size=16, color=ft.Colors.GREY_400)
            )
            self.breadcrumbs_row.controls.append(
                ft.TextButton(
                    content=ft.Text(
                        theme["name"],
                        size=16,
                        weight=ft.FontWeight.W_500,
                        color=ft.Colors.INDIGO_700,
                    ),
                    on_click=lambda e, t=theme: self.app_page.run_task(
                        self.load_subthemes, t
                    ),
                    style=ft.ButtonStyle(
                        padding=ft.Padding.symmetric(horizontal=4, vertical=2),
                        overlay_color=ft.Colors.with_opacity(0.08, ft.Colors.INDIGO),
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                )
            )
            self.breadcrumbs_row.controls.append(
                ft.Text("/", size=16, color=ft.Colors.GREY_400)
            )
            self.breadcrumbs_row.controls.append(
                ft.Text(
                    subtheme["name"],
                    size=16,
                    weight=ft.FontWeight.W_500,
                    color=ft.Colors.GREY_700,
                )
            )

        elif self.current_theme:
            theme = self.current_theme

            self.breadcrumbs_row.controls.append(
                ft.Text("/", size=16, color=ft.Colors.GREY_400)
            )
            self.breadcrumbs_row.controls.append(
                ft.TextButton(
                    content=ft.Text(
                        theme["name"],
                        size=16,
                        weight=ft.FontWeight.W_500,
                        color=ft.Colors.INDIGO_700,
                    ),
                    on_click=lambda e, t=theme: self.app_page.run_task(
                        self.load_subthemes, t
                    ),
                    style=ft.ButtonStyle(
                        padding=ft.Padding.symmetric(horizontal=4, vertical=2),
                        overlay_color=ft.Colors.with_opacity(0.08, ft.Colors.INDIGO),
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                )
            )

    def clear_list(self):
        self.items_list.controls.clear()

    def _build_rich_text(self, content: str) -> ft.Control:
        parts = URL_PATTERN.split(content)

        spans = []
        for part in parts:
            if URL_PATTERN.fullmatch(part):
                link_span = ft.TextSpan(
                    text=part,
                    url=part,
                    style=ft.TextStyle(
                        color=ft.Colors.INDIGO_600,
                        decoration=ft.TextDecoration.UNDERLINE,
                    ),
                )
                spans.append(link_span)
                self.app_page.run_task(self._fetch_and_update_title, link_span, part)
            else:
                if part:
                    spans.append(ft.TextSpan(text=part))

        return ft.Text(spans=spans, size=15, color=ft.Colors.GREY_900, selectable=True)

    async def _fetch_and_update_title(self, span: ft.TextSpan, url: str):
        title = await asyncio.to_thread(fetch_title, url)
        if title:
            span.text = title
            span.style.decoration = ft.TextDecoration.NONE
            self.update_page()

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

        controls.append(self._build_rich_text(content))

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

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=10,
            headers={"Authorization": AUTH_HEADER},
        )

    async def api_get(self, path: str, params: dict | None = None):
        async with self._client() as client:
            response = await client.get(f"{API_URL}{path}", params=params)
            response.raise_for_status()
            return response.json()

    async def api_post(self, path: str, data: dict):
        async with self._client() as client:
            response = await client.post(f"{API_URL}{path}", json=data)
            response.raise_for_status()
            return response.json()

    async def api_patch(self, path: str, data: dict):
        async with self._client() as client:
            response = await client.patch(f"{API_URL}{path}", json=data)
            response.raise_for_status()
            return response.json()

    async def api_delete(self, path: str):
        async with self._client() as client:
            response = await client.delete(f"{API_URL}{path}")
            response.raise_for_status()
            return response

    def _close_dialog(self, dialog: ft.AlertDialog):
        dialog.open = False
        self.update_page()

    async def open_add_dialog(self):
        is_record = self.current_subtheme is not None

        if is_record:
            dialog_title = "Добавить новую заметку"
            label_text = "Текст заметки"
        elif self.current_theme:
            dialog_title = "Добавить новую подтему"
            label_text = "Название подтемы"
        else:
            dialog_title = "Добавить новую тему"
            label_text = "Название темы"

        input_field = ft.TextField(
            label=label_text,
            multiline=is_record,
            min_lines=1 if is_record else 1,
            max_lines=10 if is_record else 1,
            expand=True,
            autofocus=True,
            border_radius=12,
        )

        async def on_add(e):
            text = (input_field.value or "").strip()
            if not text:
                return
            self._close_dialog(dialog)
            try:
                await self.create_item(text)
            except Exception as ex:
                self.show_error(f"Ошибка при добавлении: {ex}")

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(dialog_title),
            content=ft.Container(content=input_field, width=400),
            actions=[
                ft.TextButton("Отмена", on_click=lambda e: self._close_dialog(dialog)),
                ft.FilledButton(
                    "Добавить",
                    on_click=lambda e: self.app_page.run_task(on_add, e),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.app_page.overlay.append(dialog)
        dialog.open = True
        self.update_page()

    async def open_edit_dialog(self, item: dict, item_type: str):
        is_record = item_type == "record"
        value = item.get("content") if is_record else item.get("name", "")

        edit_field = ft.TextField(
            value=value or "",
            label="Текст заметки" if is_record else "Название",
            multiline=is_record,
            min_lines=1 if is_record else 1,
            max_lines=10 if is_record else 1,
            expand=True,
            autofocus=True,
            border_radius=12,
        )

        async def on_save(e):
            new_value = (edit_field.value or "").strip()
            if not new_value:
                return
            self._close_dialog(dialog)
            try:
                if item_type == "theme":
                    await self.api_patch(f"/themes/{item['id']}", {"name": new_value})
                    await self.load_themes()
                elif item_type == "subtheme":
                    await self.api_patch(
                        f"/subthemes/{item['id']}", {"name": new_value}
                    )
                    if self.current_theme:
                        await self.load_subthemes(self.current_theme)
                elif item_type == "record":
                    await self.api_patch(
                        f"/records/{item['id']}", {"content": new_value}
                    )
                    if self.current_subtheme:
                        await self.load_records(self.current_subtheme)
                    elif self.is_search_mode:
                        await self.do_search()
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

    async def confirm_delete(self, item: dict, item_type: str):
        labels = {"theme": "тему", "subtheme": "подтему", "record": "заметку"}
        label = labels.get(item_type, "элемент")
        name = item.get("name") or (
            (item.get("content", "")[:40]) if item.get("content") else ""
        )

        async def on_delete(e):
            self._close_dialog(dialog)
            try:
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

    def make_search_item(self, item: dict) -> ft.Container:
        content = (
            item.get("content") or item.get("text") or item.get("name") or str(item)
        )
        created_at = item.get("created_at", "")

        theme_name = item.get("theme_name")
        subtheme_name = item.get("subtheme_name")

        path_parts = [p for p in [theme_name, subtheme_name] if p]
        path = " / ".join(path_parts)

        meta_parts = [p for p in [path, self.format_date(created_at)] if p]
        meta_text = " · ".join(meta_parts)

        controls = []
        if meta_text:
            controls.append(ft.Text(value=meta_text, size=12, color=ft.Colors.GREY_500))

        controls.append(self._build_rich_text(content))

        edit_btn = ft.IconButton(
            icon=ft.Icons.EDIT_OUTLINED,
            icon_size=18,
            icon_color=ft.Colors.GREY_600,
            tooltip="Редактировать",
            on_click=lambda e, r=item: self.app_page.run_task(
                self.open_edit_dialog, r, "record"
            ),
        )

        delete_btn = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
            icon_size=18,
            icon_color=ft.Colors.RED_400,
            tooltip="Удалить",
            on_click=lambda e, r=item: self.app_page.run_task(
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

    async def do_search(self, e=None):
        query = (self.search_field.value or "").strip()
        if not query:
            return

        self.is_search_mode = True
        self.update_breadcrumbs()
        self.clear_error()
        self.clear_list()
        self.update_page()

        try:
            results = await self.api_get("/search", params={"q": query})
            for item in results:
                self.items_list.controls.append(self.make_search_item(item))
        except Exception as ex:
            self.show_error(f"Ошибка поиска: {ex}")

        self.update_empty_state("Ничего не найдено")
        self.update_page()

    async def load_themes(self, e=None):
        self.current_theme = None
        self.current_subtheme = None
        self.is_search_mode = False
        self.search_field.value = ""

        self.update_breadcrumbs()
        self.clear_error()
        self.clear_list()
        self.update_page()

        try:
            themes = await self.api_get("/themes")
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
        except Exception as ex:
            self.show_error(f"Ошибка загрузки тем: {ex}")

        self.update_empty_state()
        self.update_page()

    async def load_subthemes(self, theme: dict):
        self.current_theme = theme
        self.current_subtheme = None
        self.is_search_mode = False

        self.update_breadcrumbs()
        self.clear_error()
        self.clear_list()
        self.update_page()

        try:
            subthemes = await self.api_get(f"/themes/{theme['id']}/subthemes")
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
        except Exception as ex:
            self.show_error(f"Ошибка загрузки подтем: {ex}")

        self.update_empty_state()
        self.update_page()

    async def load_records(self, subtheme: dict):
        self.current_subtheme = subtheme
        self.is_search_mode = False

        self.update_breadcrumbs()
        self.clear_error()
        self.clear_list()
        self.update_page()

        try:
            records = await self.api_get(f"/subthemes/{subtheme['id']}/records")
            for record in records:
                self.items_list.controls.append(
                    self.make_record_item(
                        record=record,
                        content=record["content"],
                        created_at=record.get("created_at", ""),
                    )
                )
        except Exception as ex:
            self.show_error(f"Ошибка загрузки заметок: {ex}")

        self.update_empty_state()
        self.update_page()

    async def create_item(self, text: str):
        if self.current_subtheme is not None:
            await self.api_post(
                f"/subthemes/{self.current_subtheme['id']}/records",
                {"content": text},
            )
            await self.load_records(self.current_subtheme)
        elif self.current_theme is not None:
            await self.api_post(
                f"/themes/{self.current_theme['id']}/subthemes",
                {"name": text},
            )
            await self.load_subthemes(self.current_theme)
        else:
            await self.api_post("/themes", {"name": text})
            await self.load_themes()


async def main(page: ft.Page):
    page.title = "Our Journal"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.Colors.GREY_50
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.INDIGO,
        visual_density=ft.VisualDensity.COMFORTABLE,
    )
    page.padding = 0

    prefs = ft.SharedPreferences()
    page.services.append(prefs)

    authenticated = await prefs.get(AUTH_KEY)
    if authenticated:
        OJApp(page, prefs)
    else:
        await show_login(page, prefs)


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
