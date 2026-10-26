from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.record import RecordRepository
from app.schemas import RecordCreate, RecordRead

router = APIRouter(tags=["Records"])


def get_record_repo(session: AsyncSession = Depends(get_session)) -> RecordRepository:
    return RecordRepository(session)


@router.post(
    "/subthemes/{subtheme_id}/records",
    response_model=RecordRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_record(
    subtheme_id: int,
    data: RecordCreate,
    repo: RecordRepository = Depends(get_record_repo),
):
    if not await repo.subtheme_exists(subtheme_id):
        raise HTTPException(status_code=404, detail="Subtheme not found")

    return await repo.create(content=data.content, subtheme_id=subtheme_id)


@router.get("/subthemes/{subtheme_id}/records", response_model=list[RecordRead])
async def get_records(
    subtheme_id: int,
    repo: RecordRepository = Depends(get_record_repo),
):
    if not await repo.subtheme_exists(subtheme_id):
        raise HTTPException(status_code=404, detail="Subtheme not found")

    return await repo.get_by_subtheme_id(subtheme_id)


@router.get("/records/{record_id}", response_model=RecordRead)
async def get_record(
    record_id: int,
    repo: RecordRepository = Depends(get_record_repo),
):
    record = await repo.get_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.patch("/records/{record_id}", response_model=RecordRead)
async def update_record(
    record_id: int,
    data: RecordCreate,
    repo: RecordRepository = Depends(get_record_repo),
):
    record = await repo.get_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    return await repo.update(record, content=data.content)


@router.delete("/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(
    record_id: int,
    repo: RecordRepository = Depends(get_record_repo),
):
    record = await repo.get_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    await repo.delete(record)
