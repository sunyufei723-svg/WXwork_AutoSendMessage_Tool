"""学生名单与作业图片管理：Excel/文字导入、保存、清空、图片选择。"""

import os
import re
import tkinter as tk
from tkinter import filedialog, ttk

import openpyxl

from .context import (
    add_log,
    ctx,
    refresh_student_text,
    update_image_info,
    update_send_stats,
    update_status,
)
from .state import state


def normalize_student_name(name):
    name = name.strip()
    if len(name) == 1:
        return name + "同学"
    return name


def load_text_students():
    popup = tk.Toplevel(ctx.root)
    popup.title("导入名单")
    popup.geometry("560x400")          # 初始尺寸
    popup.minsize(420, 300)            # 最小尺寸，保证确认/取消按钮始终完整显示
    popup.resizable(True, True)        # 允许横向、纵向拉伸
    popup.configure(bg="#f5f5f5")

    header = tk.Label(popup, text="请输入学生名单", font=("微软雅黑", 11, "bold"), bg="#f5f5f5")
    header.grid(row=0, column=0, pady=(8, 2))
    hint = tk.Label(popup, text="支持空格、换行、中文逗号、英文逗号分隔", font=("微软雅黑", 9), fg="#888", bg="#f5f5f5")
    hint.grid(row=1, column=0, pady=(0, 8))

    # 文本输入框：占据唯一伸缩权重，随窗口横纵拉伸
    text_box = tk.Text(popup, width=30, height=12, font=("微软雅黑", 10), relief="solid", bd=1)
    text_box.grid(row=2, column=0, padx=12, pady=0, sticky="nsew")

    def confirm():
        raw_text = text_box.get("1.0", "end")
        names = re.split(r"[\s,，]+", raw_text)
        result = []
        for name in names:
            name = name.strip()
            if not name:
                continue
            result.append(normalize_student_name(name))
        state.students = result.copy()
        state.sent_students.clear()
        state.unfinished_students = result.copy()
        state.total_students = len(state.students)
        refresh_student_text()
        update_send_stats()
        add_log(f"已从文字导入 {len(state.students)} 名学生")
        update_status("文字名单已加载")
        popup.destroy()

    # 按钮行固定在底部，不参与伸缩，任何窗口尺寸下都保持可见
    btn_frame = tk.Frame(popup, bg="#f5f5f5")
    btn_frame.grid(row=3, column=0, pady=8)
    ttk.Button(btn_frame, text="确定", command=confirm, width=14).grid(row=0, column=0, padx=8)
    ttk.Button(btn_frame, text="取消", command=popup.destroy, width=14).grid(row=0, column=1, padx=8)

    popup.grid_columnconfigure(0, weight=1)
    popup.grid_rowconfigure(2, weight=1)     # 只有文本框所在行随窗口拉伸


def load_excel():
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    if not file_path:
        return
    try:
        # 用 openpyxl 直读首个工作表，避免引入重量级的 pandas
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        try:
            rows = wb.active.iter_rows(values_only=True)
            header = next(rows, None)
            header = [
                str(cell).strip() if cell is not None else ""
                for cell in (header or ())
            ]
            subject = ctx.subject_var.get().strip()
            if subject not in header:
                add_log(f"Excel中没有找到列：{subject}", "error")
                update_status("Excel列名不匹配")
                return
            col_index = header.index(subject)
            state.students = [
                normalize_student_name(str(row[col_index]))
                for row in rows
                if col_index < len(row)
                and row[col_index] is not None
                and str(row[col_index]).strip()
            ]
        finally:
            wb.close()
        state.sent_students.clear()
        state.unfinished_students = state.students.copy()
        state.total_students = len(state.students)
        refresh_student_text()
        update_send_stats()
        add_log(f"{subject}：已读取 {len(state.students)} 名学生")
        update_status(f"{subject}名单已加载")
    except Exception as e:
        add_log(f"读取 Excel 失败：{e}", "error")
        update_status("读取 Excel 失败")


def save_student_list():
    """从文本框中读取修改后的名单，更新 state.students"""
    raw = ctx.student_listbox.get("1.0", "end").strip()
    if not raw:
        state.students = []
        state.sent_students.clear()
        state.unfinished_students = []
        state.total_students = 0
    else:
        names = [line.strip() for line in raw.splitlines() if line.strip()]
        clean_names = []
        for name in names:
            if name.endswith(" [已发送]"):
                name = name[:-len(" [已发送]")]
            clean_names.append(normalize_student_name(name))
        state.students = clean_names
        state.unfinished_students = [
            name for name in state.students
            if name not in state.sent_students
        ]
        state.total_students = len(state.students)
    refresh_student_text()
    update_send_stats()
    add_log(f"名单已更新，共 {len(state.students)} 名学生")
    update_status("学生名单已修改")


def clear_students():
    state.students.clear()
    state.sent_students.clear()
    state.unfinished_students.clear()
    state.total_students = 0
    refresh_student_text()
    update_send_stats()
    add_log("学生名单已清空")
    update_status("学生名单已清空")


def load_image():
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
    if not file_path:
        return
    state.image_path = file_path
    update_image_info()
    add_log(f"已选择图片：{os.path.basename(file_path)}")
    update_status("图片已加载")


def clear_image():
    state.image_path = ""
    update_image_info()
    add_log("作业图片已删除")
    update_status("作业图片已删除")
