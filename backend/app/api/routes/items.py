import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Item,
    ItemCreate,
    ItemLogsPublic,
    ItemPublic,
    ItemsPublic,
    ItemUpdate,
    Location,
    LogCreate,
    Message,
    LogPublic,
    ItemLog,
)

router = APIRouter()


@router.get("/", response_model=ItemsPublic)
def read_items(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve items.
    """

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Item)
        count = session.exec(count_statement).one()
        statement = select(Item).offset(skip).limit(limit)
        items = session.exec(statement).all()
    else:
        count_statement = select(func.count()).select_from(Item)
        count = session.exec(count_statement).one()
        statement = select(Item).offset(skip).limit(limit)
        items = session.exec(statement).all()

    return ItemsPublic(data=items, count=count)


@router.get("/{id}", response_model=ItemPublic)
def read_item(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get item by ID.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("/", response_model=ItemPublic)
def create_item(
    *, session: SessionDep, current_user: CurrentUser, item_in: ItemCreate
) -> Any:
    """
    Create new item.
    """
    item = Item.model_validate(item_in)
    log = ItemLog(
        message=f"Item created via FastAPI.",
        operator_id=current_user.id,
        item_id=item.id,
    )
    session.add(item)
    session.add(log)
    session.commit()
    session.refresh(item)
    return item


@router.put("/{id}", response_model=ItemPublic)
def update_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    item_in: ItemUpdate,
) -> Any:
    """
    Update an item.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    update_dict = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_dict)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{id}")
def delete_item(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete an item.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(item)
    session.commit()
    return Message(message="Item deleted successfully")


@router.post("/move/{item_id}_{new_location}", response_model=Location)
def move_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    new_location: uuid.UUID | None,
    item_id: uuid.UUID,
) -> Any:
    """
    Move flask to new location.
    """

    location = session.get(Location, new_location)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    # Check if the flask is already in the new location
    if item.location_id == location.id:
        raise HTTPException(
            status_code=400,
            detail=f"Item {item.title} is already in the location {location.name}.",
        )
    log = ItemLog(
        message=f"Item moved from {item.location.name if item.location else None} to {location.name}.",
        operator_id=current_user.id,
        item_id=item.id,
    )
    item.location_id = location.id
    session.add(item)
    session.add(log)
    session.commit()
    session.refresh(item)
    return location


@router.get("/logs/{item_id}", response_model=ItemLogsPublic)
def read_item_logs(
    *, session: SessionDep, current_user: CurrentUser, item_id: uuid.UUID
) -> Any:
    """
    Retrieve item logs.
    """
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    logs = [
        LogPublic(
            id=log.id,
            item_id=log.item_id,
            message=log.message,
            date=log.date,
            operator_name=log.operator.full_name,
        )
        for log in item.logs
    ]
    return ItemLogsPublic(data=logs, count=len(logs), item_id=item.id)


@router.post("/logs/{item_id}", response_model=LogPublic)
def create_item_log(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    log_create: LogCreate,
) -> Any:
    """
    Create new item log.
    """
    item = session.get(Item, log_create.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    log = ItemLog(
        message=log_create.message,
        operator_id=current_user.id,
        item_id=item.id,
        date=log_create.date,
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    return LogPublic(
        id=log.id,
        item_id=log.item_id,
        message=log.message,
        date=log.date,
        operator_name=log.operator.full_name,
    )
