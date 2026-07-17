import pandas as pd
from tkinter import filedialog
import tkinter as tk
from tkinter import ttk
import threading
import time
import pyautogui
import pyperclip
from PIL import Image
import win32clipboard
import io

# =========================
# 全局变量
# =========================
students = []
message_template = "作业通知：\n日期：{{date}}\n科目：{{subject}}\n请同学们按时完成作业并提交"
image_path = ""
sent_students = []
pause_flag = False
running_flag = False
stop_flag = False
resume_pending = False

# =========================
# 工具函数
# =========================
def paste(text):
    pyperclip.copy(text)
    pyautogui.hotkey('ctrl', 'v')

def send_image(path):
    image = Image.open(path)
    output = io.BytesIO()
    image.convert("RGB").save(output,"BMP")
    data = output.getvalue()[14:]
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB,data)
    win32clipboard.CloseClipboard()
    pyautogui.hotkey("ctrl","v")
    time.sleep(1)
    pyautogui.press("enter")

def render_template(template, data):
    for key, value in data.items():
        template = template.replace(f"{{{{{key}}}}}",str(value))
    return template

def update_preview(*args):
    template = message_var.get().strip()
    date = date_entry.get().strip()
    subject = subject_var.get()
    count = count_entry.get().strip()
    rate = rate_entry.get().strip()
    avg = avg_entry.get().strip()
    max_score = max_entry.get().strip()
    content = content_entry.get().strip()
    date_dead = date_dead_entry.get().strip()
    data = {
        "date": date,
        "subject": subject,
        "count": count,
        "rate": rate,
        "avg": avg,
        "max": max_score,
        "content": content,
        "date_dead": date_dead
    }
    preview = render_template(template,data)
    preview_box.config(state="normal")
    preview_box.delete("1.0","end")
    preview_box.insert("end",preview)
    preview_box.config(state="disabled")

# =========================
# GUI更新
# =========================
def add_log(text,tag="info"):
    root.after(0,lambda:(log_box.insert("end",text + "\n",tag),log_box.see("end")))

def update_status(text):
    root.after(0,lambda:status_label.config(text=text))

# =========================
# 企业微信自动化
# =========================
def process_student(name,current_message):
    global stop_flag,sent_students
    if stop_flag:
        return False
    #搜索群聊
    pyautogui.hotkey('ctrl', 'f')
    time.sleep(0.5)
    paste(name)
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(1)
    #发送文字
    if stop_flag:
        return False
    paste(current_message)
    pyautogui.press('enter')
    time.sleep(1)
    #发送图片
    if image_path:
        if stop_flag:
            return False
        send_image(image_path)
    sent_students.append(name)
    return True

def run_task(current_message):
    global running_flag
    global stop_flag
    running_flag = True
    stop_flag = False
    try:
        sent_students.clear()
        task_students = students.copy()
        update_status("请立刻切换至企业微信窗口...")
        #给用户切换时间
        for i in range(3):
            while pause_flag:
                time.sleep(0.5)
            time.sleep(1)
        update_status("正在发送...")
        add_log("开始发送任务")
        total = len(task_students)
        for index, s in enumerate(task_students):
            while pause_flag:
                time.sleep(0.5)
            if stop_flag:
                update_status("发送任务已终止")
                add_log("发送任务已终止")
                break
            update_status(f"正在发送：({index+1}/{total})")
            add_log(f"正在发送：{s}")
            success = process_student(s,current_message)
            if not success:
                update_status("发送任务已终止")
                add_log("发送任务已终止")
                break
            add_log(f"{s} 发送完成","success")
            time.sleep(1)
        # 完成后显示结果
        update_status("发送完成")
        add_log("|发送完成","success")
        add_log("+---------------+")
        add_log("|发送名单：")
        for name in sent_students:
            add_log("|" +name)
        add_log("+---------------+")
    except Exception as e:
        add_log(f"错误：{e}","error")
        update_status("程序异常结束")
    finally:
        running_flag = False

# =========================
# 文件读取
# =========================
def load_excel():
    global students
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    if file_path:
        df = pd.read_excel(file_path)
        # 当前选择的科目
        subject = subject_var.get()
        # 读取该科目这一列
        if subject in df.columns:
            students = (df[subject].dropna().tolist())
            add_log(f"{subject}：已读取 {len(students)} 名学生")
            update_status(f"{subject}名单已加载")
        else:
            add_log(f"Excel中没有找到{subject}")

def load_image():
    global image_path
    path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
    if path:
        image_path = path
        add_log(f"已选择图片：{path.split('/')[-1]}")
        update_status("图片已加载")

def clear_students():
    global students
    students.clear()
    add_log("学生名单已清空")
    update_status("学生名单已清空")

def clear_image():
    global image_path
    image_path = ""
    add_log("作业图片已删除")
    update_status("作业图片已删除")

# =========================
# 开始按钮
# =========================
def pause():
    global pause_flag
    global resume_pending
    if not running_flag:
        update_status("当前没有发送任务")
        add_log("无法暂停：没有正在进行的任务","error")
        return
    pause_flag = True
    resume_pending = False
    update_status("已暂停发送")
    add_log("已暂停发送")

def resume():
    global resume_pending
    if resume_pending:
        return
    if not running_flag:
        update_status("当前没有发送任务")
        add_log("无法继续：没有正在进行的任务","error")
        return
    resume_pending = True
    update_status("即将恢复发送，请立刻切换至企业微信窗口")
    root.after(3000,continue_send)

def continue_send():
    global pause_flag
    global resume_pending
    if not resume_pending:
        return
    pause_flag = False
    update_status("继续发送")
    add_log("恢复发送")

def start():
    global running_flag
    global pause_flag
    global stop_flag
    subject = subject_var.get()
    date = date_entry.get()
    count = count_entry.get()
    rate = rate_entry.get()
    avg = avg_entry.get()
    max_score = max_entry.get()
    content = content_entry.get()
    date_dead = date_dead_entry.get()
    template = message_var.get().strip()
    data = {
        "date": date,
        "subject": subject,
        "count": count,
        "rate": rate,
        "avg": avg,
        "max": max_score,
        "content": content,
        "date_dead": date_dead
    }
    current_message = render_template(template,data)
    if len(students) == 0:
        update_status("请先读取学生名单")
        return
    if not template:
        update_status("请输入或选择发送模板")
        return
    # 防止重复启动
    if running_flag:
        update_status("任务正在运行，请勿重复发送")
        add_log("启动失败：有正在运行的任务","error")
        return
    pause_flag = False
    stop_flag = False
    running_flag = True
    # 用线程防止界面卡死
    threading.Thread(target=run_task,args=(current_message,)).start()

def stop():
    global stop_flag
    global pause_flag
    global resume_pending
    if not running_flag:
        update_status("当前没有发送任务")
        add_log("终止失败：没有正在运行的任务","error")
        return
    stop_flag = True
    pause_flag = False
    resume_pending = False
    update_status("正在终止...")
    add_log("收到终止请求")

def exit_app():
    global stop_flag
    stop_flag=True
    add_log("正在退出程序")
    root.after(500,root.destroy)

# =========================
# GUI
# =========================
root = tk.Tk()
root.title("自动发送反馈工具")
root.minsize(600, 400)

# 左右容器
main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True)
left_frame = tk.LabelFrame(main_frame, text="基础信息")
right_frame = tk.LabelFrame(main_frame, text="作业数据")
left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="n")
right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="n")
left_frame.grid_columnconfigure(1, weight=1)
right_frame.grid_columnconfigure(1, weight=1)
main_frame.grid_columnconfigure(0, weight=1)
main_frame.grid_columnconfigure(1, weight=1)

# 当前状态
status_label = tk.Label(root,text="当前状态：等待操作",font=("微软雅黑",12))
status_label.pack(pady=10)

# 科目选择
tk.Label(left_frame, text="科目").grid(row=1, column=0, sticky="w",padx=5,pady=3)
subject_var = tk.StringVar()
subject_box = ttk.Combobox(left_frame,textvariable=subject_var,values=["语文","数学","英语","物理","化学"])
subject_box.grid(row=1,column=1,sticky="ew",padx=5,pady=3)
subject_box.current(0)
# 日期
tk.Label(left_frame, text="日期").grid(row=0, column=0, sticky="w",padx=5,pady=3)
date_entry = tk.Entry(left_frame)
date_entry.grid(row=0, column=1,sticky="ew",padx=5,pady=3)
date_entry.insert(0,f"{time.localtime().tm_mon}.{time.localtime().tm_mday}")
# 提交人数
tk.Label(right_frame, text="提交人数").grid(row=0, column=0, sticky="w",padx=5,pady=3)
count_entry = tk.Entry(right_frame)
count_entry.grid(row=0, column=1,sticky="ew",padx=5,pady=3)
# 提交率
tk.Label(right_frame, text="提交率").grid(row=1, column=0, sticky="w",padx=5,pady=3)
rate_entry = tk.Entry(right_frame)
rate_entry.grid(row=1, column=1,sticky="ew",padx=5,pady=3)
# 均分
tk.Label(right_frame, text="均分").grid(row=2, column=0, sticky="w",padx=5,pady=3)
avg_entry = tk.Entry(right_frame)
avg_entry.grid(row=2, column=1,sticky="ew",padx=5,pady=3)
# 最高分
tk.Label(right_frame, text="最高分").grid(row=3, column=0, sticky="w",padx=5,pady=3)
max_entry = tk.Entry(right_frame)
max_entry.grid(row=3, column=1,sticky="ew",padx=5,pady=3)
# 作业内容
tk.Label(right_frame, text="作业内容").grid(row=4,column=0,sticky="w",padx=5,pady=3)
content_entry = tk.Entry(right_frame)
content_entry.grid(row=4,column=1,sticky="ew",padx=5,pady=3)
# 截止日期
tk.Label(right_frame, text="截止日期").grid(row=5,column=0,sticky="w",padx=5,pady=3)
date_dead_entry = tk.Entry(right_frame)
date_dead_entry.grid(row=5,column=1,sticky="ew",padx=5,pady=3)
date_dead_entry.insert(0,f"{time.localtime().tm_mon}月{time.localtime().tm_mday+1}日")
# 消息输入
tk.Label(left_frame, text="选择或输入模板").grid(row=2, column=0, sticky="w",padx=5,pady=3)
template_list = [
    "请输入",
    "{{date}}新高一四校班{{subject}}作业今晚18：00就要截止了哦，classin后台检测到小同学还未提交作业，请尽快提交～",
    "{{date}}新高一【四校班{{subject}}】作业情况反馈来啦：\n"
    "📄班级上交与得分情况\n"
    "全班共收到{{count}}份作业，提交率{{rate}}%\n"
    "均分：{{avg}}\n最高分：{{max}}\n"
    "📖 总分如图所示，没有名字的小同学就是没有提交作业哦！有的小同学classin还没有改名字\n"
    "💥同学可以在classin上查看自己的作业批改情况～\n"
    "没有提交作业的小同学一定要记得补交作业，补交后在群内@老师，我会及时批改的！交完后再看答案～这样学习效果会更好，期待你有更大的进步！",
    "{{date}}【新高一四校班{{subject}}】\n"
    "同学未带手机，已经进入教室上课了",
    "{{date}}【新高一四校班{{subject}}】\n"
    "作业👇\n🔶作业内容：{{content}}\n"
    "🔶作业提交方式：classin班级群-作业-拍照提交\n"
    "🔺作业截止时间：{{date_dead}}18：00\n"
    "作业截止时间过后，作业反馈前答案会发布在classin班级群，小同学一定要准时提交作业到classin～"
]
message_var = tk.StringVar()
message_box = ttk.Combobox(left_frame, textvariable=message_var, values=template_list)
message_box.grid(row=2,column=1,sticky="ew",padx=5,pady=3)
message_box.current(1)

# 预览
preview_box = tk.Text(main_frame, height=8)
preview_box.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

# =========================
# 按钮区域
# =========================
button_frame = tk.Frame(root)
button_frame.pack(pady=10)
file_frame = tk.LabelFrame(button_frame,text="文件管理")
control_frame = tk.LabelFrame(button_frame,text="任务控制")
file_frame.grid(row=0,column=0,padx=10)
control_frame.grid(row=0,column=1,padx=10)

# 文件按钮
excel_btn = tk.Button(file_frame,text="选择学生名单Excel",command=load_excel,width=20)
excel_btn.grid(row=0,column=0,padx=5,pady=5)
clear_excel_btn = tk.Button(file_frame,text="删除学生名单",command=clear_students,width=20)
clear_excel_btn.grid(row=1,column=0,padx=5,pady=5)

image_btn = tk.Button(file_frame,text="选择作业情况图片",command=load_image,width=20)
image_btn.grid(row=2,column=0,padx=5,pady=5)
clear_image_btn = tk.Button(file_frame,text="删除作业图片",command=clear_image,width=20)
clear_image_btn.grid(row=3,column=0,padx=5,pady=5)

# 发送按钮
btn = tk.Button(control_frame,text="开始发送",command=start,width=20)
btn.grid(row=0,column=0,padx=5,pady=5)

stop_btn = tk.Button(control_frame,text="终止发送",command=stop,width=20)
stop_btn.grid(row=1,column=0,padx=5,pady=5)

pause_btn = tk.Button(control_frame,text="暂停发送",command=pause,width=20)
pause_btn.grid(row=2,column=0,padx=5,pady=5)

resume_btn = tk.Button(control_frame,text="继续发送",command=resume,width=20)
resume_btn.grid(row=3,column=0,padx=5,pady=5)

# 日志
log_label = tk.Label(root,text="发送日志")
log_label.pack()
log_frame = tk.Frame(root)
log_frame.pack(pady=5,fill="both",expand=True)
scrollbar = tk.Scrollbar(log_frame)
log_box = tk.Text(log_frame,height=10,width=60,yscrollcommand=scrollbar.set)
scrollbar.config(command=log_box.yview)
log_box.pack(side="left",fill="both",expand=True)
scrollbar.pack(side="right",fill="y")

log_box.tag_config("success", foreground="green")
log_box.tag_config("error", foreground="red")
log_box.tag_config("info", foreground="blue")

# 退出
exit_btn = tk.Button(control_frame,text="退出程序",command=exit_app,width=20)
exit_btn.grid(row=4,column=0,padx=5,pady=5)

# 模板变化（选择 or 手动输入）
message_box.bind("<<ComboboxSelected>>", update_preview)
message_box.bind("<KeyRelease>", update_preview)

# 实时变化更新
date_entry.bind("<KeyRelease>", update_preview)
subject_box.bind("<<ComboboxSelected>>", update_preview)
count_entry.bind("<KeyRelease>", update_preview)
rate_entry.bind("<KeyRelease>", update_preview)
avg_entry.bind("<KeyRelease>", update_preview)
max_entry.bind("<KeyRelease>", update_preview)
content_entry.bind("<KeyRelease>", update_preview)
date_dead_entry.bind("<KeyRelease>", update_preview)

update_preview()

root.mainloop()