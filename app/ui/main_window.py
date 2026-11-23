"""主窗口构建：创建三个页签的全部控件，并把控件注册到 ctx。"""

import time
import tkinter as tk
from tkinter import ttk

from ..config_manager import load_config
from ..constants import (
    APP_TITLE,
    BG_CARD,
    BG_MAIN,
    CLR_DANGER,
    CLR_SUCCESS,
    FG_HINT,
    FG_LABEL,
    FG_TITLE,
)
from ..context import add_log, ctx, update_preview, update_status
from ..students import (
    clear_image,
    clear_students,
    load_excel,
    load_image,
    load_saved_rosters,
    load_text_students,
    on_roster_selected,
    save_student_list,
    set_recipients,
    toggle_student,
)
from ..tasks import begin, exit_app, pause, resume, stop
from ..templates import (
    load_local_template,
    load_templates_from_folder,
    on_template_selected,
    save_template,
)


def _build_status_bar(root):
    """顶部状态栏。"""
    status_frame = tk.Frame(root, bg="#3a3d5c", height=32)
    status_frame.pack(fill="x")
    status_frame.pack_propagate(False)
    status_icon = tk.Label(status_frame, text="●", bg="#3a3d5c", fg="#5cb85c", font=("Arial", 8))
    status_icon.pack(side="left", padx=(12, 4), pady=4)
    ctx.status_var = tk.StringVar(value="等待操作")
    status_label = tk.Label(
        status_frame, textvariable=ctx.status_var,
        bg="#3a3d5c", fg="#ffffff", font=("微软雅黑", 10), anchor="w"
    )
    status_label.pack(side="left", pady=4, fill="x", expand=True)


def _build_page_send(page1_frame):
    """第1页：发送。"""
    p1_content = tk.Frame(page1_frame, bg=BG_MAIN)
    p1_content.pack(fill="both", expand=True, padx=4, pady=4)
    p1_content.grid_columnconfigure(0, weight=0)
    p1_content.grid_columnconfigure(1, weight=1)
    p1_content.grid_columnconfigure(2, weight=1)
    p1_content.grid_rowconfigure(1, weight=1)

    # ─── 任务控制（第0列）───
    control_card = ttk.LabelFrame(p1_content, text="  任务控制  ", style="Card.TLabelframe", padding=8)
    control_card.grid(row=0, column=0, padx=(0, 6), pady=4, sticky="nsew")

    start_btn = ttk.Button(control_card, text="▶ 开始发送", command=begin, width=12)
    start_btn.grid(row=0, column=0, pady=2, sticky="ew")

    pause_btn = ttk.Button(control_card, text="⏸ 暂停发送", command=pause, width=12)
    pause_btn.grid(row=1, column=0, pady=2, sticky="ew")

    resume_btn = ttk.Button(control_card, text="▶ 继续发送", command=resume, width=12)
    resume_btn.grid(row=2, column=0, pady=2, sticky="ew")

    stop_btn = ttk.Button(control_card, text="⏹ 终止发送", command=stop, width=12)
    stop_btn.grid(row=3, column=0, pady=2, sticky="ew")

    exit_btn = ttk.Button(control_card, text="✕ 退出程序", command=exit_app, width=12)
    exit_btn.grid(row=4, column=0, pady=2, sticky="ew")

    # ─── 基础信息（第1列）───
    left_card = ttk.LabelFrame(p1_content, text="  基础信息  ", style="Card.TLabelframe", padding=8)
    left_card.grid(row=0, column=1, padx=(0, 6), pady=4, sticky="nsew")
    left_card.grid_columnconfigure(1, weight=1)

    tk.Label(left_card, text="日期", bg=BG_CARD, fg=FG_LABEL, font=("微软雅黑", 9)).grid(
        row=0, column=0, sticky="w", padx=(0, 8), pady=4
    )
    ctx.date_entry = ttk.Entry(left_card, width=16)
    ctx.date_entry.grid(row=0, column=1, sticky="ew", pady=4)
    ctx.date_entry.insert(0, f"{time.localtime().tm_mon}.{time.localtime().tm_mday}")

    tk.Label(left_card, text="科目", bg=BG_CARD, fg=FG_LABEL, font=("微软雅黑", 9)).grid(
        row=1, column=0, sticky="w", padx=(0, 8), pady=4
    )
    ctx.subject_var = tk.StringVar()
    ctx.subject_box = ttk.Combobox(
        left_card, textvariable=ctx.subject_var,
        values=["语文", "数学", "英语", "物理", "化学"], width=16
    )
    ctx.subject_box.grid(row=1, column=1, sticky="ew", pady=4)
    ctx.subject_box.current(0)

    tk.Label(left_card, text="间隔(秒)", bg=BG_CARD, fg=FG_LABEL, font=("微软雅黑", 9)).grid(
        row=2, column=0, sticky="w", padx=(0, 8), pady=4
    )
    ctx.interval_entry = ttk.Entry(left_card, width=16)
    ctx.interval_entry.grid(row=2, column=1, sticky="ew", pady=4)
    ctx.interval_entry.insert(0, "1")

    def _save_interval():
        try:
            val = float(ctx.interval_entry.get().strip())
            if val < 0.5:
                raise ValueError
            ctx.last_valid_interval = ctx.interval_entry.get().strip()
            add_log(f"间隔时间已保存：{val}秒")
            update_status(f"间隔时间已保存：{val}秒")
        except Exception:
            ctx.interval_entry.delete(0, "end")
            ctx.interval_entry.insert(0, ctx.last_valid_interval)
            add_log(f"间隔时间不合法，已回退至{ctx.last_valid_interval}", "error")
            update_status(f"间隔时间不合法，已回退至{ctx.last_valid_interval}")

    save_interval_btn = ttk.Button(left_card, text="保存间隔", command=_save_interval, width=8)
    save_interval_btn.grid(row=3, column=1, sticky="e", pady=4)

    # ─── 作业数据（第2列）───
    right_card = ttk.LabelFrame(p1_content, text="  作业数据  ", style="Card.TLabelframe", padding=8)
    right_card.grid(row=0, column=2, padx=(6, 0), pady=4, sticky="nsew")
    right_card.grid_columnconfigure(1, weight=1)

    field_labels = ["提交人数", "提交率", "均分", "最高分", "作业内容", "截止日期"]
    field_keys = ["count", "rate", "avg", "max", "content", "date_dead"]
    ctx.right_entries = {}
    for i, (label, key) in enumerate(zip(field_labels, field_keys)):
        tk.Label(right_card, text=label, bg=BG_CARD, fg=FG_LABEL, font=("微软雅黑", 9)).grid(
            row=i, column=0, sticky="w", padx=(0, 8), pady=4
        )
        entry = ttk.Entry(right_card, width=16)
        entry.grid(row=i, column=1, sticky="ew", pady=4)
        ctx.right_entries[key] = entry

    ctx.count_entry = ctx.right_entries["count"]
    ctx.rate_entry = ctx.right_entries["rate"]
    ctx.avg_entry = ctx.right_entries["avg"]
    ctx.max_entry = ctx.right_entries["max"]
    ctx.content_entry = ctx.right_entries["content"]
    ctx.date_dead_entry = ctx.right_entries["date_dead"]
    ctx.date_dead_entry.insert(0, f"{time.localtime().tm_mon}月{time.localtime().tm_mday + 1}日")

    # ─── 消息预览 ───
    preview_card = ttk.LabelFrame(p1_content, text="  消息预览  ", style="Card.TLabelframe", padding=10)
    preview_card.grid(row=1, column=0, columnspan=3, padx=0, pady=4, sticky="nsew")

    ctx.preview_box = tk.Text(
        preview_card, height=3, width=20,
        font=("微软雅黑", 9), relief="flat", bd=0,
        bg="#f8f9fa", fg="#555", wrap="word"
    )
    ctx.preview_box.pack(fill="both", expand=True)
    ctx.preview_box.config(state="disabled")

    # ─── 发送统计 ───
    stats_card = ttk.LabelFrame(page1_frame, text="  发送统计  ", style="Card.TLabelframe", padding=8)
    stats_card.pack(fill="x", padx=4, pady=(0, 4))

    ctx.recipient_summary_var = tk.StringVar(value="未选择名单")
    ttk.Label(stats_card, textvariable=ctx.recipient_summary_var, wraplength=460,
              style="Card.TLabel").pack(fill="x")

    stats_inner = tk.Frame(stats_card, bg=BG_CARD)
    stats_inner.pack(fill="x")

    ctx.total_var = tk.StringVar(value="总数：0")
    ctx.success_var = tk.StringVar(value="成功：0")
    ctx.unfinished_var = tk.StringVar(value="未完成：0")
    ctx.progress_var = tk.DoubleVar(value=0)

    tk.Label(stats_inner, textvariable=ctx.total_var, bg=BG_CARD, fg=FG_LABEL,
             font=("微软雅黑", 9), width=10).pack(side="left", padx=6, pady=4)
    tk.Label(stats_inner, textvariable=ctx.success_var, bg=BG_CARD, fg=CLR_SUCCESS,
             font=("微软雅黑", 9, "bold"), width=10).pack(side="left", padx=6, pady=4)
    tk.Label(stats_inner, textvariable=ctx.unfinished_var, bg=BG_CARD, fg=CLR_DANGER,
             font=("微软雅黑", 9, "bold"), width=10).pack(side="left", padx=6, pady=4)

    progress_bar = ttk.Progressbar(stats_inner, variable=ctx.progress_var, maximum=100, length=120)
    progress_bar.pack(side="left", fill="x", expand=True, padx=8, pady=4)

    return save_interval_btn


def _build_page_manage(page2_frame):
    """第2页：管理。"""
    p2_content = tk.Frame(page2_frame, bg=BG_MAIN)
    p2_content.pack(fill="both", expand=True, padx=4, pady=4)
    p2_content.grid_columnconfigure(0, weight=0)
    p2_content.grid_columnconfigure(1, weight=1)
    p2_content.grid_rowconfigure(0, weight=0)
    p2_content.grid_rowconfigure(1, weight=1)

    # ─── 文件管理 ───
    file_card = ttk.LabelFrame(p2_content, text="  文件管理  ", style="Card.TLabelframe", padding=8)
    file_card.grid(row=0, column=0, padx=(0, 6), sticky="nsew")

    btn_style_opts = {"width": 12}

    excel_btn = ttk.Button(file_card, text="选择名单 Excel", command=load_excel, **btn_style_opts)
    excel_btn.grid(row=0, column=0, pady=2, sticky="ew")

    text_btn = ttk.Button(file_card, text="文字导入名单", command=load_text_students, **btn_style_opts)
    text_btn.grid(row=1, column=0, pady=2, sticky="ew")

    clear_excel_btn = ttk.Button(file_card, text="取消当前名单", command=clear_students, **btn_style_opts)
    clear_excel_btn.grid(row=2, column=0, pady=2, sticky="ew")

    image_btn = ttk.Button(file_card, text="选择作业图片", command=load_image, **btn_style_opts)
    image_btn.grid(row=3, column=0, pady=2, sticky="ew")

    clear_image_btn = ttk.Button(file_card, text="删除作业图片", command=clear_image, **btn_style_opts)
    clear_image_btn.grid(row=4, column=0, pady=2, sticky="ew")

    template_btn = ttk.Button(file_card, text="加载本地模板", command=load_local_template, **btn_style_opts)
    template_btn.grid(row=5, column=0, pady=2, sticky="ew")

    save_template_btn = ttk.Button(file_card, text="保存当前模板", command=save_template, **btn_style_opts)
    save_template_btn.grid(row=6, column=0, pady=2, sticky="ew")

    # ─── 模板和模板内容 ───
    template_card = ttk.LabelFrame(p2_content, text="  模板编辑  ", style="Card.TLabelframe", padding=8)
    template_card.grid(row=0, column=1, padx=(6, 0), pady=4, sticky="nsew")
    template_card.grid_columnconfigure(1, weight=0)

    load_templates_from_folder()
    add_log(f"启动时加载模板：{len(ctx.template_dict)}个")

    tk.Label(template_card, text="模板", bg=BG_CARD, fg=FG_LABEL, font=("微软雅黑", 9)).grid(
        row=0, column=0, sticky="ew", padx=(0, 8), pady=4
    )
    ctx.template_name_var = tk.StringVar()
    ctx.message_box = ttk.Combobox(
        template_card, textvariable=ctx.template_name_var,
        values=list(ctx.template_dict.keys()), width=30
    )
    ctx.message_box.grid(row=0, column=1, sticky="ew", pady=4)

    tk.Label(template_card, text="模板内容", bg=BG_CARD, fg=FG_LABEL, font=("微软雅黑", 9)).grid(
        row=1, column=0, sticky="nw", padx=(0, 8), pady=4
    )
    ctx.message_text = tk.Text(
        template_card, height=10, width=30,
        font=("微软雅黑", 9), relief="solid", bd=1, bg="#fafafa"
    )
    ctx.message_text.grid(row=1, column=1, sticky="nsew", pady=4)
    template_card.grid_rowconfigure(1, weight=0)

    # ─── 当前状态 ───
    state_card = ttk.LabelFrame(p2_content, text="  当前状态  ", style="Card.TLabelframe", padding=8)
    state_card.grid(row=1, column=0, padx=(0, 6), pady=4, sticky="nsew")

    ctx.student_info_var = tk.StringVar(value="已加载 0 名学生")
    ctx.image_info_var = tk.StringVar(value="未加载图片")

    tk.Label(state_card, textvariable=ctx.student_info_var, bg=BG_CARD, fg=FG_LABEL,
             font=("微软雅黑", 9), wraplength=130, justify="left", anchor="w").pack(fill="x", pady=1)
    ttk.Separator(state_card, orient="horizontal").pack(fill="x", pady=2)
    tk.Label(state_card, textvariable=ctx.image_info_var, bg=BG_CARD, fg=FG_LABEL,
             font=("微软雅黑", 9), wraplength=130, justify="left", anchor="w").pack(fill="x", pady=1)

    # ─── 学生详细名单 ───
    student_card = ttk.LabelFrame(p2_content, text="  名单与本次发送对象  ", style="Card.TLabelframe", padding=8)
    student_card.grid(row=1, column=1, padx=(6, 0), pady=4, sticky="nsew")

    ctx.roster_var = tk.StringVar()
    ctx.roster_box = ttk.Combobox(student_card, textvariable=ctx.roster_var, state="readonly", width=24)
    ctx.roster_box.pack(fill="x", pady=(0, 4))
    ctx.roster_box.bind("<<ComboboxSelected>>", on_roster_selected)

    selection_bar = ttk.Frame(student_card)
    selection_bar.pack(fill="x", pady=(0, 4))
    selection_buttons = {}
    for mode, label in (("all", "全选"), ("none", "全不选"), ("invert", "反选")):
        button = ttk.Button(selection_bar, text=label, width=7,
                            command=lambda choice=mode: set_recipients(choice))
        button.pack(side="left", padx=(0, 4))
        selection_buttons[f"select_{mode}_btn"] = button
    ttk.Label(student_card, text="点击学生切换；☐ 不发送；选择自动保存",
              style="Hint.TLabel", wraplength=320).pack(anchor="w", pady=(0, 4))

    tree_frame = ttk.Frame(student_card)
    tree_frame.pack(fill="both", expand=True)
    ctx.student_tree = ttk.Treeview(tree_frame, columns=("selected", "name", "status"),
                                   show="headings", height=10, selectmode="extended")
    for column, label, width in (("selected", "勾选", 45), ("name", "学生", 120), ("status", "本次", 65)):
        ctx.student_tree.heading(column, text=label)
        ctx.student_tree.column(column, width=width, minwidth=width, stretch=column == "name", anchor="center")
    ctx.student_tree.tag_configure("excluded", foreground="#888888")
    ctx.student_tree.pack(side="left", fill="both", expand=True)
    student_scrollbar = ttk.Scrollbar(tree_frame, command=ctx.student_tree.yview)
    student_scrollbar.pack(side="right", fill="y")
    ctx.student_tree.config(yscrollcommand=student_scrollbar.set)
    ctx.student_tree.bind("<Button-1>", toggle_student)
    ctx.student_tree.bind("<space>", toggle_student)

    save_list_btn = ttk.Button(p2_content, text="编辑并保存名单", command=save_student_list, width=12)
    save_list_btn.grid(row=2, column=1, pady=(4, 0), sticky="ew")

    return {
        **selection_buttons,
        "excel_btn": excel_btn,
        "text_btn": text_btn,
        "clear_excel_btn": clear_excel_btn,
        "image_btn": image_btn,
        "clear_image_btn": clear_image_btn,
        "template_btn": template_btn,
        "save_template_btn": save_template_btn,
        "save_list_btn": save_list_btn,
    }


def _build_page_log(page3_frame):
    """第3页：日志。"""
    log_card = ttk.LabelFrame(page3_frame, text="  运行日志  ", style="Card.TLabelframe", padding=6)
    log_card.pack(fill="both", expand=True, padx=4, pady=4)

    ctx.log_box = tk.Text(
        log_card, height=10, width=20,
        font=("Consolas", 9), relief="flat", bd=0,
        bg="#1e1e2e", fg="#cdd6f4", wrap="word"
    )
    ctx.log_box.pack(side="left", fill="both", expand=True)
    scrollbar = ttk.Scrollbar(log_card, command=ctx.log_box.yview)
    scrollbar.pack(side="right", fill="y")
    ctx.log_box.config(yscrollcommand=scrollbar.set)
    ctx.log_box.tag_config("success", foreground="#a6e3a1")
    ctx.log_box.tag_config("error", foreground="#f38ba8")
    ctx.log_box.tag_config("info", foreground="#89b4fa")


def build_main_window():
    """构建主窗口与全部页面，返回 Tk 根窗口。"""
    root = tk.Tk()
    root.title(APP_TITLE)
    root.minsize(560, 720)
    root.configure(bg=BG_MAIN)
    ctx.root = root

    # ── 样式配置 ──
    style = ttk.Style()
    style.theme_use("clam")

    style.configure("Card.TFrame", background=BG_CARD, relief="flat")
    style.configure("Card.TLabel", background=BG_CARD, foreground=FG_LABEL, font=("微软雅黑", 9))
    style.configure("CardTitle.TLabel", background=BG_CARD, foreground=FG_TITLE, font=("微软雅黑", 10, "bold"))
    style.configure("Hint.TLabel", background=BG_CARD, foreground=FG_HINT, font=("微软雅黑", 8))

    style.configure("Card.TLabelframe", background=BG_CARD, relief="flat", bd=0)
    style.configure("Card.TLabelframe.Label", background=BG_CARD, foreground=FG_TITLE, font=("微软雅黑", 10, "bold"))

    style.configure("Primary.TButton", font=("微软雅黑", 9), padding=6)
    style.configure("Success.TButton", font=("微软雅黑", 9), padding=6)
    style.configure("Danger.TButton", font=("微软雅黑", 9), padding=6)
    style.configure("Warning.TButton", font=("微软雅黑", 9), padding=6)

    style.configure("TCombobox", padding=4)
    style.configure("TEntry", padding=4)

    # ── 顶部状态栏 ──
    _build_status_bar(root)

    # ── Notebook 三页面布局 ──
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=12, pady=8)

    page1_frame = tk.Frame(notebook, bg=BG_MAIN)
    page2_frame = tk.Frame(notebook, bg=BG_MAIN)
    page3_frame = tk.Frame(notebook, bg=BG_MAIN)
    notebook.add(page1_frame, text="  发送  ")
    notebook.add(page2_frame, text="  管理  ")
    notebook.add(page3_frame, text="  日志  ")

    # ═══════════════════════
    # 三个页面
    # ═══════════════════════
    save_interval_btn = _build_page_send(page1_frame)
    manage_buttons = _build_page_manage(page2_frame)
    _build_page_log(page3_frame)

    # 任务运行期间需要锁定的按钮集合
    ctx.lockable_buttons = [*manage_buttons.values(), save_interval_btn]

    # ═══════════════════════
    # 事件绑定
    # ═══════════════════════
    ctx.message_box.bind("<<ComboboxSelected>>", on_template_selected)
    ctx.message_text.bind("<KeyRelease>", update_preview)
    ctx.date_entry.bind("<KeyRelease>", update_preview)
    ctx.subject_box.bind("<<ComboboxSelected>>", update_preview)
    ctx.subject_box.bind("<KeyRelease>", update_preview)
    ctx.count_entry.bind("<KeyRelease>", update_preview)
    ctx.rate_entry.bind("<KeyRelease>", update_preview)
    ctx.avg_entry.bind("<KeyRelease>", update_preview)
    ctx.max_entry.bind("<KeyRelease>", update_preview)
    ctx.content_entry.bind("<KeyRelease>", update_preview)
    ctx.date_dead_entry.bind("<KeyRelease>", update_preview)

    load_config()
    load_saved_rosters()
    root.protocol("WM_DELETE_WINDOW", exit_app)

    update_preview()

    return root
