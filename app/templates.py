"""消息模板管理：模板目录加载、选择、保存与本地文件导入。"""

import os
from tkinter import filedialog

from .constants import SUPPORTED_TEMPLATE_EXTS, TEMPLATE_DIR
from .context import add_log, ctx, update_preview, update_status


def load_templates_from_folder():
    """扫描 templates 目录，把所有模板加载进 ctx.template_dict。"""
    ctx.template_dict = {}
    if not os.path.exists(TEMPLATE_DIR):
        os.makedirs(TEMPLATE_DIR)
        return
    for filename in os.listdir(TEMPLATE_DIR):
        if not filename.lower().endswith(SUPPORTED_TEMPLATE_EXTS):
            continue
        filepath = os.path.join(TEMPLATE_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
            template_name = os.path.splitext(filename)[0]
            ctx.template_dict[template_name] = content
        except Exception as e:
            add_log(f"加载模板失败：{filename} {e}", "error")


def on_template_selected(event=None):
    template_name = ctx.template_name_var.get()
    if template_name not in ctx.template_dict:
        return
    ctx.message_text.delete("1.0", "end")
    ctx.message_text.insert("1.0", ctx.template_dict[template_name])
    update_preview()


def save_template():
    content = ctx.message_text.get("1.0", "end-1c").strip()
    if not content:
        add_log("模板内容为空，无法保存", "error")
        update_status("模板内容为空")
        return
    name = ctx.template_name_var.get().strip()
    if not name:
        add_log("未填写模板名称，无法保存", "error")
        update_status("请先在模板下拉框中输入名称")
        return
    if not os.path.exists(TEMPLATE_DIR):
        os.makedirs(TEMPLATE_DIR)
    filepath = os.path.join(TEMPLATE_DIR, f"{name}.template")
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        ctx.template_dict[name] = content
        current_values = list(ctx.message_box["values"])
        if name not in current_values:
            current_values.append(name)
            ctx.message_box["values"] = current_values
        add_log(f"模板已保存：{name}")
        update_status(f"模板「{name}」已保存")
    except Exception as e:
        add_log(f"保存模板失败：{e}", "error")
        update_status("保存模板失败")


def load_local_template():
    patterns = " ".join(f"*{ext}" for ext in SUPPORTED_TEMPLATE_EXTS)
    template_filetypes = [("Template Files", patterns), ("All files", "*.*")]
    file_path = filedialog.askopenfilename(filetypes=template_filetypes)
    if not file_path:
        return
    encodings = ["utf-8", "utf-8-sig", "gbk"]
    content = None
    last_error = None
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()
            break
        except Exception as e:
            last_error = e
    if content is None:
        add_log(f"模板读取失败：{last_error}", "error")
        update_status("模板读取失败")
        return
    content = content.strip()
    if not content:
        add_log("模板文件为空", "error")
        update_status("模板文件为空")
        return
    # [BUG FIX] tk.Text 没有 .set() 方法，应使用 delete + insert
    ctx.message_text.delete("1.0", "end")
    ctx.message_text.insert("1.0", content)
    # [BUG FIX] 应将模板名（而非内容）加入 combobox
    template_name = os.path.splitext(os.path.basename(file_path))[0]
    current_values = list(ctx.message_box["values"])
    if template_name not in current_values:
        current_values.append(template_name)
        ctx.message_box["values"] = current_values
    ctx.template_dict[template_name] = content
    ctx.template_name_var.set(template_name)
    update_preview()
    add_log(f"已加载本地模板：{os.path.basename(file_path)}")
    update_status("本地模板已加载")
