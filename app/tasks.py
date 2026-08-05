"""任务控制：开始、暂停、继续、终止与退出。"""

import threading

from .automation import run_task, smart_sleep
from .config_manager import save_config
from .context import (
    add_log,
    ctx,
    get_template_data,
    render_template,
    set_ui_locked,
    update_status,
)
from .state import state


def pause():
    if not state.working_flag:
        update_status("当前没有发送任务")
        add_log("无法暂停：没有正在进行的任务", "error")
        return
    if state.pause_flag and not state.waiting_flag:
        update_status("任务已经处于暂停状态")
        add_log("任务已经是暂停状态", "error")
        return
    state.pause_flag = True
    state.waiting_flag = False
    update_status("正在暂停，当前步骤结束后会停止")
    add_log("收到暂停请求")


def resume():
    if not state.working_flag:
        update_status("当前没有需要继续的任务")
        add_log("无法继续：没有正在进行的任务", "error")
        return
    if state.waiting_flag:
        update_status("任务正在等待启动，请先切换到企业微信或点击终止")
        add_log("无法继续：任务正在等待启动", "error")
        return
    if not state.pause_flag:
        update_status("任务正在运行中，无需继续")
        add_log("任务正在运行中", "error")
        return
    update_status("即将继续发送，请立刻切换至企业微信窗口")
    add_log("收到继续发送请求，3 秒后恢复")
    state.pause_flag = False
    start()


def begin():
    if state.working_flag:
        update_status("任务正在进行中，请勿重复发送")
        add_log("启动失败：有正在进行的任务", "error")
        return
    state.sent_students.clear()
    state.unfinished_students = state.students.copy()
    start()


def start():
    if state.waiting_flag:
        update_status("任务正在等待启动，请勿重复启动")
        add_log("启动失败：有正在启动的任务", "error")
        return
    if len(state.students) == 0:
        update_status("请先读取学生名单")
        add_log("启动失败：学生名单为空", "error")
        return
    # 主线程中收集控件数据（线程安全）
    template = ctx.message_text.get("1.0", "end-1c").strip()
    current_message = render_template(template, get_template_data())
    if not current_message.strip() and not state.image_path:
        update_status("模板和图片不能同时为空")
        add_log("启动失败：模板和图片不能同时为空", "error")
        return
    state.working_flag = True
    state.waiting_flag = True
    set_ui_locked(True)

    def countdown_and_run():
        # 3秒倒计时（子线程中执行，不阻塞UI）
        for i in range(3):
            update_status(f"请切换至企业微信窗口，{3 - i} 秒后开始...")
            add_log(f"请切换至企业微信窗口，{3 - i} 秒后开始...")
            if not smart_sleep(1):
                return
        state.waiting_flag = False
        threading.Thread(target=run_task, args=(current_message,), daemon=True).start()

    threading.Thread(target=countdown_and_run, daemon=True).start()


def stop():
    if not state.working_flag:
        update_status("当前没有发送任务")
        add_log("终止失败：没有正在运行的任务", "error")
        return
    state.working_flag = False
    state.pause_flag = False
    state.waiting_flag = False
    set_ui_locked(False)
    update_status("发送任务已终止")
    add_log("发送任务已终止", "error")


def exit_app():
    save_config()
    if state.working_flag:
        stop()
    add_log("正在退出程序")
    ctx.root.after(500, ctx.root.destroy)
