"""运行时数据状态。"""


class AppState:
    def __init__(self):
        # 数据
        self.students = []
        self.excluded_students = set()
        self.rosters = {}
        self.active_roster_id = ""
        self.task_students = []
        self.image_path = ""
        self.sent_students = set()
        self.unfinished_students = []
        self.total_students = 0
        # 事件控制
        self.working_flag = False
        self.pause_flag = False
        self.waiting_flag = False             # 等待启动阶段（倒计时/等窗口）

    @property
    def selected_students(self):
        return [name for name in self.students if name not in self.excluded_students]

    def reset_progress(self):
        self.sent_students.clear()
        self.task_students = self.selected_students
        self.unfinished_students = self.task_students.copy()
        self.total_students = len(self.task_students)


state = AppState()
