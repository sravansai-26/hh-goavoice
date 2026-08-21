from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Document(BaseModel):
    document_id: str
    text: str
    language: str
    source: str = "MSMARCO-XI"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Chunk(BaseModel):
    chunk_id: str
    document_id: str
    strategy: str
    text: str
    language: str
    start_char: int
    end_char: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
