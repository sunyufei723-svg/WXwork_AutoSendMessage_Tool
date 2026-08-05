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
        self.student_listbox = None
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
    """将 state.students 写入第2页学生名单文本框，并更新人数标签"""
    ctx.student_info_var.set(f"已加载 {len(state.students)} 名学生")
    ctx.student_listbox.delete("1.0", "end")
    ctx.student_listbox.insert("1.0", "\n".join(state.students))


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
    # 学生名单文本框：锁定时禁用，解锁时恢复可编辑
    ctx.student_listbox.config(state=new_state)
    ctx.message_text.config(state=new_state)
    ctx.message_box.config(state=new_state)
    ctx.date_entry.config(state=new_state)
    for entry in ctx.right_entries.values():
        entry.config(state=new_state)
    ctx.subject_box.config(state=new_state)
