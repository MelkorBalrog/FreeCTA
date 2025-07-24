import json
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import os

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
        self.root_package = self.create_element("Package", name="Root")

    @classmethod
    def get_instance(cls) -> "SysMLRepository":
        if cls._instance is None:
            cls._instance = SysMLRepository()
        return cls._instance

    def create_element(self, elem_type: str, name: str = "", properties: Optional[Dict[str, str]] = None, owner: Optional[str] = None) -> SysMLElement:
        elem_id = str(uuid.uuid4())
        elem = SysMLElement(elem_id, elem_type, name, properties or {}, owner=owner)
        self.elements[elem_id] = elem
        return elem

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    def create_package(self, name: str, parent: Optional[str] = None) -> SysMLElement:
        """Create a Package element optionally under a parent Package."""
        if parent is None:
            parent = self.root_package.elem_id
        return self.create_element("Package", name=name, owner=parent)

    def delete_element(self, elem_id: str) -> None:
        """Remove an element and any relationships referencing it."""
        if elem_id in self.elements:
            del self.elements[elem_id]
        self.relationships = [r for r in self.relationships if r.source != elem_id and r.target != elem_id]

    def get_element(self, elem_id: str) -> Optional[SysMLElement]:
        return self.elements.get(elem_id)

    def get_qualified_name(self, elem_id: str) -> str:
        elem = self.elements[elem_id]
        parts = [elem.name or elem.elem_id]
        current = elem.owner
        while current:
            parent = self.elements[current]
            parts.append(parent.name or parent.elem_id)
            current = parent.owner
        return "::".join(reversed(parts))

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.serialize())

    def load(self, path: str) -> None:
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.elements.clear()
        self.relationships.clear()
        for e in data.get("elements", []):
            elem = SysMLElement(**e)
            self.elements[elem.elem_id] = elem
        for r in data.get("relationships", []):
            rel = SysMLRelationship(**r)
            self.relationships.append(rel)
        self.root_package = None
        for elem in self.elements.values():
            if elem.elem_type == "Package" and elem.owner is None:
                self.root_package = elem
                break
        if self.root_package is None:
            self.root_package = self.create_element("Package", name="Root")

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

