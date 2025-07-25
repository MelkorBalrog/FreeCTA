import unittest
from sysml_repository import SysMLRepository

class ActionNameTests(unittest.TestCase):
    def setUp(self):
        SysMLRepository._instance = None
        self.repo = SysMLRepository.get_instance()

    def test_activity_actions(self):
        diag = self.repo.create_diagram("Activity Diagram", name="MainFlow")
        act = self.repo.create_element("Action Usage", name="DoThing")
        obj = {
            "obj_id": 1,
            "obj_type": "Action Usage",
            "x": 10,
            "y": 10,
            "element_id": act.elem_id,
            "width": 20,
            "height": 20,
            "properties": {"name": "DoThing"},
        }
        diag.objects.append(obj)
        names = self.repo.get_activity_actions()
        self.assertIn("MainFlow", names)
        self.assertIn("DoThing", names)

if __name__ == '__main__':
    unittest.main()
