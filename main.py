from dataclasses import dataclass
from typing import List, ForwardRef
from datetime import datetime, timedelta
from enum import Enum
from sample_data import *

from bson import ObjectId
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from faker import Faker
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import Model, EmbeddedModel, Field, AIOEngine

import consumers

logging.getLogger().setLevel(logging.INFO)

app = FastAPI()

fake = Faker()

MONGO_URI = "mongodb+srv://vibhor:3rbFGS7rbRmXsBxR@cluster0.zor93e2.mongodb.net/?retryWrites=true&w=majority"  # Change this to your MongoDB URI

client = AsyncIOMotorClient(MONGO_URI)
database = client["your_database_name"]  # Change this to your desired database name

# Example of creating a collection
collection = database["your_collection_name"]  # Change this to your desired collection name

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_methods=['*'],
    allow_headers=['*']
)

user_engine = AIOEngine(client=client, database='user_db')
incident_engine = AIOEngine(client=client, database='incident_db')


class Location(EmbeddedModel):
    latitude: float
    longitude: float


class Status(Enum):
    IN_PROGRESS = 'IN_PROGRESS'
    RESOLVED = 'RESOLVED'
    PENDING = 'PENDING'


class Severity(Enum):
    CRITICAL = 'CRITICAL'
    SERIOUS = 'SERIOUS'
    CONCERNING = 'CONCERNING'
    MILD = 'MILD'


class Emergency(EmbeddedModel):
    name: str
    description: str
    symptoms: str
    treatments: str


class IncidentResponse(Model):
    datetime: datetime
    description: str
    agent: str


class IncidentAdditional(EmbeddedModel):
    incidentResponses: List[IncidentResponse]


class Incident(Model):
    name: str
    description: str
    subject: str
    datetime: datetime
    status: str
    emergency: str
    severity: str
    additional: IncidentAdditional


class UserAdditional(EmbeddedModel):
    incidents: List[Incident]
    preexistingConditions: List[str]
    expertise: List[str]
    equipment: List[str]


class UserModel(Model):
    firstName: str
    lastName: str
    address: str
    bloodType: str
    birthDate: datetime
    createdDate: datetime
    rating: int = 0
    location: Location
    additional: UserAdditional


def getDummyIncident():
    incident_date_time = fake.date_time_this_month()
    return Incident(
        name="Fell on bathroom floor",
        description="Subject fell on bathroom floor and hit their head on a concrete slab",
        subject="65a35175e57e4760959f41ae",
        datetime=incident_date_time,
        status=Status.IN_PROGRESS.name,
        emergency='TRAUMA',
        severity=Severity.CRITICAL.name,
        additional=IncidentAdditional(
            incidentResponses=[
                IncidentResponse(
                    datetime=incident_date_time + timedelta(minutes=5),
                    agent="65a3532e9307f2d788022533",
                    description="Delivered first-aid to victim, Sutured with 0.1M Monocryl thread, administered painkillers"
                )
            ]
        )
    )


def getDummyUserModel():
    return UserModel(
        firstName=fake.first_name(),
        lastName=fake.last_name(),
        address=fake.address(),
        bloodType=getRandomChoice(blood_types),
        birthDate=fake.date_time(),
        createdDate=fake.date_time_this_year(),
        residence=fake.address(),
        rating=fake.random_int(min=1, max=5),
        location=Location(latitude=fake.latitude(), longitude=fake.longitude()),
        additional=UserAdditional(
            incidents=[],
            preexistingConditions=getRandomSizedSample(health_conditions),
            expertise=getRandomSizedSample(medical_expertise),
            equipment=getRandomSizedSample(medical_equipment)
        )
    )


async def try_except(async_fn, *args, **kwargs):
    try:
        return await async_fn(*args, **kwargs)
    except Exception as e:
        logging.error(f"Failed to perform operation {async_fn} due to {str(e)}")
        return None


@app.get('/user')
async def user():
    return await try_except(user_engine.find, UserModel)


@app.post('/user/create')
async def user_create(request: Request):
    body = await request.json()
    user = getDummyUserModel()
    saved_user = await try_except(user_engine.save, user)
    logging.info(f"Saved user {saved_user}")
    return saved_user


@app.get('/incident')
async def incident():
    return await try_except(incident_engine.find, Incident)


@app.post('/incident/create')
async def incident_create(request: Request):
    body = await request.json()
    incident = getDummyIncident()
    saved_incident = await try_except(incident_engine.save, incident)
    logging.info(f"Saved incident {saved_incident}")
    subject_id = saved_incident.subject
    user_to_update = await try_except(user_engine.find_one, UserModel, UserModel.id == ObjectId(subject_id))
    logging.info(f"Retrieved Subject user {user_to_update}")
    user_to_update.additional.incidents.append(incident)
    updated_user = await try_except(user_engine.save, user_to_update)
    logging.info(f"Linked subject user to incident {updated_user}")
    return saved_incident


@app.post('/condition/create')
async def condition_create(request: Request):
    body = await request.json()
    user = getDummyUserModel()
    saved_user = await try_except(user_engine.save, user)
    logging.info(f"Saved user {saved_user}")
    return saved_user

