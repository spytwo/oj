from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Subtheme, Theme


class SubthemeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, subtheme_id: int) -> Subtheme | None:
        return await self.session.get(Subtheme, subtheme_id)

    async def get_by_theme_id(self, theme_id: int) -> list[Subtheme]:
        result = await self.session.execute(
            select(Subtheme)
            .where(Subtheme.theme_id == theme_id)
            .order_by(Subtheme.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, name: str, theme_id: int) -> Subtheme:
        subtheme = Subtheme(name=name, theme_id=theme_id)
        self.session.add(subtheme)
        await self.session.commit()
        await self.session.refresh(subtheme)
        return subtheme

    async def update(self, subtheme: Subtheme, name: str) -> Subtheme:
        subtheme.name = name
        await self.session.commit()
        await self.session.refresh(subtheme)
        return subtheme

    async def delete(self, subtheme: Subtheme) -> None:
        await self.session.delete(subtheme)
        await self.session.commit()

    async def theme_exists(self, theme_id: int) -> bool:
        theme = await self.session.get(Theme, theme_id)
        return theme is not None
