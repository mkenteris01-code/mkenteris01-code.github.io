"""Graph schema and operations for ScholarGraph."""

from typing import Literal
from .schema import SchemaManager
from .nodes import NodeManager
from .relationships import RelationshipManager
from .queries import QueryTemplates, QueryExecutor
from .vector_index import VectorIndexManager, ContentMode, PREVIEW_LENGTH
from .temporal_schema import TemporalSchemaManager

__all__ = [
    "SchemaManager",
    "NodeManager",
    "RelationshipManager",
    "QueryTemplates",
    "QueryExecutor",
    "VectorIndexManager",
    "TemporalSchemaManager",
    "ContentMode",
    "PREVIEW_LENGTH",
]
