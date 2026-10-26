from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.theme import ThemeRepository
from app.schemas import ThemeCreate, ThemeRead

router = APIRouter(prefix="/themes", tags=["Themes"])


def get_theme_repo(session: AsyncSession = Depends(get_session)) -> ThemeRepository:
    return ThemeRepository(session)


@router.post("", response_model=ThemeRead, status_code=status.HTTP_201_CREATED)
async def create_theme(
    data: ThemeCreate,
    repo: ThemeRepository = Depends(get_theme_repo),
):
    return await repo.create(name=data.name)


@router.get("", response_model=list[ThemeRead])
async def get_themes(
    repo: ThemeRepository = Depends(get_theme_repo),
):
    return await repo.get_all()


@router.get("/{theme_id}", response_model=ThemeRead)
async def get_theme(
    theme_id: int,
    repo: ThemeRepository = Depends(get_theme_repo),
):
    theme = await repo.get_by_id(theme_id)
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")
    return theme


@router.patch("/{theme_id}", response_model=ThemeRead)
async def update_theme(
    theme_id: int,
    data: ThemeCreate,
    repo: ThemeRepository = Depends(get_theme_repo),
):
    theme = await repo.get_by_id(theme_id)
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")
    return await repo.update(theme, name=data.name)


@router.delete("/{theme_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_theme(
    theme_id: int,
    repo: ThemeRepository = Depends(get_theme_repo),
):
    theme = await repo.get_by_id(theme_id)
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")
    await repo.delete(theme)
