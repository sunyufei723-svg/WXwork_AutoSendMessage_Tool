"""学生名单与作业图片管理：Excel/文字导入、保存、清空、图片选择。"""

import os
import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

import openpyxl

from .constants import ROSTER_DIR
from .context import (
    add_log,
    ctx,
    refresh_student_text,
    update_image_info,
    update_send_stats,
    update_status,
)
from .state import state
from .rosters import RosterStore, clean_students


roster_store = RosterStore(ROSTER_DIR)


def _remember_roster():
    from .config_manager import save_config
    try:
        save_config()
    except OSError as exc:
        add_log(f"名单已保存，但记住当前名单失败：{exc}", "error")


def _refresh_roster_choices():
    ctx.roster_ids = list(state.rosters)
    labels = [
        f"{r['name']} · {r.get('subject', '')} [{i + 1}]"
        for i, r in enumerate(state.rosters.values())
    ]
    ctx.roster_box.config(values=labels)
    if state.active_roster_id in ctx.roster_ids:
        ctx.roster_box.current(ctx.roster_ids.index(state.active_roster_id))
    else:
        ctx.roster_var.set("")


def _activate_roster(roster_id):
    state.active_roster_id = roster_id
    roster = state.rosters.get(roster_id)
    state.students = roster["students"].copy() if roster else []
    state.excluded_students = set(roster["excluded_students"]) if roster else set()
    if roster and roster.get("subject"):
        ctx.subject_var.set(roster["subject"])
        from .context import update_preview
        update_preview()
    state.reset_progress()
    _refresh_roster_choices()
    refresh_student_text()
    update_send_stats()


def load_saved_rosters():
    state.rosters, errors = roster_store.load_all()
    previous = state.active_roster_id
    _activate_roster(previous if previous in state.rosters else next(iter(state.rosters), ""))
    add_log(f"启动时加载 JSON 名单：{len(state.rosters)} 份")
    for error in errors:
        add_log(f"跳过无法读取的名单：{error}", "error")
    if errors:
        update_status(f"已加载 {len(state.rosters)} 份名单，{len(errors)} 份读取失败（详见日志）")


def on_roster_selected(event=None):
    if state.working_flag:
        _refresh_roster_choices()
        return
    index = ctx.roster_box.current()
    if index < 0:
        return
    _activate_roster(ctx.roster_ids[index])
    _remember_roster()
    add_log(f"已切换名单：{state.rosters[state.active_roster_id]['name']}")
    update_status("名单已切换，请确认本次发送对象")


def _save_and_activate(roster):
    """先写入成功再更新当前名单，写入失败时保留原有数据和选择。"""
    try:
        saved = roster_store.save(roster)
    except (OSError, ValueError) as exc:
        add_log(f"保存 JSON 名单失败：{exc}", "error")
        update_status("名单保存失败，原名单与选择已保留")
        messagebox.showerror("名单保存失败", str(exc), parent=ctx.root)
        return False
    state.rosters[saved["id"]] = saved
    _activate_roster(saved["id"])
    _remember_roster()
    return True


def set_recipients(mode, names=()):
    if state.working_flag or not state.active_roster_id:
        return
    excluded = set(state.excluded_students)
    if mode == "all":
        excluded.clear()
    elif mode == "none":
        excluded = set(state.students)
    elif mode == "invert":
        excluded = set(state.students) - excluded
    elif mode == "toggle":
        excluded.symmetric_difference_update(names)
    else:
        return
    roster = dict(state.rosters[state.active_roster_id])
    roster["excluded_students"] = [n for n in state.students if n in excluded]
    view = ctx.student_tree.yview()
    selected_rows = ctx.student_tree.selection()
    if _save_and_activate(roster):
        ctx.student_tree.yview_moveto(view[0])
        ctx.student_tree.selection_set(*selected_rows)
        update_status(f"本次发送 {len(state.selected_students)} 人，选择已自动保存")


def toggle_student(event):
    tree = ctx.student_tree
    if event.keysym == "space":
        rows = tree.selection()
    else:
        if tree.identify_region(event.x, event.y) != "cell":
            return
        row = tree.identify_row(event.y)
        rows = (row,) if row else ()
        if row:
            tree.focus_set()
            tree.focus(row)
            tree.selection_set(row)
    if rows:
        set_recipients("toggle", [state.students[int(row)] for row in rows])
    return "break"


def normalize_student_name(name):
    name = name.strip()
    if len(name) == 1:
        return name + "同学"
    return name


def load_text_students():
    if state.working_flag:
        return
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
        if state.working_flag:
            return
        raw_text = text_box.get("1.0", "end")
        names = re.split(r"[\s,，]+", raw_text)
        result = []
        for name in names:
            name = name.strip()
            if not name:
                continue
            result.append(normalize_student_name(name))
        if not result:
            messagebox.showwarning("名单为空", "请至少输入一名学生。", parent=popup)
            return
        name = simpledialog.askstring("保存名单", "名单名称（相同名称和科目会更新原名单）：", parent=popup)
        if not name or not name.strip():
            return
        roster = roster_store.make_roster(name.strip(), ctx.subject_var.get().strip(), result)
        old = state.rosters.get(roster["id"])
        if old:
            if not messagebox.askyesno("更新名单", f"是否更新已有名单“{name.strip()}”？", parent=popup):
                return
            roster["excluded_students"] = old["excluded_students"]
        if _save_and_activate(roster):
            add_log(f"已从文字导入并保存 {len(state.students)} 名学生")
            update_status("文字名单已保存为 JSON")
            popup.destroy()

    # 按钮行固定在底部，不参与伸缩，任何窗口尺寸下都保持可见
    btn_frame = tk.Frame(popup, bg="#f5f5f5")
    btn_frame.grid(row=3, column=0, pady=8)
    ttk.Button(btn_frame, text="确定", command=confirm, width=14).grid(row=0, column=0, padx=8)
    ttk.Button(btn_frame, text="取消", command=popup.destroy, width=14).grid(row=0, column=1, padx=8)

    popup.grid_columnconfigure(0, weight=1)
    popup.grid_rowconfigure(2, weight=1)     # 只有文本框所在行随窗口拉伸
    popup.transient(ctx.root)
    popup.grab_set()


def load_excel():
    if state.working_flag:
        return
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
            students = [
                normalize_student_name(str(row[col_index]))
                for row in rows
                if col_index < len(row)
                and row[col_index] is not None
                and str(row[col_index]).strip()
            ]
        finally:
            wb.close()
        if not students:
            update_status("Excel 名单为空，当前名单已保留")
            add_log(f"{subject}列没有学生，未保存名单", "error")
            return
        roster = roster_store.make_roster(Path(file_path).stem, subject, students, file_path)
        old = state.rosters.get(roster["id"])
        if old:
            roster["excluded_students"] = old["excluded_students"]
        if _save_and_activate(roster):
            add_log(f"{subject}：已读取并保存 {len(state.students)} 名学生")
            update_status(f"{subject}名单已保存为 JSON")
    except Exception as e:
        add_log(f"读取 Excel 失败：{e}", "error")
        update_status("读取 Excel 失败")


def save_student_list():
    """在独立弹窗编辑名单，可更新当前名单或另存为独立的新名单。"""
    if state.working_flag or not state.active_roster_id:
        update_status("请先选择或导入名单")
        return
    if ctx.student_editor and ctx.student_editor.winfo_exists():
        ctx.student_editor.lift()
        return
    roster_id = state.active_roster_id
    popup = tk.Toplevel(ctx.root)
    ctx.student_editor = popup
    popup.title("编辑名单（每行一名学生）")
    popup.geometry("460x360")
    popup.minsize(380, 220)
    popup.grid_columnconfigure(0, weight=1)
    popup.grid_rowconfigure(0, weight=1)
    text = tk.Text(popup, width=24, height=8, font=("微软雅黑", 10), wrap="none")
    text.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
    text.insert("1.0", "\n".join(state.students))

    def confirm(save_as=False):
        if state.working_flag:
            return
        original = state.rosters[roster_id]
        edited_students = clean_students(text.get("1.0", "end").splitlines())
        if save_as:
            name = simpledialog.askstring(
                "另存为新名单", "新名单名称（原名单保持不变）：",
                initialvalue=f"{original['name']}（副本）", parent=popup,
            )
            if name is None:
                return
            name = name.strip()
            if not name:
                messagebox.showwarning("名称为空", "请输入新名单名称。", parent=popup)
                return
            if any(r["name"].strip().casefold() == name.casefold()
                   and r.get("subject", "") == original.get("subject", "")
                   for r in state.rosters.values()):
                messagebox.showwarning("名单已存在", "该科目已有同名名单，请使用其他名称。", parent=popup)
                return
            roster = roster_store.copy_roster(original, name, edited_students)
        else:
            roster = dict(original, students=edited_students)
        if _save_and_activate(roster):
            if save_as:
                add_log(f"已另存为“{name}”，共 {len(state.students)} 名学生，原名单保持不变")
                update_status("已另存并切换到新名单")
            else:
                add_log(f"名单已更新并保存，共 {len(state.students)} 名学生")
                update_status("名单修改已保存")
            popup.destroy()

    buttons = ttk.Frame(popup)
    buttons.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
    ttk.Button(buttons, text="保存到当前名单", command=confirm).pack(side="left")
    ttk.Button(buttons, text="另存为新名单", command=lambda: confirm(True)).pack(side="left", padx=8)
    ttk.Button(buttons, text="取消", command=popup.destroy).pack(side="right")
    popup.update_idletasks()
    popup.minsize(max(380, buttons.winfo_reqwidth() + 24), 220)
    popup.transient(ctx.root)
    popup.grab_set()


def clear_students():
    if state.working_flag:
        return
    _activate_roster("")
    _remember_roster()
    add_log("已取消当前名单，已保存的 JSON 名单仍可从下拉框选择")
    update_status("已取消当前名单")


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
