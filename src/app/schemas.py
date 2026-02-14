from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# --- Auth ---
class UserRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    plan: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Forms ---
class FormCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    allowed_origins: str = Field(default="*", max_length=500)
    redirect_url: str | None = Field(default=None, max_length=500)
    email_notifications: bool = True
    notification_email: str | None = Field(default=None, max_length=320)


class FormUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    allowed_origins: str | None = Field(default=None, max_length=500)
    redirect_url: str | None = None
    email_notifications: bool | None = None
    notification_email: str | None = None
    is_active: bool | None = None


class FormResponse(BaseModel):
    id: int
    uuid: str
    name: str
    allowed_origins: str
    redirect_url: str | None
    email_notifications: bool
    notification_email: str | None
    is_active: bool
    created_at: datetime
    submission_count: int = 0

    model_config = {"from_attributes": True}


class FormListResponse(BaseModel):
    forms: list[FormResponse]
    total: int


# --- Submissions ---
class SubmissionResponse(BaseModel):
    id: int
    data: dict
    ip_address: str | None
    is_spam: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SubmissionListResponse(BaseModel):
    submissions: list[SubmissionResponse]
    total: int
    page: int
    per_page: int
