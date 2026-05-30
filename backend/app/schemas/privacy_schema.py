from pydantic import BaseModel, ConfigDict


class PrivacyOut(BaseModel):
    show_email: bool
    show_phone: bool
    show_age: bool
    allow_search: bool

    model_config = ConfigDict(from_attributes=True)


class PrivacyUpdateRequest(BaseModel):
    show_email: bool | None = None
    show_phone: bool | None = None
    show_age: bool | None = None
    allow_search: bool | None = None

