import json
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class SysMLElement:
    """Basic SysML element stored in the repository."""
    elem_id: str
    elem_type: str
    name: str = ""
    properties: Dict[str, str] = field(default_factory=dict)
    stereotypes: Dict[str, str] = field(default_factory=dict)
    owner: Optional[str] = None

@dataclass
class SysMLRelationship:
    rel_id: str
    rel_type: str
    source: str
    target: str
    stereotype: Optional[str] = None
    properties: Dict[str, str] = field(default_factory=dict)

class SysMLRepository:
    """Singleton repository for all SysML elements and relationships."""
    _instance = None

    def __init__(self):
        self.elements: Dict[str, SysMLElement] = {}
        self.relationships: List[SysMLRelationship] = []

    @classmethod
    def get_instance(cls) -> "SysMLRepository":
        if cls._instance is None:
            cls._instance = SysMLRepository()
        return cls._instance

    def create_element(self, elem_type: str, name: str = "", properties: Optional[Dict[str, str]] = None) -> SysMLElement:
        elem_id = str(uuid.uuid4())
        elem = SysMLElement(elem_id, elem_type, name, properties or {})
        self.elements[elem_id] = elem
        return elem

    def create_relationship(self, rel_type: str, source: str, target: str, stereotype: Optional[str] = None, properties: Optional[Dict[str, str]] = None) -> SysMLRelationship:
        rel_id = str(uuid.uuid4())
        rel = SysMLRelationship(rel_id, rel_type, source, target, stereotype, properties or {})
        self.relationships.append(rel)
        return rel

    def serialize(self) -> str:
        data = {
            "elements": [elem.__dict__ for elem in self.elements.values()],
            "relationships": [rel.__dict__ for rel in self.relationships],
        }
        return json.dumps(data, indent=2)

