"""企业微信自动化：剪贴板操作、窗口检测与单个学生的发送流程。"""

import io
import time

import pyautogui
import pygetwindow as gw
import pyperclip
import win32clipboard
from PIL import Image

from .constants import APP_TITLE
from .context import add_log, ctx, set_ui_locked, update_send_stats, update_status
from .state import state


def paste(text):
    pyperclip.copy(text)
    pyautogui.hotkey("ctrl", "v")


def check_wecom():
    """检查当前活动窗口是否是企业微信（排除本程序自身窗口）。"""
    try:
        window = gw.getActiveWindow()
        if window is None:
            return False
        title = window.title
        # 排除本程序自己的窗口
        if APP_TITLE in title:
            return False
        return "企业微信" in title
    except Exception:
        return False


def send_image(file_path):
    """把图片放入剪贴板，然后粘贴发送。"""
    try:
        image = Image.open(file_path)
        output = io.BytesIO()
        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        finally:
            win32clipboard.CloseClipboard()
        pyautogui.hotkey("ctrl", "v")
        pyautogui.press("enter")
        return True
    except Exception as e:
        add_log(f"图片发送失败：{e}", "error")
        return False


def smart_sleep(s):
    eclipse = 0.0
    while eclipse < s:
        if state.pause_flag and not state.waiting_flag:
            update_status("发送任务已暂停")
            add_log("发送任务已暂停", "error")
            state.waiting_flag = False
            return False
        if not state.working_flag:
            update_status("发送任务已终止")
            add_log("发送任务已终止", "error")
            state.pause_flag = False
            state.waiting_flag = False
            return False
        if (not state.waiting_flag) and (not check_wecom()):
            update_status("未检测到企业微信窗口，任务已暂停")
            add_log("未检测到企业微信窗口，已自动暂停", "error")
            state.pause_flag = True
            state.waiting_flag = False
            return False
        time.sleep(0.1)
        eclipse += 0.1
    return True


def process_student(name, current_message):
    interval = float(ctx.interval_entry.get().strip())
    if not smart_sleep(interval):
        return False
    try:
        # 1. 打开搜索框
        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.3)
        # 2. 清空搜索框
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.2)
        pyautogui.press("backspace")
        time.sleep(0.2)
        # 3. 粘贴学生姓名
        paste(name)
        if not smart_sleep(interval):
            return False
        # 4. 回车进入群聊
        pyautogui.press("enter")
        time.sleep(0.3)
        # 5. 清空输入框
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.2)
        pyautogui.press("backspace")
        time.sleep(0.2)
        # 6. 发送文字
        if current_message.strip():
            paste(current_message)
            if not smart_sleep(interval):
                return False
            pyautogui.press("enter")
            if not smart_sleep(interval):
                return False
        # 7. 发送图片
        if state.image_path:
            if not send_image(state.image_path):
                state.pause_flag = True
                add_log(f"{name} 图片发送失败", "error")
                return False
            if not smart_sleep(interval):
                return False
        # 8. 记为完成
        if name not in state.sent_students:
            state.sent_students.add(name)
            state.unfinished_students = [
                name
                for name in state.task_students
                if name not in state.sent_students
            ]
        return True
    except Exception as e:
        state.pause_flag = True
        add_log(f"{name} 发送异常：{e}", "error")
        return False


def run_task(current_message):
    task_students = state.unfinished_students.copy()
    add_log("开始发送任务")
    update_status("正在发送")
    for index, student_name in enumerate(task_students, start=1):
        update_status(f"正在发送：({len(state.sent_students)+1}/{state.total_students}) {student_name}")
        add_log(f"正在发送：{student_name}")
        success = process_student(student_name, current_message)
        if not success:
            update_send_stats()
            break
        add_log(f"{student_name} 发送完成", "success")
        update_send_stats()
    # 任务结束统计
    if not state.working_flag:
        update_status("发送任务已终止")
        add_log("发送任务已终止", "error")
        state.working_flag = False
    elif state.pause_flag:
        update_status("发送任务已暂停")
        add_log("发送任务已暂停", "error")
    else:
        update_status("发送完成")
        add_log("发送完成", "success")
        state.working_flag = False
        ctx.root.after(0, lambda: set_ui_locked(False))
    add_log("=" * 20)
    add_log(f"发送成功：{len(state.sent_students)}人", "success")
    for name in state.sent_students:
        add_log(name, "success")
    add_log("─" * 20)
    add_log(f"未完成：{len(state.unfinished_students)}人", "error")
    for name in state.unfinished_students:
        add_log(name, "error")
    add_log("=" * 20)
