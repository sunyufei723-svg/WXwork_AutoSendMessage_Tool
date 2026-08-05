"""运行时数据状态。"""


class AppState:
    def __init__(self):
        # 数据
        self.students = []
        self.image_path = ""
        self.sent_students = set()
        self.unfinished_students = []
        self.total_students = 0
        # 事件控制
        self.working_flag = False
        self.pause_flag = False
        self.waiting_flag = False             # 等待启动阶段（倒计时/等窗口）


state = AppState()
