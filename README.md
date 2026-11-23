# WXwork_AutoSendMessage_Tool

## v1.6.0：持久名单与发送对象选择（2026-10-30）

本版本由 v1.5.2 升级。开发入口是 `main.py`；打包后的入口为 `dist/WXwork_AutoSendMessage_Tool.exe`。

1. 在「发送」页选择科目，再到「管理」页点击「选择名单 Excel」。沿用原有格式：读取活动工作表，第一行须包含与当前科目同名的列，下面填写学生姓名。
2. 每个 Excel / 科目组合会自动保存为一份 JSON 名单。相同路径和科目再次导入会更新原名单，并保留仍在名单内的「不发送」标记；不同路径的同名文件独立保存。姓名会去除空白并去重，单字姓名沿用旧版追加「同学」的规则。
3. 在「管理」页的名单下拉框切换名单。点击学生即可勾选或取消勾选，也可使用「全选」「全不选」「反选」。`☑` 表示本次发送，`☐` 和灰字「不发送」表示本次排除，学生仍保留在原名单中。选择即时保存，重启后自动读取所有 JSON，恢复上次使用的名单和选择。
4. 「发送」页会显示当前名单与本次人数。发送与暂停后继续只处理本次勾选的学生；全部取消勾选时不能启动。任务运行或暂停期间禁止切换名单、修改选择。
5. 「编辑并保存名单」可修改姓名：弹窗中「保存到当前名单」更新当前 JSON；「另存为新名单」输入新名称后生成独立 JSON，保留原名单并自动切换到新名单。新名单继承仍在名单内的「不发送」标记，新添加的学生默认勾选。同科目重名、取消命名或保存失败均不会覆盖原名单。新名单独立保存，重新导入原 Excel 只更新原导入名单。「文字导入名单」也支持命名后持久保存。「取消当前名单」只解除当前选择，已保存的名单仍保留在下拉框中。

名单保存在程序所在目录的 `rosters/` 中，每份 JSON 包含名单名称、科目、Excel 来源路径、完整学生名单和 `excluded_students`（不发送的学生）。JSON 使用 UTF-8；保存采用先写临时文件再替换的方式。无法读取的名单会跳过并显示日志，不影响其他名单加载。该目录含个人信息，已加入 `.gitignore`。

源码运行时，`config.json`、`templates/` 和 `rosters/` 位于本目录；运行 exe 时位于 exe 所在目录。两种入口的数据位置相互独立。迁移电脑或升级时，应一起复制需要保留的这三个项目。关闭窗口或点击「退出程序」均会保存配置。

开发运行：安装 `requirements.txt` 后执行 `python main.py`。Windows 打包：执行 `build.bat`（需要已安装 Python；自动创建虚拟环境、安装依赖和 PyInstaller）。验证：执行 `python -m unittest discover -s tests -v`；测试使用临时名单和模拟发送，不向企业微信发送消息。

编辑名单弹窗默认尺寸为 460×360，最小高度为 220；文本区随窗口伸缩，底部保存、另存和取消按钮保持可见。最小宽度会根据按钮所需宽度调整，以适应显示缩放。

## Project desciption

This project can enable users to send messages in and only in WXwork quickly and automatically, which improve working efficiency.

With this tool, you can send message and pictures to all receivers in the name list, just type what you want to send at first!

We also provide several templates for you, and new updates with load and save templates functions is available in versions newer than v1.2.0.

All you need to do, is to open the software, type the message, and press the button!

## Update log

- Date 2026-07-17

The exe file named WXwork_AutoSendMessage_Tool v0.7.0 is the first version, it isn't perfect now, but new updates will be uploaded later.

- Date 2026-07-18

New features are added, just download the exe file to use it.

- Date 2026-07-23

We now allow you to load name list from word input. If you want to send slower or faster, we allow you to adjust the interval time between actions now.

- Date 2026-07-24

Now you can create and update your owner tailored templates!

Create a txt file, edit the template and save it to a template file (for example, new.template), then you can load the template each time you want, rather than type the template each time.

Also, you can copy the template file into the archive named template, so that the software will load your template automatically.

For detailed instruction, follow the content in the example.txt.

- Date 2026-07-25

We've improved the view for sending status and the list of receivers finished sending and unfinished sending.

- Date 2026-08-05

We are exicited to claim that, we've redesigned the UI radically. Now there are three pages in the software, responsible for different functions.

The design stems from the desire that, we want to make the software smaller in size, so users can put it beside WXwork to check anytime.

- Date 2026-08-05

We've fixed a bug in v1.5.2. And now we push our code to the main branch. The following is instruction.

If you want to get the software conveniently, just go to the release to get the latest version, and put the exe with templates\ in the same folder.

If you want to study and run the python code, you can do like:

Run the file 'main.py' to run the software (if you've already had a .venv environment).

Run the file 'build.bat' to package the python file into one exe file.
