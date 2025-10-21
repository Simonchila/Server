from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    name: str
    email: EmailStr

    model_config = {
        "validate_by_name": True  # replaces allow_population_by_field_name
    }

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int

    model_config = {
        "from_attributes": True  # replaces orm_mode
    }

class UserLogin(BaseModel):
    email: str
    password: str
