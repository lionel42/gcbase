"""Very similar to the basic Item and modified fro flasks"""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Location,
    LocationCreate,
    LocationsPublic,
    Message,
)

router = APIRouter()




@router.get("/", response_model=LocationsPublic)
def read_locations(
    session: SessionDep, current_user: CurrentUser,
) -> Any:
    """
    Retrieve all locations.
    """


    locations = session.exec(select(Location)).all()

    return LocationsPublic(locations={location.id: location.name for location in locations})

@router.get("/{id}", response_model=Location)
def read_location(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Location | None:
    """
    Retrieve all locations.
    """


    location = session.get(Location, id)

    return location


@router.post("/", response_model=Location)
def create_location(
    *, session: SessionDep, current_user: CurrentUser, location_in: LocationCreate
) -> Any:
    """
    Create new location.
    """
    # Check if the flask is already in the database
    location = session.exec(select(Location).where(Location.name == location_in.name)).first()
    if location:
        raise HTTPException(
            status_code=400,
            detail=f"The location with name {location.name} already exists in the system.",
        )
    location = Location.model_validate(location_in)
    session.add(location)
    session.commit()
    session.refresh(location)
    return location

