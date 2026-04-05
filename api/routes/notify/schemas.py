from pydantic import BaseModel
from uuid import UUID
from typing import List


class NotifyRequest(BaseModel):
    application_id: UUID


class BulkNotifyRequest(BaseModel):
    application_ids: List[UUID]


class BulkNotifyResponse(BaseModel):
    succeeded: List[str]
    failed: List[dict]
    total: int
