from datetime import datetime
import uuid
from enum import Enum
from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel


class ItemType(str, Enum):
    flask = "flask"
    pump = "pump"
    computer = "computer"
    other = "other"


class ItemStatus(str, Enum):
    available = "available"
    in_use = "in_use"
    maintenance = "maintenance"
    lost = "lost"
    discarded = "discarded"
    

# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str

    logs: list['ItemLog'] = Relationship(back_populates="operator", cascade_delete=False)
    analyses: list['Analysis'] = Relationship(back_populates="user", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


class LocationBase(SQLModel):
    name: str = Field(min_length=1, max_length=63)
    description: str | None = Field(default=None, max_length=255)

class Location(LocationBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    items: list["Item"] = Relationship(back_populates="location")

class LocationCreate(LocationBase):
    pass

class LocationsPublic(SQLModel):
    locations: dict[uuid.UUID, str]



# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)

    type: ItemType = Field(default=ItemType.other)
    status: ItemStatus = Field(default=ItemStatus.available)





# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore

    location_id: uuid.UUID | None

# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=255)

    location_id: uuid.UUID | None = Field(default=None, foreign_key="location.id")
    location: Location | None = Relationship(back_populates="items")
    logs: list["ItemLog"] = Relationship(back_populates="item", cascade_delete=True, sa_relationship_kwargs={"order_by": "desc(ItemLog.date)"})


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    location_id: uuid.UUID | None


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int

# Sample of air
class Sample(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=63)
    description: str | None = Field(default=None, max_length=255)
    sampled_date: datetime = Field(default_factory=datetime.now)

    measurements: list["Measurement"] = Relationship(back_populates="sample")
    analyses: list["Analysis"] = Relationship(back_populates="sample")
    flasks: list["Flask"] = Relationship(back_populates="sample")

# When measuring a sample on an instrument, if no sample is given, it can also be a air or blank measurement
class Measurement(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=63)
    description: str | None = Field(default=None, max_length=255)

    sample_id: uuid.UUID | None = Field(default=None, foreign_key="sample.id")
    sample: Sample | None = Relationship(back_populates="measurements")


class Analysis(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=63)
    description: str | None = Field(default=None, max_length=255)

    user_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    user: User | None = Relationship(back_populates="analyses")

    sample_id: uuid.UUID | None = Field(default=None, foreign_key="sample.id")
    sample: Sample | None = Relationship(back_populates="analyses")


class LogBase(SQLModel):
    message: str = Field(max_length=2047)
    # Date of the log entry
    date: datetime = Field(default_factory=datetime.now)

class ItemLog(LogBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # Date of when the log entry was registered
    date_registered: datetime = Field(default_factory=datetime.now)
    
    operator_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    operator: User | None = Relationship(back_populates="logs")

    item_id: uuid.UUID | None = Field(default=None, foreign_key="item.id")
    item: Item | None = Relationship(back_populates="logs")

class LogCreate(LogBase):
    item_id: uuid.UUID

class LogPublic(LogBase):
    id: uuid.UUID
    operator_name: str | None
    item_id: uuid.UUID | None

class ItemLogsPublic(SQLModel):
    item_id: uuid.UUID
    data: list[LogPublic]
    count: int



# Database model, database table inferred from class name
class Flask(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    item_id: uuid.UUID | None = Field(default=None, foreign_key="item.id")

    sample_id: uuid.UUID | None = Field(default=None, foreign_key="sample.id")
    sample: Sample | None = Relationship(back_populates="flasks")


# Properties to return via API, id is always required
class FlaskPublic(ItemPublic):

    sample_id: uuid.UUID | None


class FlasksPublic(SQLModel):
    data: list[FlaskPublic]
    count: int




# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)
