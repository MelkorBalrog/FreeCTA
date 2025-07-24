import unittest
from sysml_repository import SysMLRepository

class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.repo = SysMLRepository.get_instance()
        self.repo.elements.clear()
        self.repo.relationships.clear()

    def test_create_elements(self):
        actor = self.repo.create_element("Actor", name="User")
        use_case = self.repo.create_element("Use Case", name="Login")
        self.assertNotEqual(actor.elem_id, use_case.elem_id)
        self.assertEqual(actor.name, "User")
        self.assertEqual(use_case.name, "Login")

    def test_create_relationship(self):
        a = self.repo.create_element("Actor")
        b = self.repo.create_element("Use Case")
        rel = self.repo.create_relationship("Association", a.elem_id, b.elem_id)
        self.assertEqual(rel.source, a.elem_id)
        self.assertEqual(rel.target, b.elem_id)

    def test_serialize(self):
        blk = self.repo.create_element("Block", name="Car")
        js = self.repo.serialize()
        self.assertIn("Car", js)
        self.assertIn(blk.elem_id, js)

if __name__ == '__main__':
    unittest.main()
