from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Record, Subtheme


class RecordRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, record_id: int) -> Record | None:
        return await self.session.get(Record, record_id)

    async def get_by_subtheme_id(self, subtheme_id: int) -> list[Record]:
        result = await self.session.execute(
            select(Record)
            .where(Record.subtheme_id == subtheme_id)
            .order_by(Record.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, content: str, subtheme_id: int) -> Record:
        record = Record(content=content.lower(), subtheme_id=subtheme_id)
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def update(self, record: Record, content: str) -> Record:
        record.content = content.lower()
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def delete(self, record: Record) -> None:
        await self.session.delete(record)
        await self.session.commit()

    async def subtheme_exists(self, subtheme_id: int) -> bool:
        subtheme = await self.session.get(Subtheme, subtheme_id)
        return subtheme is not None

    async def search_by_content(self, query: str) -> list[Record]:
        if len(query) < 2:
            return []
        search_term = f"%{query.lower()}%"
        result = await self.session.execute(
            select(Record)
            .where(Record.content.like(search_term))
            .options(selectinload(Record.subtheme).selectinload(Subtheme.theme))
            .order_by(Record.created_at.desc())
        )
        return list(result.scalars().all())
