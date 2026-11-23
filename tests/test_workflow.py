"""真实 Tk 控件和临时 Excel/JSON；企业微信键鼠操作全部替换为模拟。"""

import json
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import openpyxl

from app import automation, config_manager, students, tasks
from app.context import ctx, set_ui_locked
from app.rosters import RosterStore
from app.state import state
from app.ui.main_window import build_main_window


class RosterWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.store = RosterStore(self.directory / "rosters")
        self.patches = [patch.object(tempfile, "tempdir", str(self.directory)),
                        patch.object(students, "roster_store", self.store),
                        patch.object(config_manager, "CONFIG_FILE", str(self.directory / "config.json"))]
        for replacement in self.patches:
            replacement.start()
            self.addCleanup(replacement.stop)
        state.__init__()
        ctx.student_editor = None
        self.root = build_main_window()
        self.root.withdraw()
        self.callback_errors = []
        self.root.report_callback_exception = lambda *error: self.callback_errors.append(error)
        self.root.update()
        self.addCleanup(self.root.destroy)
        ctx.subject_var.set("数学")

    def tearDown(self):
        state.working_flag = False
        self.root.update()
        self.assertFalse(self.callback_errors)

    def import_excel(self, filename="数学班.xlsx", names=("张三", "李四", "王五")):
        path = self.directory / filename
        workbook = openpyxl.Workbook()
        workbook.active.append(["数学", "英语"])
        for name in names:
            workbook.active.append([name, "赵六"])
        workbook.save(path)
        workbook.close()
        with patch.object(students.filedialog, "askopenfilename", return_value=str(path)):
            students.load_excel()
        self.root.update()
        return state.active_roster_id

    def test_excel_selection_switch_and_restart(self):
        first = self.import_excel()
        students.set_recipients("toggle", ["李四"])
        self.assertEqual(state.selected_students, ["张三", "王五"])
        second = self.import_excel("英语班.xlsx", ("陈七", "周八"))
        students.set_recipients("none")
        ctx.roster_box.current(ctx.roster_ids.index(first))
        students.on_roster_selected()
        self.assertEqual(state.excluded_students, {"李四"})
        self.assertEqual(len(self.store.load_all()[0]), 2)
        state.__init__()
        config_manager.load_config()
        students.load_saved_rosters()
        self.assertEqual(state.active_roster_id, first)
        self.assertEqual(state.selected_students, ["张三", "王五"])
        self.assertEqual(state.rosters[second]["excluded_students"], ["陈七", "周八"])
        self.assertEqual(ctx.student_tree.item("1", "values"), ("☐", "李四", "不发送"))

    def test_select_all_none_invert_and_keyboard(self):
        self.import_excel()
        students.set_recipients("none")
        self.assertEqual(state.total_students, 0)
        students.set_recipients("invert")
        self.assertEqual(state.total_students, 3)
        ctx.student_tree.selection_set("0", "2")
        students.toggle_student(SimpleNamespace(keysym="space"))
        self.assertEqual(state.selected_students, ["李四"])
        students.set_recipients("invert")
        self.assertEqual(state.selected_students, ["张三", "王五"])
        students.set_recipients("all")
        self.assertEqual(state.total_students, 3)

    def test_reimport_retains_exclusions_and_adds_new_students(self):
        roster_id = self.import_excel()
        students.set_recipients("toggle", ["李四"])
        self.import_excel(names=("张三", "李四", "新同学", "张三"))
        self.assertEqual(state.active_roster_id, roster_id)
        self.assertEqual(len(state.rosters), 1)
        self.assertEqual(state.students, ["张三", "李四", "新同学"])
        self.assertEqual(state.selected_students, ["张三", "新同学"])

    def test_no_recipients_does_not_start_task(self):
        self.import_excel()
        students.set_recipients("none")
        with patch.object(tasks.threading, "Thread") as thread:
            tasks.begin()
        thread.assert_not_called()
        self.assertFalse(state.working_flag)

    def test_send_and_resume_never_include_excluded_students(self):
        self.import_excel()
        students.set_recipients("toggle", ["李四"])
        ctx.message_text.delete("1.0", "end")
        ctx.message_text.insert("1.0", "作业提醒")
        with patch.object(tasks.threading, "Thread"):
            tasks.begin()
        self.assertEqual(state.task_students, ["张三", "王五"])
        self.assertEqual(str(ctx.roster_box.cget("state")), "disabled")
        students.set_recipients("all")
        self.assertEqual(state.excluded_students, {"李四"})
        state.waiting_flag = False
        original_process = automation.process_student

        def pause_after_first(name, message):
            success = original_process(name, message)
            if name == "张三":
                state.pause_flag = True
            return success

        with patch.object(automation, "smart_sleep", side_effect=lambda _: not state.pause_flag), \
                patch.object(automation.pyautogui, "hotkey"), \
                patch.object(automation.pyautogui, "press"), \
                patch.object(automation.time, "sleep"), \
                patch.object(automation, "paste") as paste:
            with patch.object(automation, "process_student", side_effect=pause_after_first):
                automation.run_task("作业提醒")
            self.assertEqual(state.sent_students, {"张三"})
            self.assertEqual(state.unfinished_students, ["王五"])
            with patch.object(tasks.threading, "Thread"):
                tasks.resume()
            state.waiting_flag = False
            automation.run_task("作业提醒")
        self.assertEqual([call.args[0] for call in paste.call_args_list], ["张三", "作业提醒", "王五", "作业提醒"])
        self.assertEqual(state.sent_students, {"张三", "王五"})
        self.assertEqual(state.unfinished_students, [])
        self.assertEqual(state.total_students, 2)
        self.root.update()
        self.assertEqual(str(ctx.roster_box.cget("state")), "readonly")

    def test_failed_save_keeps_selection_and_clear_keeps_files(self):
        self.import_excel()
        with patch.object(self.store, "save", side_effect=OSError("模拟只读目录")), \
                patch.object(students.messagebox, "showerror") as error:
            students.set_recipients("none")
        error.assert_called_once()
        self.assertEqual(state.total_students, 3)
        students.clear_students()
        self.assertEqual(state.students, [])
        self.assertEqual(len(self.store.load_all()[0]), 1)

    def test_invalid_excel_keeps_current_roster(self):
        roster_id = self.import_excel()
        ctx.subject_var.set("不存在的科目")
        with patch.object(students.filedialog, "askopenfilename", return_value=str(self.directory / "数学班.xlsx")):
            students.load_excel()
        self.assertEqual(state.active_roster_id, roster_id)
        self.assertEqual(state.students, ["张三", "李四", "王五"])

    def test_editor_saves_full_roster_and_preserves_exclusions(self):
        self.import_excel()
        students.set_recipients("toggle", ["李四"])
        students.save_student_list()
        popup = ctx.student_editor
        text = next(widget for widget in popup.winfo_children() if isinstance(widget, tk.Text))
        text.delete("1.0", "end")
        text.insert("1.0", "张三\n李四\n新同学")
        buttons = popup.winfo_children()[-1].winfo_children()
        buttons[0].invoke()
        self.assertEqual(state.students, ["张三", "李四", "新同学"])
        self.assertEqual(state.excluded_students, {"李四"})
        saved = self.store.load_all()[0][state.active_roster_id]
        self.assertEqual(saved["students"], state.students)

    def open_edited_copy(self):
        students.save_student_list()
        popup = ctx.student_editor
        text = next(widget for widget in popup.winfo_children() if isinstance(widget, tk.Text))
        text.delete("1.0", "end")
        text.insert("1.0", "张三\n李四\n新同学")
        return popup, popup.winfo_children()[-1].winfo_children()[1]

    def test_editor_buttons_stay_visible_at_minimum_and_larger_sizes(self):
        self.import_excel()
        self.root.deiconify()
        self.root.update()
        students.save_student_list()
        popup = ctx.student_editor
        text, buttons = popup.winfo_children()
        min_width, min_height = popup.minsize()
        for width, height in ((min_width, min_height), (460, 360), (640, 520)):
            with self.subTest(size=(width, height)):
                popup.geometry(f"{width}x{height}")
                popup.update()
                self.assertTrue(buttons.winfo_ismapped())
                self.assertGreater(text.winfo_height(), 0)
                self.assertLessEqual(text.winfo_y() + text.winfo_height(), buttons.winfo_y())
                self.assertLessEqual(buttons.winfo_y() + buttons.winfo_height(), popup.winfo_height())
                for button in buttons.winfo_children():
                    self.assertTrue(button.winfo_ismapped())
                    self.assertGreaterEqual(button.winfo_width(), button.winfo_reqwidth())
                    self.assertLessEqual(button.winfo_x() + button.winfo_width(), buttons.winfo_width())
        popup.destroy()

    def test_save_as_preserves_original_and_survives_restart_and_reimport(self):
        original_id = self.import_excel()
        students.set_recipients("toggle", ["李四"])
        original_path = self.store.directory / f"{original_id}.json"
        original_bytes = original_path.read_bytes()
        popup, save_as = self.open_edited_copy()
        with patch.object(students.simpledialog, "askstring", return_value="数学临时组"):
            save_as.invoke()
        copy_id = state.active_roster_id
        self.assertNotEqual(copy_id, original_id)
        self.assertEqual(original_path.read_bytes(), original_bytes)
        self.assertEqual(state.students, ["张三", "李四", "新同学"])
        self.assertEqual(state.excluded_students, {"李四"})
        self.assertFalse(popup.winfo_exists())
        state.__init__()
        config_manager.load_config()
        students.load_saved_rosters()
        self.assertEqual(state.active_roster_id, copy_id)
        copy_path = self.store.directory / f"{copy_id}.json"
        copy_bytes = copy_path.read_bytes()
        self.import_excel(names=("张三", "李四", "王五", "陈七"))
        self.assertEqual(state.active_roster_id, original_id)
        self.assertEqual(copy_path.read_bytes(), copy_bytes)
        self.assertEqual(len(state.rosters), 2)

    def test_save_as_cancel_blank_and_duplicate_keep_original(self):
        original_id = self.import_excel()
        original_path = self.store.directory / f"{original_id}.json"
        original_bytes = original_path.read_bytes()
        popup, save_as = self.open_edited_copy()
        for name in (None, "   ", state.rosters[original_id]["name"]):
            with self.subTest(name=name), \
                    patch.object(students.simpledialog, "askstring", return_value=name), \
                    patch.object(students.messagebox, "showwarning"):
                save_as.invoke()
                self.assertEqual(state.active_roster_id, original_id)
                self.assertEqual(original_path.read_bytes(), original_bytes)
                self.assertEqual(len(list(self.store.directory.glob("*.json"))), 1)
                self.assertTrue(popup.winfo_exists())
        popup.destroy()

    def test_save_as_write_failure_keeps_editor_and_original(self):
        original_id = self.import_excel()
        original_path = self.store.directory / f"{original_id}.json"
        original_bytes = original_path.read_bytes()
        popup, save_as = self.open_edited_copy()
        with patch.object(students.simpledialog, "askstring", return_value="新名单"), \
                patch.object(self.store, "save", side_effect=OSError("模拟保存失败")), \
                patch.object(students.messagebox, "showerror"):
            save_as.invoke()
        self.assertEqual(state.active_roster_id, original_id)
        self.assertEqual(original_path.read_bytes(), original_bytes)
        self.assertEqual(state.students, ["张三", "李四", "王五"])
        self.assertTrue(popup.winfo_exists())
        popup.destroy()


if __name__ == "__main__":
    unittest.main()
