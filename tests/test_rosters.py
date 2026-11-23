import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.rosters import RosterStore
from app.state import AppState


class RosterStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name) / "rosters"
        self.store = RosterStore(self.directory)

    def test_roundtrip_preserves_full_roster_and_exclusions(self):
        roster = self.store.make_roster("数学名单", "数学", [" 张三 ", "李四", "张三", "王", ""])
        roster["excluded_students"] = ["李四", "不存在"]
        self.store.save(roster)
        loaded, errors = RosterStore(self.directory).load_all()
        self.assertFalse(errors)
        self.assertEqual(loaded[roster["id"]]["students"], ["张三", "李四", "王同学"])
        self.assertEqual(loaded[roster["id"]]["excluded_students"], ["李四"])

    def test_files_and_subjects_are_independent(self):
        records = [self.store.make_roster("名单", subject, ["张三"], source)
                   for subject, source in (("数学", "甲/名单.xlsx"), ("英语", "甲/名单.xlsx"),
                                           ("数学", "乙/名单.xlsx"))]
        for record in records:
            self.store.save(record)
        self.assertEqual(len(self.store.load_all()[0]), 3)
        self.assertEqual(records[0]["id"], self.store.make_roster("名单", "数学", [], "甲/名单.xlsx")["id"])

    def test_corrupt_file_does_not_block_other_rosters(self):
        roster = self.store.make_roster("正常名单", "数学", ["张三"])
        self.store.save(roster)
        (self.directory / "broken.json").write_text("{", encoding="utf-8")
        (self.directory / "wrong.json").write_text(json.dumps({"version": 1, "name": "无效", "students": [123]}), encoding="utf-8")
        loaded, errors = self.store.load_all()
        self.assertEqual(list(loaded), [roster["id"]])
        self.assertEqual(len(errors), 2)

    def test_replace_failure_keeps_last_saved_roster(self):
        roster = self.store.make_roster("名单", "数学", ["张三", "李四"])
        self.store.save(roster)
        roster["excluded_students"] = ["李四"]
        with patch("app.rosters.os.replace", side_effect=OSError("模拟写入失败")):
            with self.assertRaises(OSError):
                self.store.save(roster)
        loaded, errors = self.store.load_all()
        self.assertFalse(errors)
        self.assertEqual(loaded[roster["id"]]["excluded_students"], [])

    def test_begin_snapshot_contains_selected_students_only(self):
        state = AppState()
        state.students = ["张三", "李四", "王五"]
        state.excluded_students = {"李四"}
        state.reset_progress()
        self.assertEqual(state.unfinished_students, ["张三", "王五"])
        self.assertEqual(state.total_students, 2)
        state.excluded_students.add("王五")
        self.assertEqual(state.task_students, ["张三", "王五"])


if __name__ == "__main__":
    unittest.main()
