"""
控件中心容器与线程安全的 GUI 更新函数。

ctx 集中持有 UI 模块创建的所有控件引用，其他模块通过 ctx 读写控件，
替代原单文件脚本中的模块级全局变量。
add_log / update_status 等更新函数统一经 root.after 回到主线程执行，保证线程安全。
"""

import os

from .state import state


class AppContext:
    """集中保存控件引用与运行参数。"""

    def __init__(self):
        # 主窗口与公共控件
        self.root = None
        self.status_var = None
        self.log_box = None
        # 基础信息
        self.date_entry = None
        self.subject_var = None
        self.subject_box = None
        self.interval_entry = None
        self.last_valid_interval = "1"
        # 作业数据
        self.count_entry = None
        self.rate_entry = None
        self.avg_entry = None
        self.max_entry = None
        self.content_entry = None
        self.date_dead_entry = None
        self.right_entries = {}
        # 模板编辑
        self.template_dict = {}
        self.template_name_var = None
        self.message_box = None
        self.message_text = None
        self.preview_box = None
        # 名单与图片
        self.student_info_var = None
        self.recipient_summary_var = None
        self.student_tree = None
        self.roster_box = None
        self.roster_var = None
        self.roster_ids = []
        self.student_editor = None
        self.image_info_var = None
        # 发送统计
        self.total_var = None
        self.success_var = None
        self.unfinished_var = None
        self.progress_var = None
        # 任务运行期间需要禁用的按钮
        self.lockable_buttons = []


ctx = AppContext()

# =========================
# 模板渲染
# =========================
def render_template(template, data):
    """替换模板中的 {{变量名}}。"""
    for key, value in data.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))
    return template


def get_template_data():
    """
    统一收集模板变量。
    避免 update_preview() 和 start() 重复写同一份 data。
    """
    return {
        "date": ctx.date_entry.get().strip(),
        "subject": ctx.subject_var.get().strip(),
        "count": ctx.count_entry.get().strip(),
        "rate": ctx.rate_entry.get().strip(),
        "avg": ctx.avg_entry.get().strip(),
        "max": ctx.max_entry.get().strip(),
        "content": ctx.content_entry.get().strip(),
        "date_dead": ctx.date_dead_entry.get().strip(),
    }

# =========================
# GUI 更新（线程安全）
# =========================
def add_log(text, tag="info"):
    ctx.root.after(
        0,
        lambda: (
            ctx.log_box.insert("end", text + "\n", tag),
            ctx.log_box.see("end")
        )
    )


def update_status(text):
    ctx.root.after(
        0,
        lambda: ctx.status_var.set(text)
    )


def refresh_student_text():
    """刷新名单与本次发送标记；原始名单包含未勾选的学生。"""
    selected = len(state.selected_students)
    ctx.student_info_var.set(
        f"名单 {len(state.students)} 人\n本次发送 {selected} 人\n不发送 {len(state.students) - selected} 人"
    )
    roster = state.rosters.get(state.active_roster_id)
    title = f"{roster['name']} · {roster.get('subject', '')}" if roster else "未选择名单"
    ctx.recipient_summary_var.set(f"{title}：本次发送 {selected} 人 / 名单 {len(state.students)} 人")
    tree = ctx.student_tree
    children = tree.get_children()
    if children:
        tree.delete(*children)
    for index, name in enumerate(state.students):
        included = name not in state.excluded_students
        tree.insert("", "end", iid=str(index), values=(
            "☑" if included else "☐", name, "发送" if included else "不发送"
        ), tags=(() if included else ("excluded",)))


def update_preview(*args):
    template = ctx.message_text.get("1.0", "end-1c").strip()
    preview = render_template(
        template,
        get_template_data()
    )
    ctx.preview_box.config(state="normal")
    ctx.preview_box.delete("1.0", "end")
    ctx.preview_box.insert("end", preview)
    ctx.preview_box.config(state="disabled")


def update_image_info():
    if state.image_path:
        ctx.image_info_var.set(
            f"已加载：{os.path.basename(state.image_path)}"
        )
    else:
        ctx.image_info_var.set("未加载图片")


def update_send_stats():
    total = state.total_students
    success = len(state.sent_students)
    unfinished = len(state.unfinished_students)
    if total > 0:
        progress = success / total * 100
    else:
        progress = 0
    ctx.root.after(
        0,
        lambda: (
            ctx.total_var.set(f"总数：{total}"),
            ctx.success_var.set(f"成功：{success}"),
            ctx.unfinished_var.set(f"未完成：{unfinished}"),
            ctx.progress_var.set(progress)
        )
    )

# =========================
# UI 锁定控制
# =========================
def set_ui_locked(locked):
    """锁定/解锁 UI 控件。locked=True 时禁止修改内容，只允许任务控制。"""
    new_state = "disabled" if locked else "normal"
    for btn in ctx.lockable_buttons:
        btn.config(state=new_state)
    ctx.interval_entry.config(state=new_state)
    ctx.roster_box.config(state="disabled" if locked else "readonly")
    ctx.message_text.config(state=new_state)
    ctx.message_box.config(state=new_state)
    ctx.date_entry.config(state=new_state)
    for entry in ctx.right_entries.values():
        entry.config(state=new_state)
    ctx.subject_box.config(state=new_state)
