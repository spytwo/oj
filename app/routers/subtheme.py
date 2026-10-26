from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.subtheme import SubthemeRepository
from app.schemas import SubthemeCreate, SubthemeRead

router = APIRouter(tags=["Subthemes"])


def get_subtheme_repo(
    session: AsyncSession = Depends(get_session),
) -> SubthemeRepository:
    return SubthemeRepository(session)


@router.post(
    "/themes/{theme_id}/subthemes",
    response_model=SubthemeRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_subtheme(
    theme_id: int,
    data: SubthemeCreate,
    repo: SubthemeRepository = Depends(get_subtheme_repo),
):
    if not await repo.theme_exists(theme_id):
        raise HTTPException(status_code=404, detail="Theme not found")

    return await repo.create(name=data.name, theme_id=theme_id)


@router.get("/themes/{theme_id}/subthemes", response_model=list[SubthemeRead])
async def get_subthemes(
    theme_id: int,
    repo: SubthemeRepository = Depends(get_subtheme_repo),
):
    if not await repo.theme_exists(theme_id):
        raise HTTPException(status_code=404, detail="Theme not found")

    return await repo.get_by_theme_id(theme_id)


@router.get("/subthemes/{subtheme_id}", response_model=SubthemeRead)
async def get_subtheme(
    subtheme_id: int,
    repo: SubthemeRepository = Depends(get_subtheme_repo),
):
    subtheme = await repo.get_by_id(subtheme_id)
    if not subtheme:
        raise HTTPException(status_code=404, detail="Subtheme not found")
    return subtheme


@router.patch("/subthemes/{subtheme_id}", response_model=SubthemeRead)
async def update_subtheme(
    subtheme_id: int,
    data: SubthemeCreate,
    repo: SubthemeRepository = Depends(get_subtheme_repo),
):
    subtheme = await repo.get_by_id(subtheme_id)
    if not subtheme:
        raise HTTPException(status_code=404, detail="Subtheme not found")

    return await repo.update(subtheme, name=data.name)


@router.delete("/subthemes/{subtheme_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subtheme(
    subtheme_id: int,
    repo: SubthemeRepository = Depends(get_subtheme_repo),
):
    subtheme = await repo.get_by_id(subtheme_id)
    if not subtheme:
        raise HTTPException(status_code=404, detail="Subtheme not found")

    await repo.delete(subtheme)
