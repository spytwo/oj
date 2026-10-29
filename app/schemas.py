from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ThemeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ThemeRead(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubthemeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class SubthemeRead(BaseModel):
    id: int
    name: str
    created_at: datetime
    theme_id: int

    model_config = ConfigDict(from_attributes=True)


class RecordCreate(BaseModel):
    content: str = Field(min_length=1)


class RecordRead(BaseModel):
    id: int
    content: str
    created_at: datetime
    subtheme_id: int

    model_config = ConfigDict(from_attributes=True)


class RecordSearchRead(BaseModel):
    id: int
    content: str
    created_at: datetime
    subtheme_id: int
    subtheme_name: str
    theme_name: str

    model_config = ConfigDict(from_attributes=True)
