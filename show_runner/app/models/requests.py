from pydantic import BaseModel, ConfigDict, Field, field_validator


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str = Field(min_length=1, max_length=120)
    hints: list[str] = Field(min_length=1, max_length=6)
    points: list[int] = Field(min_length=1, max_length=6)

    @field_validator("hints")
    @classmethod
    def hints_valid(cls, hints):
        if any(not h.strip() or len(h) > 500 for h in hints):
            raise ValueError("Clues must contain 1–500 characters")
        return hints

    @field_validator("points")
    @classmethod
    def points_valid(cls, points):
        if any(p < 0 or p > 10000 for p in points):
            raise ValueError("Points must be between 0 and 10,000")
        return points


class CreateRoom(BaseModel):
    names: list[str] = Field(min_length=3, max_length=3)

    @field_validator("names")
    @classmethod
    def names_valid(cls, names):
        names = [name.strip() for name in names]
        if any(not name or len(name) > 32 for name in names):
            raise ValueError("Names must contain 1–32 characters")
        if len({name.casefold() for name in names}) != 3:
            raise ValueError("Use three different contestant names")
        return names


class Login(BaseModel):
    password: str = Field(max_length=256)


class Command(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=8, max_length=80)
    revision: int = Field(ge=0)
    action: str = Field(max_length=32)
    payload: dict = Field(default_factory=dict)
