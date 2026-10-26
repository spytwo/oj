from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Theme


class ThemeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, theme_id: int) -> Theme | None:
        return await self.session.get(Theme, theme_id)

    async def get_all(self) -> list[Theme]:
        result = await self.session.execute(
            select(Theme).order_by(Theme.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, name: str) -> Theme:
        theme = Theme(name=name)
        self.session.add(theme)
        await self.session.commit()
        await self.session.refresh(theme)
        return theme

    async def update(self, theme: Theme, name: str) -> Theme:
        theme.name = name
        await self.session.commit()
        await self.session.refresh(theme)
        return theme

    async def delete(self, theme: Theme) -> None:
        await self.session.delete(theme)
        await self.session.commit()
