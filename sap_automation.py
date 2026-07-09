# -*- coding: utf-8 -*-
'''
在断点续连的基础上，新增功能：支持用户选择需要截图的内容
比如第一次选择123进行截图，代码发生中断结束后，再执行该代码，还选择123，则会触发断点续连；若在第二次选择时，勾选456，则不会触发断点续连
'''




import pyautogui
import time
import os
import json
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox
#import win32gui

# ==================== 用户自定义日期参数 ====================
# 全局变量，由 input_dates() 弹窗赋值，供各步骤函数中的 pyautogui.typewrite() 调用
AUDIT_START_DATE = "2025.01.01"   # 审计期间开始日期
AUDIT_END_DATE = "2025.09.30"     # 审计期间结束日期
FISCAL_YEAR = "2025"              # 会计年度
COMPANY_CODE = "1010"             # 公司代码

# ==================== 等待时间配置 ====================
# 可通过 input_dates() 弹窗自定义，单位：秒
SLEEP_LOAD = 5.0       # T-code画面加载等待
SLEEP_QUERY = 10.0     # F8查询执行等待
SLEEP_EXPORT = 13.0    # 导出对话框等待
SLEEP_LONG = 20.0      # 超长等待(大数据量查询)

# ==================== 断点续连状态管理 ====================
STATE_FILENAME = ".sap_automation_state.json"

def get_state_file_path(save_path):
    """状态文件保存在截图目录下，与具体项目关联"""
    return os.path.join(save_path, STATE_FILENAME)

def save_progress(save_path, step_index, step_name, sub_step=None, status="running"):
    """保存执行进度到JSON文件"""
    state = {
        "step_index": step_index,
        "step_name": step_name,
        "sub_step": sub_step,
        "status": status,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    state_file = get_state_file_path(save_path)
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def load_progress(save_path):
    """读取上次执行进度，如果不存在返回None"""
    state_file = get_state_file_path(save_path)
    if os.path.exists(state_file):
        with open(state_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def clear_progress(save_path):
    """清除进度文件（全部成功完成后调用）"""
    state_file = get_state_file_path(save_path)
    if os.path.exists(state_file):
        os.remove(state_file)

def ask_resume(step_name, sub_step=None):
    """弹出对话框询问是否从断点继续执行"""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    sub_info = f"（子步骤：{sub_step}）" if sub_step else ""
    result = messagebox.askyesno(
        "断点续连",
        f"检测到上次执行在步骤【{step_name}】{sub_info}中断。\n\n"
        f"是否从该断点继续执行？\n\n"
        f"点击【是】将从断点继续；\n"
        f"点击【否】将从头开始执行。"
    )
    root.destroy()
    return result

def should_skip_sub_step(state, func_name, sub_step, sub_steps_order):
    """判断当前子步骤是否应该跳过（因为上次已完成）"""
    if not state or state.get("step_name") != func_name:
        return False
    resume_sub = state.get("sub_step")
    if resume_sub is None:
        return False
    try:
        current_idx = sub_steps_order.index(sub_step)
        resume_idx = sub_steps_order.index(resume_sub)
        return current_idx < resume_idx
    except ValueError:
        return False

def mark_sub_step_done(save_path, func_name, sub_step, sub_steps_order):
    """标记子步骤已完成，自动保存下一个子步骤到状态文件"""
    state = load_progress(save_path)
    if not state or state.get("step_name") != func_name:
        return
    try:
        idx = sub_steps_order.index(sub_step)
        next_sub = sub_steps_order[idx + 1] if idx + 1 < len(sub_steps_order) else None
        save_progress(save_path, state["step_index"], func_name, sub_step=next_sub, status="running")
    except ValueError:
        pass

# =========================================================


def ClickMouse_UP():
    #获取屏幕大小并用鼠标点击指定点位
    screen_size = pyautogui.size()
    width_origin = screen_size[0]
    height_origin = screen_size[1]
    width_filter = int(0.25*width_origin)
    height_filter = int(0.25*height_origin)
    pyautogui.click(width_filter, height_filter)


def ClickMouse_DOWN():
    #获取屏幕大小并用鼠标点击指定点位
    screen_size = pyautogui.size()
    width_origin = screen_size[0]
    height_origin = screen_size[1]
    width_filter = int(0.75*width_origin)
    height_filter = int(0.75*height_origin)
    pyautogui.click(width_filter, height_filter)


def select_save_path():
    """弹出窗口选择截图/文件保存路径"""
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    root.attributes('-topmost', True)  # 窗口置顶
    
    # 弹出路径选择对话框
    save_path = filedialog.askdirectory(title="请选择截图和文件的保存文件夹")
    
    if not save_path:
        messagebox.showerror("错误", "未选择保存路径，程序退出！")
        exit()
    
    # 自动创建路径（不存在则创建）
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    
    messagebox.showinfo("路径设置成功", f"文件将保存至：\n{save_path}\n\n点击确定后，3秒开始执行自动化！")
    root.destroy()
    return save_path




def clear_input():
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.3)
    pyautogui.press('backspace')
    time.sleep(0.3)
    # 额外保险：多按几次backspace确保清空
    for _ in range(5):
        pyautogui.press('delete')
        time.sleep(0.1)





def show_input_reminder():
    """弹出提醒：切换输入法为英文大写"""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    messagebox.showwarning(
        "重要提醒",
        "请提前将输入法切换为：【英文 大写模式】\n\n"
        "否则会导致输入错误、程序执行失败！\n\n"
        "确认切换完成后，点击【确定】继续。"
    )
    root.destroy()


def input_dates():
    """弹出窗口让用户自定义输入审计期间日期和会计年度"""
    global AUDIT_START_DATE, AUDIT_END_DATE, FISCAL_YEAR, COMPANY_CODE

    root = tk.Tk()
    root.title("日期参数设置")
    root.attributes('-topmost', True)

    # 计算窗口居中
    win_w, win_h = 560, 520
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = (screen_w - win_w) // 2
    y = (screen_h - win_h) // 2
    root.geometry(f"{win_w}x{win_h}+{x}+{y}")
    root.resizable(False, False)

    # 格式提醒（红色醒目）
    tk.Label(root, text="⚠ 日期格式：YYYY.MM.DD（如 2025.01.01），会计年度：YYYY（如 2025）",
             font=("微软雅黑", 9), fg="red").pack(pady=(15, 5))

    # 提示标签
    tk.Label(root, text="请输入审计期间日期与会计年度：",
             font=("微软雅黑", 11)).pack(pady=(0, 10))

    # 审计开始日期
    frame1 = tk.Frame(root)
    frame1.pack(pady=5)
    tk.Label(frame1, text="审计开始日期：", font=("微软雅黑", 10), width=14, anchor="e").pack(side="left")
    var_start = tk.StringVar()
    entry_start = tk.Entry(frame1, textvariable=var_start, font=("微软雅黑", 10), width=18, justify="center")
    entry_start.pack(side="left", padx=5)

    # 审计结束日期
    frame2 = tk.Frame(root)
    frame2.pack(pady=5)
    tk.Label(frame2, text="审计结束日期：", font=("微软雅黑", 10), width=14, anchor="e").pack(side="left")
    var_end = tk.StringVar()
    entry_end = tk.Entry(frame2, textvariable=var_end, font=("微软雅黑", 10), width=18, justify="center")
    entry_end.pack(side="left", padx=5)

    # 会计年度
    frame3 = tk.Frame(root)
    frame3.pack(pady=5)
    tk.Label(frame3, text="会计年度：", font=("微软雅黑", 10), width=14, anchor="e").pack(side="left")
    var_year = tk.StringVar()
    entry_year = tk.Entry(frame3, textvariable=var_year, font=("微软雅黑", 10), width=18, justify="center")
    entry_year.pack(side="left", padx=5)

    # 公司代码
    frame4 = tk.Frame(root)
    frame4.pack(pady=5)
    tk.Label(frame4, text="公司代码：", font=("微软雅黑", 10), width=14, anchor="e").pack(side="left")
    var_company = tk.StringVar()
    entry_company = tk.Entry(frame4, textvariable=var_company, font=("微软雅黑", 10), width=18, justify="center")
    entry_company.pack(side="left", padx=5)

    # 等待时间配置
    tk.Label(root, text="等待时间配置（秒，默认值即可，需要时调整）：",
             font=("微软雅黑", 9), fg="blue").pack(pady=(10, 5))

    sleep_frame = tk.Frame(root)
    sleep_frame.pack(pady=2)
    sleep_vars = {}
    for label_text, var_name, default_val in [
        ("画面加载等待：", "SLEEP_LOAD", "5.0"),
        ("查询执行等待：", "SLEEP_QUERY", "10.0"),
        ("导出对话框等待：", "SLEEP_EXPORT", "13.0"),
        ("超长等待：", "SLEEP_LONG", "20.0"),
    ]:
        row = tk.Frame(sleep_frame)
        row.pack(pady=1)
        tk.Label(row, text=label_text, font=("微软雅黑", 9), width=16, anchor="e").pack(side="left")
        sv = tk.StringVar(value=default_val)
        sleep_vars[var_name] = sv
        tk.Entry(row, textvariable=sv, font=("微软雅黑", 9), width=8, justify="center").pack(side="left", padx=3)
        tk.Label(row, text="秒", font=("微软雅黑", 9)).pack(side="left")

    def on_confirm():
        global AUDIT_START_DATE, AUDIT_END_DATE, FISCAL_YEAR, COMPANY_CODE
        global SLEEP_LOAD, SLEEP_QUERY, SLEEP_EXPORT, SLEEP_LONG
        start_val = var_start.get().strip()
        end_val = var_end.get().strip()
        year_val = var_year.get().strip()
        company_val = var_company.get().strip()

        if not start_val or not end_val or not year_val or not company_val:
            messagebox.showwarning("提示", "所有字段均为必填，请完善后再确认！", parent=root)
            return

        AUDIT_START_DATE = start_val
        AUDIT_END_DATE = end_val
        FISCAL_YEAR = year_val
        COMPANY_CODE = company_val

        # 保存等待时间配置
        try:
            SLEEP_LOAD = float(sleep_vars["SLEEP_LOAD"].get().strip())
            SLEEP_QUERY = float(sleep_vars["SLEEP_QUERY"].get().strip())
            SLEEP_EXPORT = float(sleep_vars["SLEEP_EXPORT"].get().strip())
            SLEEP_LONG = float(sleep_vars["SLEEP_LONG"].get().strip())
        except:
            pass

        root.quit()
        root.destroy()

    def on_close():
        messagebox.showinfo("程序退出", "日期参数未设置，程序即将退出。")
        root.quit()
        root.destroy()
        exit()

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=(10, 10))
    tk.Button(btn_frame, text="确认", command=on_confirm,
              font=("微软雅黑", 10), width=14, bg="#4CAF50", fg="white").pack(side="left", padx=8)

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.focus_force()
    root.mainloop()

    print(f"[日期参数] 审计开始日期：{AUDIT_START_DATE}，审计结束日期：{AUDIT_END_DATE}，会计年度：{FISCAL_YEAR}，公司代码：{COMPANY_CODE}")
    print(f"[等待时间] 加载={SLEEP_LOAD}s 查询={SLEEP_QUERY}s 导出={SLEEP_EXPORT}s 超长={SLEEP_LONG}s")


def GetExcel_shortcutKey_1():
    pyautogui.hotkey('ctrl', 'shift', 'F9')
    time.sleep(SLEEP_EXPORT)
    pyautogui.press('down')
    time.sleep(1)
    pyautogui.press('down')
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(SLEEP_EXPORT)
    # 点击对话框中间确保文件名输入框获得焦点
    screen_w, screen_h = pyautogui.size()
    pyautogui.click(screen_w // 2, screen_h // 2)
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.5)
    pyautogui.press('backspace')
    time.sleep(0.3)




def GetExcel_shortcutKey_2():
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(SLEEP_EXPORT)
    pyautogui.press('tab')
    time.sleep(1)
    pyautogui.press('tab')
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(SLEEP_EXPORT)
    pyautogui.press('left')
    time.sleep(2)
    pyautogui.press('enter')
    time.sleep(SLEEP_EXPORT)
    pyautogui.press('enter')
    time.sleep(3)




def GetExcel_pc_1():
    pyautogui.typewrite('%PC')
    time.sleep(13)
    pyautogui.press('enter')
    time.sleep(SLEEP_EXPORT)
    pyautogui.press('down')
    time.sleep(1)
    pyautogui.press('down')
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(SLEEP_EXPORT)
    # 点击对话框中间确保文件名输入框获得焦点
    screen_w, screen_h = pyautogui.size()
    pyautogui.click(screen_w // 2, screen_h // 2)
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.5)
    pyautogui.press('backspace')
    time.sleep(0.3)


def GetExcel_pc_2():
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(SLEEP_EXPORT)
    pyautogui.press('tab')
    time.sleep(1)
    pyautogui.press('tab')
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(SLEEP_EXPORT)
    pyautogui.press('left')
    time.sleep(2)
    pyautogui.press('enter')
    time.sleep(SLEEP_EXPORT)
    pyautogui.press('enter')
    time.sleep(3)




def Getbasis_1_T000(save_path):
    setup_pyautogui()
    #登录至菜单
    time.sleep(1)
    pyautogui.hotkey('ctrl', '/')
    for i in range(3):
        pyautogui.press('esc')
        time.sleep(0.5)
    time.sleep(1)
    pyautogui.typewrite('/nSE16')
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(5)

    #截图TDDAT
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(1)
    pyautogui.typewrite('TDDAT')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path,'basis_1_TDDAT.png'))
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(2)
    #截图T000
    pyautogui.typewrite('T000')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path,'basis_1_T000.png')) #根据前台获取的保存路径保存
    pyautogui.hotkey('F8')
    time.sleep(3)
    
    #截图basis_1_权限组值
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path,'basis_1_权限组值.png')) #根据前台获取的保存路径保存

    #返回
    for i in range(3):
        pyautogui.press('F3')
        time.sleep(1)



def Getbasis_1_table_a(save_path):
    setup_pyautogui()
    time.sleep(1)
    #SUIM-用户-按复杂选择条件选择的用户-按权限值
    for i in range(3):
        pyautogui.press('esc')
        time.sleep(0.5)
    time.sleep(1)
    pyautogui.hotkey('ctrl', '/')
    pyautogui.typewrite('/nS_BCE_68001397')
    time.sleep(1.0)
    pyautogui.press('enter')
    time.sleep(5)
    #按复杂选择条件选择的权限
    pyautogui.typewrite('S_TCODE')
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(5)
    pyautogui.press('tab')
    time.sleep(1)
    pyautogui.typewrite('SCC4')
    time.sleep(1)
    pyautogui.press('tab')
    pyautogui.press('tab')
    pyautogui.press('tab')
    pyautogui.press('tab')
    time.sleep(2)
    pyautogui.typewrite('S_TABU_CLI')
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(5)
    pyautogui.press('tab')
    pyautogui.typewrite('X')
    time.sleep(1)
    pyautogui.press('tab')
    pyautogui.press('tab')
    pyautogui.press('tab')
    pyautogui.press('tab')
    time.sleep(1)
    pyautogui.typewrite('S_TABU_DIS')   
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(SLEEP_EXPORT)
    pyautogui.press('tab')
    time.sleep(2)
    pyautogui.typewrite('SS')
    time.sleep(1)
    pyautogui.press('tab')
    pyautogui.press('tab')
    pyautogui.press('tab')
    pyautogui.press('tab')
    time.sleep(1)
    pyautogui.typewrite('02')
    time.sleep(1)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path,'basis_1_scc4_查看权限_a.png')) #根据前台获取的保存路径保存
    pyautogui.hotkey('F8')
    time.sleep(5)
    ClickMouse_UP()

    #截图表a筛选条件
    pyautogui.press('pageup')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path,'basis_1_1.a查询结果1.png')) 
    pyautogui.press('pagedown')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path,'basis_1_1.a查询结果2.png'))

    #完整性截图
    ClickMouse_DOWN()
    pyautogui.hotkey('ctrl', 'shift', 'down')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_1_1.a查询结果3.png'))

    #导出表a
    GetExcel_shortcutKey_1()
    pyautogui.typewrite('basis_1_1_a')
    GetExcel_shortcutKey_2()
    for i in range(2):
        pyautogui.press('F3')
        time.sleep(1)
    

def Getbasis_1_table_b(save_path):
     setup_pyautogui()
     #SUIM-权限-按值
     # 先按ESC确保退出任何残留画面
     for i in range(3):
         pyautogui.press('esc')
         time.sleep(0.5)
     time.sleep(1)
     pyautogui.hotkey('ctrl', '/')
     pyautogui.typewrite('/nS_BCE_68001397')
     time.sleep(1)
     pyautogui.press('enter')
     print("5")
     time.sleep(5)
     #按复杂选择条件选择的权限
     pyautogui.typewrite('S_TCODE')
     time.sleep(1)
     pyautogui.press('enter')
     time.sleep(5)
     pyautogui.press('tab')
     time.sleep(1)
     pyautogui.typewrite('SCC4')
     time.sleep(1)
     pyautogui.press('tab')
     time.sleep(1)
     pyautogui.press('tab')
     time.sleep(1)
     pyautogui.press('tab')
     time.sleep(1)
     pyautogui.press('tab')
     time.sleep(2)
     pyautogui.typewrite('S_TABU_CLI')
     time.sleep(1)
     pyautogui.press('enter')
     time.sleep(5)
     pyautogui.press('tab')
     pyautogui.typewrite('X')
     time.sleep(1)
     pyautogui.press('tab')
     pyautogui.press('tab')
     pyautogui.press('tab')
     pyautogui.press('tab')
     time.sleep(1)
     pyautogui.typewrite('S_TABU_NAM')   
     time.sleep(1)
     pyautogui.press('enter')
     time.sleep(5)
     screenshot = pyautogui.screenshot()
     screenshot.save(os.path.join(save_path,'basis_1_scc4_查看权限_b_条件2确认.png'))
     pyautogui.press('tab')
     time.sleep(2)
     pyautogui.typewrite('02')
     time.sleep(1)
     pyautogui.press('tab')
     pyautogui.press('tab')
     pyautogui.press('tab')
     pyautogui.press('tab')
     time.sleep(1)
     pyautogui.typewrite('T000')
     time.sleep(1)
     screenshot = pyautogui.screenshot()
     screenshot.save(os.path.join(save_path,'basis_1_scc4_查看权限_b.png'))
     pyautogui.hotkey('F8')
     time.sleep(SLEEP_LONG)
     ClickMouse_UP()

     #截图表b筛选条件
     pyautogui.press('pageup')
     time.sleep(3)
     screenshot = pyautogui.screenshot()
     screenshot.save(os.path.join(save_path,'basis_1_1.b查询结果1.png')) 
     pyautogui.press('pagedown')
     time.sleep(3)
     screenshot = pyautogui.screenshot()
     screenshot.save(os.path.join(save_path,'basis_1_1.b查询结果2.png'))

     # 完整性截图
     ClickMouse_DOWN()
     pyautogui.hotkey('ctrl', 'shift', 'down')
     time.sleep(3)
     screenshot = pyautogui.screenshot()
     screenshot.save(os.path.join(save_path, 'basis_1_1.b查询结果3.png'))
     
     #导出表B
     GetExcel_shortcutKey_1()
     pyautogui.typewrite('basis_1_1_b')
     GetExcel_shortcutKey_2()

     #返回
     for i in range(2):
         pyautogui.press('F3')
         time.sleep(1)

#科目余额表
def GetTB(save_path):
    setup_pyautogui()
    #登录至菜单
    time.sleep(1)
    for i in range(3):
        pyautogui.press('esc')
        time.sleep(0.5)
    time.sleep(1)
    pyautogui.hotkey('ctrl', '/')
    time.sleep(1)
    pyautogui.typewrite('/nS_ALR_87012277')
    time.sleep(5)
    pyautogui.press('enter')
    time.sleep(5)
    
    #公司编码、会计年度
    for i in range(6):
        pyautogui.press('tab')
        time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.typewrite(COMPANY_CODE) #公司代码
    pyautogui.hotkey('ctrl', 'tab')
    time.sleep(1)
    pyautogui.hotkey('ctrl', 'tab')
    time.sleep(1)
    pyautogui.hotkey('ctrl', 'tab')
    time.sleep(1)
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.typewrite(FISCAL_YEAR)
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path,'config.png'))
    for i in range(4):
        pyautogui.hotkey('ctrl', 'tab')
        time.sleep(1)
    pyautogui.press('enter')
    time.sleep(5)
    ClickMouse_UP()
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path,'TB_1.png'))
    pyautogui.hotkey('ctrl', 'shift', 'pagedown')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path,'TB_2.png'))
    pyautogui.hotkey('ctrl', '/')
    GetExcel_pc_1()
    pyautogui.typewrite('TB')
    GetExcel_pc_2()

    #返回
    pyautogui.press('tab')
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(1)
    for i in range(2):
        pyautogui.press('F3')
        time.sleep(1)


#序时账
def GetJE(save_path):
    setup_pyautogui()
    time.sleep(1)
    for i in range(3):
        pyautogui.press('esc')
        time.sleep(0.5)
    time.sleep(1)
    pyautogui.hotkey('ctrl', '/')
    time.sleep(1)
    pyautogui.typewrite('/nSE16')
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(5)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(1)
    pyautogui.typewrite('ACDOCA')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path,'ACDOCA.png'))
    pyautogui.press('enter')
    time.sleep(5)
    pyautogui.hotkey('ctrl', 'tab')
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(5)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path,'JE_1.png'))
    time.sleep(1)
    pyautogui.hotkey('ctrl','shift','F12')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path,'JE_2.png'))
    for i in range(3):
        pyautogui.hotkey('ctrl', 'tab')
        time.sleep(1)
    pyautogui.hotkey('ctrl','a')
    GetExcel_pc_1()
    pyautogui.typewrite('JE')
    GetExcel_pc_2()

    # 返回
    pyautogui.press('tab')
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(1)
    for i in range(3):
        pyautogui.press('F3')
        time.sleep(1)

'''
#第二页 没有权限访问
#替代性程序
def Getbasis_2_2(save_path):
    setup_pyautogui()
    for i in range(3):
        pyautogui.press('esc')
        time.sleep(0.5)
    time.sleep(1)
    pyautogui.hotkey('ctrl', '/')
    pyautogui.typewrite('/nSE16')
    pyautogui.press('enter')
    time.sleep(5)
    pyautogui.typewrite('T000')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_2_T000.png'))
    pyautogui.press('enter')
    time.sleep(5)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_2_筛选条件.png'))
    time.sleep(1)
    pyautogui.press('F8')
    time.sleep(5)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_2_结果.png'))

    #导出
    for i in range(3):
        pyautogui.hotkey('ctrl', 'tab')
        time.sleep(1)
    clear_input()
    GetExcel_pc_1()
    pyautogui.typewrite('basis_2')
    GetExcel_pc_2()

    # 返回
    pyautogui.press('tab')
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(1)
    for i in range(3):
        pyautogui.press('F3')
        time.sleep(1)

#第三页 与12重合

def Getbasis_3(save_path):
    setup_pyautogui()
    for i in range(3):
        pyautogui.press('esc')
        time.sleep(0.5)
    time.sleep(1)
    pyautogui.hotkey('ctrl', '/')
    pyautogui.typewrite('/nSA38')
    pyautogui.press('enter')
    time.sleep(5)
    pyautogui.hotkey('ctrl', '/')
    pyautogui.typewrite('RSPARAM')
    pyautogui.press('enter')
    time.sleep(5)

    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_3.png'))

    GetExcel_shortcutKey_1()
    pyautogui.typewrite('basis_3')
    GetExcel_shortcutKey_2()
'''



def Getbasis_4(save_path):
    setup_pyautogui()
    time.sleep(1)
    for i in range(3):
        pyautogui.press('esc')
        time.sleep(0.5)
    time.sleep(1)
    pyautogui.hotkey('ctrl', '/')
    time.sleep(1)
    pyautogui.typewrite('/nSE16')
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(5)
    clear_input()
    pyautogui.typewrite('DD09L')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'Getbasis_4_DD09L.png'))
    pyautogui.press('enter')
    time.sleep(5)
    pyautogui.typewrite('T000')
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(5)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'Getbasis_4_T000.png'))
    pyautogui.press('F8')
    time.sleep(5)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'Getbasis_4.png'))

    #返回
    for i in range(3):
        pyautogui.press('F3')
        time.sleep(1)




def Getbasis_5(save_path):
    setup_pyautogui()
    sub_steps = ["5a", "5b"]
    state = load_progress(save_path)
    '''
    # SUIM-用户-按复杂选择条件选择的用户-按权限值
    time.sleep(1)
    for i in range(3):
        pyautogui.press('esc')
        time.sleep(0.5)
    time.sleep(1)
    pyautogui.hotkey('ctrl', '/')
    pyautogui.typewrite('/nS_BCE_68001397')
    time.sleep(1.0)
    pyautogui.press('enter')
    time.sleep(5)
    # 按复杂选择条件选择的权限
    pyautogui.typewrite('S_TCODE')
    time.sleep(1.0)
    pyautogui.press('enter')
    time.sleep(5)
    pyautogui.press('tab')
    time.sleep(1.0)
    pyautogui.typewrite('STMS')
    time.sleep(1.0)
    pyautogui.press('tab')
    time.sleep(1.0)
    pyautogui.typewrite('STMS_IMPORT')
    time.sleep(1.0)
    pyautogui.press('tab')
    pyautogui.press('tab')
    pyautogui.press('tab')
    time.sleep(2)
    pyautogui.typewrite('S_CTS_ADMI')
    time.sleep(1.0)
    pyautogui.press('enter')
    time.sleep(5)
    pyautogui.press('tab')
    pyautogui.typewrite('IMP*')
    time.sleep(1.0)
    pyautogui.press('tab')
    pyautogui.press('tab')
    pyautogui.press('tab')
    pyautogui.press('tab')
    time.sleep(1.0)
    pyautogui.typewrite('S_TRANSPRT')
    time.sleep(1.0)
    pyautogui.press('enter')
    time.sleep(5)
    pyautogui.press('tab')
    time.sleep(2)
    pyautogui.typewrite('03')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_5_STMS_查看权限_a.png'))  # 根据前台获取的保存路径保存
    pyautogui.hotkey('F8')
    time.sleep(SLEEP_LONG)
    ClickMouse_UP()
    '''

    # ---------- 子步骤 5a ----------
    skip_5a = should_skip_sub_step(state, "Getbasis_5", "5a", sub_steps)
    if not skip_5a:
        # SUIM-用户-按复杂选择条件选择的用户-按权限值
        time.sleep(1)
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nS_BCE_68001397')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(5)
        # 按复杂选择条件选择的权限
        pyautogui.typewrite('S_TCODE')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.press('tab')
        time.sleep(1.0)
        pyautogui.typewrite('STMS')
        time.sleep(1.0)
        pyautogui.press('tab')
        time.sleep(1.0)
        pyautogui.typewrite('STMS_IMPORT')
        time.sleep(1.0)
        pyautogui.press('tab')
        pyautogui.press('tab')
        pyautogui.press('tab')
        time.sleep(2)
        pyautogui.typewrite('S_CTS_ADMI')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.press('tab')
        pyautogui.typewrite('IMP*')
        time.sleep(1.0)
        pyautogui.press('tab')
        pyautogui.press('tab')
        pyautogui.press('tab')
        pyautogui.press('tab')
        time.sleep(1.0)
        pyautogui.typewrite('S_TRANSPRT')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.press('tab')
        time.sleep(2)
        pyautogui.typewrite('03')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_5_STMS_查看权限_a.png'))  # 根据前台获取的保存路径保存
        pyautogui.hotkey('F8')
        time.sleep(SLEEP_LONG)
        ClickMouse_UP()

        # 截图表a筛选条件
        pyautogui.press('pageup')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_5.a查询结果1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_5.a查询结果2.png'))

        # 完整性截图
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_5.a查询结果3.png'))

        # 导出表a
        GetExcel_shortcutKey_1()
        pyautogui.typewrite('basis_5_a')
        GetExcel_shortcutKey_2()

        #返回
        pyautogui.press('F3')
        time.sleep(1)

        mark_sub_step_done(save_path, "Getbasis_5", "5a", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 5a")

    # ---------- 子步骤 5b ----------
    skip_5b = should_skip_sub_step(state, "Getbasis_5", "5b", sub_steps)
    if not skip_5b:
        #表b
        time.sleep(1)
        pyautogui.press('tab')
        clear_input()
        pyautogui.typewrite('RSAUDITM_BCE_IMPO')
        pyautogui.press('enter')
        pyautogui.press('tab')
        time.sleep(1)
        clear_input()
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_5_STMS_查看权限_b.png'))  # 根据前台获取的保存路径保存
        pyautogui.hotkey('F8')
        time.sleep(5)
        ClickMouse_UP()

        # 截图表b筛选条件
        pyautogui.press('pageup')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_5.b查询结果1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_5.b查询结果2.png'))

        # 完整性截图
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_5.b查询结果3.png'))

        # 导出表b
        GetExcel_shortcutKey_1()
        pyautogui.typewrite('basis_5_b')
        GetExcel_shortcutKey_2()

        #返回
        for i in range(2):
            pyautogui.press('F3')
            time.sleep(1)

        mark_sub_step_done(save_path, "Getbasis_5", "5b", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 5b")


def Getbasis_6(save_path):
    setup_pyautogui()
    time.sleep(1)
    # SUIM-用户-按复杂选择条件选择的用户-按权限值
    for i in range(3):
        pyautogui.press('esc')
        time.sleep(0.5)
    time.sleep(1)
    pyautogui.hotkey('ctrl', '/')
    pyautogui.typewrite('/nS_BCE_68001397')
    time.sleep(1.0)
    pyautogui.press('enter')
    time.sleep(5)
    # 按复杂选择条件选择的权限
    pyautogui.typewrite('S_DEVELOP')
    time.sleep(1.0)
    pyautogui.press('enter')
    time.sleep(5)
    for i in range(5):
        pyautogui.press('tab')
    time.sleep(2)
    pyautogui.typewrite('DEBUG')
    time.sleep(1.0)
    pyautogui.press('enter')
    time.sleep(5)
    for i in range(12):
        pyautogui.press('tab')
    pyautogui.typewrite('02')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_6.png'))  # 根据前台获取的保存路径保存
    pyautogui.hotkey('F8')
    time.sleep(SLEEP_LONG)
    ClickMouse_UP()

    # 截图筛选条件
    pyautogui.press('pageup')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_6.查询结果1.png'))
    pyautogui.press('pagedown')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_6.查询结果2.png'))

    # 完整性截图
    ClickMouse_DOWN()
    pyautogui.hotkey('ctrl', 'shift', 'down')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_6.查询结果3.png'))

    # 导出
    GetExcel_shortcutKey_1()
    pyautogui.typewrite('basis_6')
    GetExcel_shortcutKey_2()

    #返回
    for i in range(2):
        pyautogui.press('F3')
        time.sleep(1)




def Getbasis_7(save_path):
    setup_pyautogui()
    for i in range(3):
        pyautogui.press('esc')
        time.sleep(0.5)
    time.sleep(1)
    # SUIM-用户-按复杂选择条件选择的用户-按权限值
    pyautogui.hotkey('ctrl', '/')
    pyautogui.typewrite('/nS_BCE_68001397')
    time.sleep(1.0)
    pyautogui.press('enter')
    time.sleep(5)
    # 按复杂选择条件选择的权限
    pyautogui.typewrite('S_TCODE')
    time.sleep(1.0)
    pyautogui.press('enter')
    time.sleep(5)
    pyautogui.press('tab')
    pyautogui.typewrite('PFCG')
    time.sleep(1.0)
    pyautogui.press('enter')
    time.sleep(5)
    for i in range(4):
        pyautogui.press('tab')
    time.sleep(2)
    pyautogui.typewrite('S_USER_AGR')
    time.sleep(1.0)
    pyautogui.press('enter')
    time.sleep(5)
    for i in range(5):
        pyautogui.press('tab')
    time.sleep(1.0)
    pyautogui.typewrite('01')
    time.sleep(1.0)
    pyautogui.press('enter')
    time.sleep(1.0)
    pyautogui.press('tab')
    pyautogui.typewrite('02')
    time.sleep(1.0)
    for i in range(3):
        pyautogui.press('tab')
    pyautogui.typewrite('S_USER_PRO')
    time.sleep(1.0)
    pyautogui.press('enter')
    time.sleep(1.0)
    for i in range(5):
        pyautogui.press('tab')
    time.sleep(1.0)
    pyautogui.typewrite('01')
    time.sleep(1.0)
    pyautogui.press('enter')
    time.sleep(1.0)
    pyautogui.press('tab')
    pyautogui.typewrite('02')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_7.png'))  # 根据前台获取的保存路径保存
    pyautogui.hotkey('F8')
    time.sleep(SLEEP_LONG)
    ClickMouse_UP()

    # 截图筛选条件
    pyautogui.press('pageup')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_7.查询结果1.png'))
    pyautogui.press('pagedown')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_7.查询结果2.png'))

    # 完整性截图
    ClickMouse_DOWN()
    pyautogui.hotkey('ctrl', 'shift', 'down')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_7.查询结果3.png'))

    # 导出
    GetExcel_shortcutKey_1()
    pyautogui.typewrite('basis_7')
    GetExcel_shortcutKey_2()

    # 返回
    for i in range(2):
        pyautogui.press('F3')
        time.sleep(1)



def Getbasis_8_1(save_path):
    setup_pyautogui()
    time.sleep(1)
    # SUIM-更改文档-用于角色
    for i in range(3):
        pyautogui.press('esc')
        time.sleep(0.5)
    time.sleep(1)
    pyautogui.hotkey('ctrl', '/')
    pyautogui.typewrite('/nRSSCD100_PFCG')
    time.sleep(1.0)
    pyautogui.press('enter')
    time.sleep(5)
    pyautogui.press('down')
    pyautogui.press('down')
    time.sleep(1)
    clear_input()
    pyautogui.typewrite(AUDIT_START_DATE) #审计期间开始日期
    pyautogui.press('enter')
    time.sleep(1)
    pyautogui.press('down')
    pyautogui.press('down')
    time.sleep(1)
    clear_input()
    pyautogui.typewrite(AUDIT_END_DATE) #审计期间结束日期
    pyautogui.press('enter')
    time.sleep(2)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_8_1_日期设置.png'))
    pyautogui.hotkey('ctrl', 'tab')
    for i in range(14):
        pyautogui.press('down')
        time.sleep(1)
    time.sleep(2)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_8_1.筛选条件.png'))  # 根据前台获取的保存路径保存
    time.sleep(1)
    pyautogui.hotkey('F8')
    time.sleep(5)
    ClickMouse_UP()

    # 截图筛选条件
    pyautogui.press('pageup')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_8_1.查询结果1.png'))
    pyautogui.press('pagedown')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_8_1.查询结果2.png'))

    # 完整性截图
    ClickMouse_DOWN()
    pyautogui.hotkey('ctrl', 'shift', 'right')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_8_1.查询结果3.png'))
    pyautogui.hotkey('ctrl', 'shift', 'down')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_8_1.查询结果4.png'))
    pyautogui.hotkey('ctrl', 'shift', 'left')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_8_1.查询结果5.png'))

    # 导出
    GetExcel_shortcutKey_1()
    pyautogui.typewrite('basis_8_1')
    GetExcel_shortcutKey_2()

    #返回
    for i in range(2):
        pyautogui.press('F3')
        time.sleep(1)


def Getbasis_8_2(save_path):
    setup_pyautogui()
    time.sleep(1)
    # SUIM-更改文档-针对参数文件
    for i in range(3):
        pyautogui.press('esc')
        time.sleep(0.5)
    time.sleep(1)
    pyautogui.hotkey('ctrl', '/')
    pyautogui.typewrite('/nS_BCE_68001440')
    time.sleep(1.0)
    pyautogui.press('enter')
    time.sleep(5)
    pyautogui.press('down')
    pyautogui.press('down')
    time.sleep(1)
    clear_input()
    clear_input()
    pyautogui.typewrite(AUDIT_START_DATE) #审计期间开始日期
    pyautogui.press('enter')
    time.sleep(1)
    pyautogui.press('down')
    time.sleep(1)
    clear_input()
    pyautogui.typewrite(AUDIT_END_DATE) #审计期间结束日期
    pyautogui.press('enter')
    time.sleep(2)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_8_2_日期设置.png'))
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_8_2.png'))  # 根据前台获取的保存路径保存
    time.sleep(1)
    pyautogui.hotkey('F8')
    time.sleep(5)
    ClickMouse_UP()

    # 截图筛选条件
    pyautogui.press('pageup')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_8_2.查询结果1.png'))
    pyautogui.press('pagedown')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_8_2.查询结果2.png'))

    # 完整性截图
    ClickMouse_DOWN()
    pyautogui.hotkey('ctrl', 'shift', 'down')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_8_2.查询结果3.png'))
    time.sleep(2)

    # 导出
    GetExcel_shortcutKey_1()
    pyautogui.typewrite('basis_8_2')
    GetExcel_shortcutKey_2()

    #返回
    for i in range(2):
        pyautogui.press('F3')
        time.sleep(1)

def Getbasis_9(save_path):
    setup_pyautogui()
    sub_steps = ["9a","9b","9c","9d","9e","9f","9g","9h","9i","9j","9k","9l","9m","9n","9o","9p"]
    state = load_progress(save_path)

    # ---------- 子步骤 9a ----------
    skip_9a = should_skip_sub_step(state, "Getbasis_9", "9a", sub_steps)
    if not skip_9a:
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nS_BCE_68001397')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.typewrite('S_TCODE')
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.press('tab')
        pyautogui.typewrite('SU01')
        pyautogui.press('enter')
        time.sleep(3)
        pyautogui.press('tab')
        clear_input()
        pyautogui.typewrite('SU02')
        pyautogui.press('enter')
        time.sleep(3)
        for i in range(3):
            pyautogui.press('tab')
        time.sleep(5)
        pyautogui.typewrite('S_USER_GRP')
        pyautogui.press('enter')
        time.sleep(5)
        for i in range(5):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('02')
        pyautogui.press('tab')
        pyautogui.typewrite('22')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9a1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9a2.png'))
        pyautogui.hotkey('F8')
        time.sleep(SLEEP_LONG)
        ClickMouse_UP()
        pyautogui.press('pageup')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9a.查询结果1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9a.查询结果2.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9a.查询结果3.png'))
        GetExcel_shortcutKey_1()
        pyautogui.typewrite('basis_9a')
        GetExcel_shortcutKey_2()
        for i in range(2):
            pyautogui.press('F3')
            time.sleep(1)
        mark_sub_step_done(save_path, "Getbasis_9", "9a", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 9a")
    # ---------- 子步骤 9b ----------
    skip_9b = should_skip_sub_step(state, "Getbasis_9", "9b", sub_steps)
    if not skip_9b:
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nS_BCE_68001397')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.typewrite('S_TCODE')
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.press('tab')
        pyautogui.typewrite('SU12')
        pyautogui.press('enter')
        time.sleep(3)
        pyautogui.press('tab')
        clear_input()
        pyautogui.typewrite('PFCG')
        pyautogui.press('enter')
        time.sleep(3)
        for i in range(3):
            pyautogui.press('tab')
        time.sleep(5)
        pyautogui.typewrite('S_USER_GRP')
        pyautogui.press('enter')
        time.sleep(5)
        for i in range(5):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('02')
        pyautogui.press('tab')
        pyautogui.typewrite('22')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9b1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9b2.png'))
        pyautogui.hotkey('F8')
        time.sleep(SLEEP_LONG)
        ClickMouse_UP()
        pyautogui.press('pageup')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9b.查询结果1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9b.查询结果2.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9b.查询结果3.png'))
        GetExcel_shortcutKey_1()
        pyautogui.typewrite('basis_9b')
        GetExcel_shortcutKey_2()
        for i in range(2):
            pyautogui.press('F3')
            time.sleep(1)
        mark_sub_step_done(save_path, "Getbasis_9", "9b", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 9b")
    # ---------- 子步骤 9c ----------
    skip_9c = should_skip_sub_step(state, "Getbasis_9", "9c", sub_steps)
    if not skip_9c:
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nS_BCE_68001397')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.typewrite('S_TCODE')
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.press('tab')
        pyautogui.typewrite('GCE1')
        pyautogui.press('enter')
        time.sleep(3)
        pyautogui.press('tab')
        clear_input()
        pyautogui.typewrite('OMDL')
        pyautogui.press('enter')
        time.sleep(3)
        for i in range(3):
            pyautogui.press('tab')
        time.sleep(5)
        pyautogui.typewrite('S_USER_GRP')
        pyautogui.press('enter')
        time.sleep(5)
        for i in range(5):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('02')
        pyautogui.press('tab')
        pyautogui.typewrite('22')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9c1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9c2.png'))
        pyautogui.hotkey('F8')
        time.sleep(SLEEP_LONG)
        ClickMouse_UP()
        pyautogui.press('pageup')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9c.查询结果1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9c.查询结果2.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9c.查询结果3.png'))
        GetExcel_shortcutKey_1()
        pyautogui.typewrite('basis_9c')
        GetExcel_shortcutKey_2()
        for i in range(2):
            pyautogui.press('F3')
            time.sleep(1)
        mark_sub_step_done(save_path, "Getbasis_9", "9c", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 9c")
    # ---------- 子步骤 9d ----------
    skip_9d = should_skip_sub_step(state, "Getbasis_9", "9d", sub_steps)
    if not skip_9d:
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nS_BCE_68001397')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.typewrite('S_TCODE')
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.press('tab')
        pyautogui.typewrite('OMEH')
        pyautogui.press('enter')
        time.sleep(3)
        pyautogui.press('tab')
        clear_input()
        pyautogui.typewrite('OMWF')
        pyautogui.press('enter')
        time.sleep(3)
        for i in range(3):
            pyautogui.press('tab')
        time.sleep(5)
        pyautogui.typewrite('S_USER_GRP')
        pyautogui.press('enter')
        time.sleep(5)
        for i in range(5):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('02')
        pyautogui.press('tab')
        pyautogui.typewrite('22')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9d1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9d2.png'))
        pyautogui.hotkey('F8')
        time.sleep(SLEEP_LONG)
        ClickMouse_UP()
        pyautogui.press('pageup')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9d.查询结果1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9d.查询结果2.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9d.查询结果3.png'))
        GetExcel_shortcutKey_1()
        pyautogui.typewrite('basis_9d')
        GetExcel_shortcutKey_2()
        for i in range(2):
            pyautogui.press('F3')
            time.sleep(1)
        mark_sub_step_done(save_path, "Getbasis_9", "9d", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 9d")
    # ---------- 子步骤 9e ----------
    skip_9e = should_skip_sub_step(state, "Getbasis_9", "9e", sub_steps)
    if not skip_9e:
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nS_BCE_68001397')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.typewrite('S_TCODE')
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.press('tab')
        pyautogui.typewrite('ON09')
        pyautogui.press('enter')
        time.sleep(3)
        pyautogui.press('tab')
        clear_input()
        pyautogui.typewrite('OOUS')
        pyautogui.press('enter')
        time.sleep(3)
        for i in range(3):
            pyautogui.press('tab')
        time.sleep(5)
        pyautogui.typewrite('S_USER_GRP')
        pyautogui.press('enter')
        time.sleep(5)
        for i in range(5):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('02')
        pyautogui.press('tab')
        pyautogui.typewrite('22')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9e1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9e2.png'))
        pyautogui.hotkey('F8')
        time.sleep(SLEEP_LONG)
        ClickMouse_UP()
        pyautogui.press('pageup')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9e.查询结果1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9e.查询结果2.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9e.查询结果3.png'))
        GetExcel_shortcutKey_1()
        pyautogui.typewrite('basis_9e')
        GetExcel_shortcutKey_2()
        for i in range(2):
            pyautogui.press('F3')
            time.sleep(1)
        mark_sub_step_done(save_path, "Getbasis_9", "9e", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 9e")
    # ---------- 子步骤 9f ----------
    skip_9f = should_skip_sub_step(state, "Getbasis_9", "9f", sub_steps)
    if not skip_9f:
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nS_BCE_68001397')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.typewrite('S_TCODE')
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.press('tab')
        pyautogui.typewrite('OPF0')
        pyautogui.press('enter')
        time.sleep(3)
        pyautogui.press('tab')
        clear_input()
        pyautogui.typewrite('OTZ1')
        pyautogui.press('enter')
        time.sleep(3)
        for i in range(3):
            pyautogui.press('tab')
        time.sleep(5)
        pyautogui.typewrite('S_USER_GRP')
        pyautogui.press('enter')
        time.sleep(5)
        for i in range(5):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('02')
        pyautogui.press('tab')
        pyautogui.typewrite('22')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9f1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9f2.png'))
        pyautogui.hotkey('F8')
        time.sleep(SLEEP_LONG)
        ClickMouse_UP()
        pyautogui.press('pageup')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9f.查询结果1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9f.查询结果2.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9f.查询结果3.png'))
        GetExcel_shortcutKey_1()
        pyautogui.typewrite('basis_9f')
        GetExcel_shortcutKey_2()
        for i in range(2):
            pyautogui.press('F3')
            time.sleep(1)
        mark_sub_step_done(save_path, "Getbasis_9", "9f", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 9f")
    # ---------- 子步骤 9g ----------
    skip_9g = should_skip_sub_step(state, "Getbasis_9", "9g", sub_steps)
    if not skip_9g:
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nS_BCE_68001397')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.typewrite('S_TCODE')
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.press('tab')
        pyautogui.typewrite('OY22')
        pyautogui.press('enter')
        time.sleep(3)
        pyautogui.press('tab')
        clear_input()
        pyautogui.typewrite('OY28')
        pyautogui.press('enter')
        time.sleep(3)
        for i in range(3):
            pyautogui.press('tab')
        time.sleep(5)
        pyautogui.typewrite('S_USER_GRP')
        pyautogui.press('enter')
        time.sleep(5)
        for i in range(5):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('02')
        pyautogui.press('tab')
        pyautogui.typewrite('22')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9g1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9g2.png'))
        pyautogui.hotkey('F8')
        time.sleep(SLEEP_LONG)
        ClickMouse_UP()
        pyautogui.press('pageup')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9g.查询结果1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9g.查询结果2.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9g.查询结果3.png'))
        GetExcel_shortcutKey_1()
        pyautogui.typewrite('basis_9g')
        GetExcel_shortcutKey_2()
        for i in range(2):
            pyautogui.press('F3')
            time.sleep(1)
        mark_sub_step_done(save_path, "Getbasis_9", "9g", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 9g")
    # ---------- 子步骤 9h ----------
    skip_9h = should_skip_sub_step(state, "Getbasis_9", "9h", sub_steps)
    if not skip_9h:
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nS_BCE_68001397')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.typewrite('S_TCODE')
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.press('tab')
        pyautogui.typewrite('OY29')
        pyautogui.press('enter')
        time.sleep(3)
        pyautogui.press('tab')
        clear_input()
        pyautogui.typewrite('OY30')
        pyautogui.press('enter')
        time.sleep(3)
        for i in range(3):
            pyautogui.press('tab')
        time.sleep(5)
        pyautogui.typewrite('S_USER_GRP')
        pyautogui.press('enter')
        time.sleep(5)
        for i in range(5):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('02')
        pyautogui.press('tab')
        pyautogui.typewrite('22')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9h1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9h2.png'))
        pyautogui.hotkey('F8')
        time.sleep(SLEEP_LONG)
        ClickMouse_UP()
        pyautogui.press('pageup')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9h.查询结果1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9h.查询结果2.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9h.查询结果3.png'))
        GetExcel_shortcutKey_1()
        pyautogui.typewrite('basis_9h')
        GetExcel_shortcutKey_2()
        for i in range(2):
            pyautogui.press('F3')
            time.sleep(1)
        mark_sub_step_done(save_path, "Getbasis_9", "9h", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 9h")
    # ---------- 子步骤 9i ----------
    skip_9i = should_skip_sub_step(state, "Getbasis_9", "9i", sub_steps)
    if not skip_9i:
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nS_BCE_68001397')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.typewrite('S_TCODE')
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.press('tab')
        pyautogui.typewrite('SU01')
        pyautogui.press('enter')
        time.sleep(3)
        pyautogui.press('tab')
        clear_input()
        pyautogui.typewrite('SU10')
        pyautogui.press('enter')
        time.sleep(3)
        for i in range(3):
            pyautogui.press('tab')
        time.sleep(5)
        pyautogui.typewrite('S_USER_GRP')
        pyautogui.press('enter')
        time.sleep(5)
        for i in range(5):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('02')
        pyautogui.press('tab')
        pyautogui.typewrite('22')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9i1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9i2.png'))
        pyautogui.hotkey('F8')
        time.sleep(SLEEP_LONG)
        ClickMouse_UP()
        pyautogui.press('pageup')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9i.查询结果1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9i.查询结果2.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9i.查询结果3.png'))
        GetExcel_shortcutKey_1()
        pyautogui.typewrite('basis_9i')
        GetExcel_shortcutKey_2()
        for i in range(2):
            pyautogui.press('F3')
            time.sleep(1)
        mark_sub_step_done(save_path, "Getbasis_9", "9i", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 9i")
    # ---------- 子步骤 9j ----------
    skip_9j = should_skip_sub_step(state, "Getbasis_9", "9j", sub_steps)
    if not skip_9j:
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nS_BCE_68001397')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.typewrite('S_TCODE')
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.press('tab')
        pyautogui.typewrite('SU12')
        pyautogui.press('enter')
        time.sleep(3)
        pyautogui.press('tab')
        clear_input()
        pyautogui.typewrite('PFCG')
        pyautogui.press('enter')
        time.sleep(3)
        for i in range(3):
            pyautogui.press('tab')
        time.sleep(5)
        pyautogui.typewrite('S_USER_GRP')
        pyautogui.press('enter')
        time.sleep(5)
        for i in range(5):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('02')
        pyautogui.press('tab')
        pyautogui.typewrite('22')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9j1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9j2.png'))
        pyautogui.hotkey('F8')
        time.sleep(SLEEP_LONG)
        ClickMouse_UP()
        pyautogui.press('pageup')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9j.查询结果1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9j.查询结果2.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9j.查询结果3.png'))
        GetExcel_shortcutKey_1()
        pyautogui.typewrite('basis_9j')
        GetExcel_shortcutKey_2()
        for i in range(2):
            pyautogui.press('F3')
            time.sleep(1)
        mark_sub_step_done(save_path, "Getbasis_9", "9j", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 9j")
    # ---------- 子步骤 9k ----------
    skip_9k = should_skip_sub_step(state, "Getbasis_9", "9k", sub_steps)
    if not skip_9k:
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nS_BCE_68001397')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.typewrite('S_TCODE')
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.press('tab')
        pyautogui.typewrite('GCE1')
        pyautogui.press('enter')
        time.sleep(3)
        pyautogui.press('tab')
        clear_input()
        pyautogui.typewrite('OMDL')
        pyautogui.press('enter')
        time.sleep(3)
        for i in range(3):
            pyautogui.press('tab')
        time.sleep(5)
        pyautogui.typewrite('S_USER_GRP')
        pyautogui.press('enter')
        time.sleep(5)
        for i in range(5):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('02')
        pyautogui.press('tab')
        pyautogui.typewrite('22')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9k1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9k2.png'))
        pyautogui.hotkey('F8')
        time.sleep(SLEEP_LONG)
        ClickMouse_UP()
        pyautogui.press('pageup')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9k.查询结果1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9k.查询结果2.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9k.查询结果3.png'))
        GetExcel_shortcutKey_1()
        pyautogui.typewrite('basis_9k')
        GetExcel_shortcutKey_2()
        for i in range(2):
            pyautogui.press('F3')
            time.sleep(1)
        mark_sub_step_done(save_path, "Getbasis_9", "9k", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 9k")
    # ---------- 子步骤 9l ----------
    skip_9l = should_skip_sub_step(state, "Getbasis_9", "9l", sub_steps)
    if not skip_9l:
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nS_BCE_68001397')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.typewrite('S_TCODE')
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.press('tab')
        pyautogui.typewrite('OMEH')
        pyautogui.press('enter')
        time.sleep(3)
        pyautogui.press('tab')
        clear_input()
        pyautogui.typewrite('OMWF')
        pyautogui.press('enter')
        time.sleep(3)
        for i in range(3):
            pyautogui.press('tab')
        time.sleep(5)
        pyautogui.typewrite('S_USER_GRP')
        pyautogui.press('enter')
        time.sleep(5)
        for i in range(5):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('02')
        pyautogui.press('tab')
        pyautogui.typewrite('22')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9l1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9l2.png'))
        pyautogui.hotkey('F8')
        time.sleep(SLEEP_LONG)
        ClickMouse_UP()
        pyautogui.press('pageup')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9l.查询结果1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9l.查询结果2.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9l.查询结果3.png'))
        GetExcel_shortcutKey_1()
        pyautogui.typewrite('basis_9l')
        GetExcel_shortcutKey_2()
        for i in range(2):
            pyautogui.press('F3')
            time.sleep(1)
        mark_sub_step_done(save_path, "Getbasis_9", "9l", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 9l")
    # ---------- 子步骤 9m ----------
    skip_9m = should_skip_sub_step(state, "Getbasis_9", "9m", sub_steps)
    if not skip_9m:
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nS_BCE_68001397')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.typewrite('S_TCODE')
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.press('tab')
        pyautogui.typewrite('ON09')
        pyautogui.press('enter')
        time.sleep(3)
        pyautogui.press('tab')
        clear_input()
        pyautogui.typewrite('OOUS')
        pyautogui.press('enter')
        time.sleep(3)
        for i in range(3):
            pyautogui.press('tab')
        time.sleep(5)
        pyautogui.typewrite('S_USER_GRP')
        pyautogui.press('enter')
        time.sleep(5)
        for i in range(5):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('02')
        pyautogui.press('tab')
        pyautogui.typewrite('22')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9m1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9m2.png'))
        pyautogui.hotkey('F8')
        time.sleep(SLEEP_LONG)
        ClickMouse_UP()
        pyautogui.press('pageup')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9m.查询结果1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9m.查询结果2.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9m.查询结果3.png'))
        GetExcel_shortcutKey_1()
        pyautogui.typewrite('basis_9m')
        GetExcel_shortcutKey_2()
        for i in range(2):
            pyautogui.press('F3')
            time.sleep(1)
        mark_sub_step_done(save_path, "Getbasis_9", "9m", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 9m")
    # ---------- 子步骤 9n ----------
    skip_9n = should_skip_sub_step(state, "Getbasis_9", "9n", sub_steps)
    if not skip_9n:
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nS_BCE_68001397')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.typewrite('S_TCODE')
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.press('tab')
        pyautogui.typewrite('OPF0')
        pyautogui.press('enter')
        time.sleep(3)
        pyautogui.press('tab')
        clear_input()
        pyautogui.typewrite('OTZ1')
        pyautogui.press('enter')
        time.sleep(3)
        for i in range(3):
            pyautogui.press('tab')
        time.sleep(5)
        pyautogui.typewrite('S_USER_GRP')
        pyautogui.press('enter')
        time.sleep(5)
        for i in range(5):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('02')
        pyautogui.press('tab')
        pyautogui.typewrite('22')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9n1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9n2.png'))
        pyautogui.hotkey('F8')
        time.sleep(SLEEP_LONG)
        ClickMouse_UP()
        pyautogui.press('pageup')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9n.查询结果1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9n.查询结果2.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9n.查询结果3.png'))
        GetExcel_shortcutKey_1()
        pyautogui.typewrite('basis_9n')
        GetExcel_shortcutKey_2()
        for i in range(2):
            pyautogui.press('F3')
            time.sleep(1)
        mark_sub_step_done(save_path, "Getbasis_9", "9n", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 9n")
    # ---------- 子步骤 9o ----------
    skip_9o = should_skip_sub_step(state, "Getbasis_9", "9o", sub_steps)
    if not skip_9o:
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nS_BCE_68001397')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.typewrite('S_TCODE')
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.press('tab')
        pyautogui.typewrite('OY22')
        pyautogui.press('enter')
        time.sleep(3)
        pyautogui.press('tab')
        clear_input()
        pyautogui.typewrite('OY28')
        pyautogui.press('enter')
        time.sleep(3)
        for i in range(3):
            pyautogui.press('tab')
        time.sleep(5)
        pyautogui.typewrite('S_USER_GRP')
        pyautogui.press('enter')
        time.sleep(5)
        for i in range(5):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('02')
        pyautogui.press('tab')
        pyautogui.typewrite('22')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9o1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9o2.png'))
        pyautogui.hotkey('F8')
        time.sleep(SLEEP_LONG)
        ClickMouse_UP()
        pyautogui.press('pageup')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9o.查询结果1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9o.查询结果2.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9o.查询结果3.png'))
        GetExcel_shortcutKey_1()
        pyautogui.typewrite('basis_9o')
        GetExcel_shortcutKey_2()
        for i in range(2):
            pyautogui.press('F3')
            time.sleep(1)
        mark_sub_step_done(save_path, "Getbasis_9", "9o", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 9o")
    # ---------- 子步骤 9p ----------
    skip_9p = should_skip_sub_step(state, "Getbasis_9", "9p", sub_steps)
    if not skip_9p:
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nS_BCE_68001397')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.typewrite('S_TCODE')
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.press('tab')
        pyautogui.typewrite('OY29')
        pyautogui.press('enter')
        time.sleep(3)
        pyautogui.press('tab')
        clear_input()
        pyautogui.typewrite('OY30')
        pyautogui.press('enter')
        time.sleep(3)
        for i in range(3):
            pyautogui.press('tab')
        time.sleep(5)
        pyautogui.typewrite('S_USER_GRP')
        pyautogui.press('enter')
        time.sleep(5)
        for i in range(5):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('02')
        pyautogui.press('tab')
        pyautogui.typewrite('22')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9p1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9p2.png'))
        pyautogui.hotkey('F8')
        time.sleep(SLEEP_LONG)
        ClickMouse_UP()
        pyautogui.press('pageup')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9p.查询结果1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9p.查询结果2.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_9p.查询结果3.png'))
        GetExcel_shortcutKey_1()
        pyautogui.typewrite('basis_9p')
        GetExcel_shortcutKey_2()
        for i in range(2):
            pyautogui.press('F3')
            time.sleep(1)
        mark_sub_step_done(save_path, "Getbasis_9", "9p", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 9p")

def Getbasis_10(save_path):
    setup_pyautogui()
    sub_steps = ["10a", "10b", "10c", "10d"]
    state = load_progress(save_path)

    # ---------- 子步骤 10a ----------
    skip_10a = should_skip_sub_step(state, "Getbasis_10", "10a", sub_steps)
    if not skip_10a:
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nS_BCE_68001397')
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.typewrite('S_TCODE')
        pyautogui.press('enter')
        time.sleep(3)
        pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('SM30')
        pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('SM31')
        for i in range(3):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('S_TABU_DIS')
        pyautogui.press('enter')
        time.sleep(3)
        pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('*')
        for i in range(4):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('02')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_10_a.png'))
        time.sleep(1)
        pyautogui.press('F8')
        time.sleep(5)
        ClickMouse_UP()
        pyautogui.press('pageup')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_10_a.查询结果1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_10_a.查询结果2.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_10_a.查询结果3.png'))
        GetExcel_shortcutKey_1()
        pyautogui.typewrite('basis_10_a')
        GetExcel_shortcutKey_2()
        for i in range(2):
            pyautogui.press('F3')
            time.sleep(1)
        mark_sub_step_done(save_path, "Getbasis_10", "10a", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 10a")

    # ---------- 子步骤 10b ----------
    skip_10b = should_skip_sub_step(state, "Getbasis_10", "10b", sub_steps)
    if not skip_10b:
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nS_BCE_68001397')
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.typewrite('S_TCODE')
        pyautogui.press('enter')
        time.sleep(3)
        for i in range(3):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('S_TABU_NAM')
        pyautogui.press('enter')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_10_b_S_TABU_NAM确认.png'))
        pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('*')
        for i in range(4):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('02')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_10_b.png'))
        time.sleep(1)
        pyautogui.press('F8')
        time.sleep(5)
        ClickMouse_UP()
        pyautogui.press('pageup')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_10_b.查询结果1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_10_b.查询结果2.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_10_b.查询结果3.png'))
        GetExcel_shortcutKey_1()
        pyautogui.typewrite('basis_10_b')
        GetExcel_shortcutKey_2()
        for i in range(2):
            pyautogui.press('F3')
            time.sleep(1)
        mark_sub_step_done(save_path, "Getbasis_10", "10b", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 10b")

    # ---------- 子步骤 10c ----------
    skip_10c = should_skip_sub_step(state, "Getbasis_10", "10c", sub_steps)
    if not skip_10c:
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nS_BCE_68001397')
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.typewrite('S_TCODE')
        pyautogui.press('enter')
        time.sleep(3)
        pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('SM34')
        for i in range(3):
            pyautogui.press('tab')
        time.sleep(1)
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_10_c.png'))
        time.sleep(1)
        pyautogui.press('F8')
        time.sleep(5)
        ClickMouse_UP()
        pyautogui.press('pageup')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_10_c.查询结果1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_10_c.查询结果2.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_10_c.查询结果3.png'))
        GetExcel_shortcutKey_1()
        pyautogui.typewrite('basis_10_c')
        GetExcel_shortcutKey_2()
        for i in range(2):
            pyautogui.press('F3')
            time.sleep(1)
        mark_sub_step_done(save_path, "Getbasis_10", "10c", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 10c")

    # ---------- 子步骤 10d ----------
    skip_10d = should_skip_sub_step(state, "Getbasis_10", "10d", sub_steps)
    if not skip_10d:
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nS_BCE_68001397')
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.typewrite('S_TCODE')
        pyautogui.press('enter')
        time.sleep(3)
        for i in range(3):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('S_TABU_DIS')
        pyautogui.press('enter')
        time.sleep(3)
        pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('*')
        for i in range(4):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('02')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_10_d.png'))
        time.sleep(1)
        pyautogui.press('F8')
        time.sleep(5)
        ClickMouse_UP()
        pyautogui.press('pageup')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_10_d.查询结果1.png'))
        pyautogui.press('pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_10_d.查询结果2.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_10_d.查询结果3.png'))
        GetExcel_shortcutKey_1()
        pyautogui.typewrite('basis_10_d')
        GetExcel_shortcutKey_2()
        for i in range(2):
            pyautogui.press('F3')
            time.sleep(1)
        mark_sub_step_done(save_path, "Getbasis_10", "10d", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 10d")

def Getbasis_11(save_path):
    setup_pyautogui()
    time.sleep(1)
    # SUIM-用户-按复杂选择条件选择的用户-按权限值
    for i in range(3):
        pyautogui.press('esc')
        time.sleep(0.5)
    time.sleep(1)
    pyautogui.hotkey('ctrl', '/')
    pyautogui.typewrite('/nS_BCE_68001397')
    time.sleep(1.0)
    pyautogui.press('enter')
    time.sleep(5)
    pyautogui.typewrite('S_TCODE')
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(5)
    pyautogui.press('tab')
    time.sleep(1)
    pyautogui.typewrite('SM36')
    pyautogui.press('tab')
    time.sleep(1)
    pyautogui.typewrite('SM37')
    pyautogui.hotkey('ctrl', 'tab')
    time.sleep(1)
    pyautogui.typewrite('S_BTCH_ADM')
    pyautogui.press('enter')
    time.sleep(5)
    pyautogui.press('tab')
    time.sleep(1)
    pyautogui.typewrite('Y')
    pyautogui.hotkey('ctrl', 'tab')
    time.sleep(1)
    pyautogui.typewrite('S_BTCH_JOB')
    pyautogui.press('enter')
    time.sleep(5)
    pyautogui.press('tab')
    time.sleep(1)
    pyautogui.typewrite('RELE')
    pyautogui.press('tab')
    time.sleep(1)
    pyautogui.typewrite('DELE')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_11.png'))
    time.sleep(1)
    pyautogui.press('F8')
    time.sleep(5)
    ClickMouse_UP()

    # 截图筛选条件
    pyautogui.press('pageup')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_11.查询结果1.png'))
    pyautogui.press('pagedown')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_11.查询结果2.png'))

    # 完整性截图
    ClickMouse_DOWN()
    pyautogui.hotkey('ctrl', 'shift', 'down')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_11.查询结果3.png'))

    # 导出
    GetExcel_shortcutKey_1()
    pyautogui.typewrite('basis_11')
    GetExcel_shortcutKey_2()

    #返回
    time.sleep(3)
    for i in range(2):
        pyautogui.press('F3')
        time.sleep(1)

def Getbasis_12(save_path):
    setup_pyautogui()
    sub_steps = ["12_密码变更记录", "12_密码策略"]
    state = load_progress(save_path)
    #登录至菜单

    # ---------- 子步骤 12_密码变更记录 ----------
    skip_12_1 = should_skip_sub_step(state, "Getbasis_12", "12_密码变更记录", sub_steps)
    if not skip_12_1:
        time.sleep(1)
        #密码变更记录
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        time.sleep(1)
        pyautogui.typewrite('/nSE16')
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(5)
        clear_input()
        pyautogui.typewrite('PAHI')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_12_PAHI.png'))
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(5)
        for i in range(3):
            pyautogui.press('down')
        time.sleep(1)
        pyautogui.typewrite(AUDIT_START_DATE) #审计开始日期
        time.sleep(1)
        pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite(AUDIT_END_DATE) #审计结束日期
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_12_筛选界面.png'))
        pyautogui.press('F8')
        time.sleep(5)

        # 完整性截图
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_12_密码变更记录首页.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_12_密码变更记录尾页.png'))

        #导出
        for i in range(3):
            pyautogui.hotkey('ctrl', 'tab')
        time.sleep(1)
        GetExcel_pc_1()
        pyautogui.typewrite('basis_12_1')
        GetExcel_pc_2()

        #回退
        pyautogui.press('tab')
        pyautogui.press('enter')
        time.sleep(3)
        for i in range(3):
            pyautogui.press('F3')
            time.sleep(1)

        mark_sub_step_done(save_path, "Getbasis_12", "12_密码变更记录", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 12_密码变更记录")

    # ---------- 子步骤 12_密码策略 ----------
    skip_12_2 = should_skip_sub_step(state, "Getbasis_12", "12_密码策略", sub_steps)
    if not skip_12_2:
        #密码策略
        # 先按ESC确保退出任何残留画面
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        time.sleep(1)
        pyautogui.typewrite('/nSA38')
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(3)
        pyautogui.typewrite('RSPARAM')
        pyautogui.press('F8')
        time.sleep(5)

        #完整性截图
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_12_密码策略首页.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_12_密码策略尾页.png'))

        #导出
        pyautogui.hotkey('ctrl', '/')
        time.sleep(1)
        GetExcel_pc_1()
        pyautogui.typewrite('basis_12_2')
        GetExcel_pc_2()

        #返回
        time.sleep(3)
        for i in range(2):
            pyautogui.press('F3')
            time.sleep(1)

        mark_sub_step_done(save_path, "Getbasis_12", "12_密码策略", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 12_密码策略")





def Getbasis_13(save_path):
    sub_steps = ["13_查看组件版本", "13_USR02"]
    state = load_progress(save_path)

    # ---------- 子步骤 13_查看组件版本 ----------
    skip_13_1 = should_skip_sub_step(state, "Getbasis_13", "13_查看组件版本", sub_steps)
    if not skip_13_1:
        # 先按ESC确保退出任何残留画面
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('alt', 'Y')
        time.sleep(0.5)
        pyautogui.press('A')
        time.sleep(0.5)
        for i in range(2):
            pyautogui.hotkey('ctrl', 'tab')
        time.sleep(1)
        pyautogui.press('tab')
        pyautogui.press('enter')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_13_查看SAP组件版本.png'))

        #返回
        pyautogui.hotkey('ctrl', 'tab')
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(5)
        for i in range(5):
            pyautogui.hotkey('ctrl', 'tab')
        time.sleep(1)
        pyautogui.press('enter')

        mark_sub_step_done(save_path, "Getbasis_13", "13_查看组件版本", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 13_查看组件版本")

    # ---------- 子步骤 13_USR02 ----------
    skip_13_2 = should_skip_sub_step(state, "Getbasis_13", "13_USR02", sub_steps)
    if not skip_13_2:
        #如果SAP_BASIS组件>=732，请执行以下程序，为所有适用的SAP实例提供完整的USR02报告。
        # 先按ESC确保退出任何残留画面
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        time.sleep(1)
        pyautogui.typewrite('/nSE16')
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(3)
        clear_input()
        pyautogui.typewrite('USR02')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_13_USR02.png'))
        pyautogui.press('enter')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_13_筛选.png'))
        pyautogui.press('F8')
        time.sleep(5)

        #完整性截图
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_13_USR02首页.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_13_USR02尾页.png'))

        #导出
        pyautogui.hotkey('ctrl', '/')
        time.sleep(1)
        GetExcel_pc_1()
        pyautogui.typewrite('basis_13')
        GetExcel_pc_2()

        #返回
        pyautogui.hotkey('ctrl', 'tab')
        pyautogui.press('enter')
        time.sleep(3)
        for i in range(3):
            pyautogui.press('F3')

        mark_sub_step_done(save_path, "Getbasis_13", "13_USR02", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 13_USR02")

    '''
    #13.2没写完，有问题，底稿中并没有到这一步
    pyautogui.press('F3')
    time.sleep(1)
    pyautogui.press('F3')
    time.sleep(1)
    pyautogui.hotkey('ctrl', 'tab')
    pyautogui.typewrite('SECPOL')
    '''

def Getbasis_14(save_path):
    setup_pyautogui()
    # 先按ESC确保退出任何残留画面
    for i in range(3):
        pyautogui.press('esc')
        time.sleep(0.5)
    time.sleep(1)
    pyautogui.hotkey('ctrl', '/')
    time.sleep(1)
    pyautogui.typewrite('/nSA38')
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(5)
    pyautogui.typewrite('RSUSR003')
    time.sleep(3)
    pyautogui.hotkey('shift', 'tab')
    time.sleep(0.5)
    pyautogui.press('space')
    time.sleep(0.5)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_14_RSUSR003.png'))
    time.sleep(1)
    pyautogui.press('F8')
    time.sleep(5)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_14_RSUSR003结果1.png'))
    time.sleep(1)
    pyautogui.press('F8')
    time.sleep(5)

    #完整性截图
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_14_RSUSR003_首页1.png'))
    ClickMouse_UP()
    pyautogui.press('pagedown')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_14_RSUSR003_尾页1.png'))
    ClickMouse_DOWN()
    pyautogui.hotkey('ctrl', 'shift', 'down')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_14_RSUSR003_尾页2.png'))
    
    #导出
    GetExcel_shortcutKey_1()
    pyautogui.typewrite('basis_14')
    GetExcel_shortcutKey_2()

    #返回
    time.sleep(3)
    for i in range(3):
        pyautogui.press('F3')


def Getbasis_15(save_path):
    setup_pyautogui()
    sub_steps = ["15_SAP_ALL_NEW", "15_SAP_NEW角色"]
    state = load_progress(save_path)

    # ---------- 子步骤 15_SAP_ALL_NEW ----------
    skip_15_1 = should_skip_sub_step(state, "Getbasis_15", "15_SAP_ALL_NEW", sub_steps)
    if not skip_15_1:
        # 先按ESC确保退出任何残留画面
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        # SUIM-用户-按复杂选择条件选择的用户-按角色/参数文件
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nS_BCE_68001400')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(5)

        for i in range(13):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(5)

        pyautogui.typewrite('SAP_ALL')
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(1)
        pyautogui.press('down')
        time.sleep(1)
        pyautogui.typewrite('SAP_NEW')
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_15.SAP_ALL&SAP_NEW_1.png'))
        time.sleep(1)
        pyautogui.press('F8')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_15.SAP_ALL&SAP_NEW_2.png'))
        pyautogui.press('F8')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_15.SAP_ALL&SAP_NEW_结果_首页.png'))

        #完整性截图
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'down')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_15.SAP_ALL&SAP_NEW_结果_尾页.png'))
        time.sleep(1)

        #导出
        GetExcel_shortcutKey_1()
        pyautogui.typewrite('basis_15.SAP_ALL&SAP_NEW')
        GetExcel_shortcutKey_2()

        #返回
        for i in range(3):
            pyautogui.press('F3')
            time.sleep(1)

        mark_sub_step_done(save_path, "Getbasis_15", "15_SAP_ALL_NEW", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 15_SAP_ALL_NEW")

    # ---------- 子步骤 15_SAP_NEW角色 ----------
    skip_15_2 = should_skip_sub_step(state, "Getbasis_15", "15_SAP_NEW角色", sub_steps)
    if not skip_15_2:
        # 先按ESC确保退出任何残留画面
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        # SUIM-用户-按复杂选择条件选择的用户-按角色/参数文件
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nS_BCE_68001400')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(5)

        for i in range(10):
            pyautogui.press('tab')
        time.sleep(1)
        pyautogui.typewrite('SAP_NEW')
        pyautogui.press('enter')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_15.SAP_NEW角色.png'))
        pyautogui.press('F8')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_15.SAP_NEW_角色结果.png'))

        #返回
        for i in range(2):
            pyautogui.press('F3')
            time.sleep(1)

        mark_sub_step_done(save_path, "Getbasis_15", "15_SAP_NEW角色", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: 15_SAP_NEW角色")
def Getbasis_16(save_path):
    setup_pyautogui()
    # SUIM-更改文档-用户-用于用户-按角色/参数文件
    # 先按ESC确保退出任何残留画面
    for i in range(3):
        pyautogui.press('esc')
        time.sleep(0.5)
    time.sleep(1)
    pyautogui.hotkey('ctrl', '/')
    pyautogui.typewrite('/nS_BCE_68001439')
    time.sleep(1.0)
    pyautogui.press('enter')
    time.sleep(5)

    # 开始日期
    for i in range(7):
        pyautogui.press('down')
    clear_input()
    pyautogui.typewrite(AUDIT_START_DATE)
    pyautogui.press('enter')
    time.sleep(1)

    # 结束日期
    for i in range(5):
        pyautogui.press('down')
    clear_input()
    pyautogui.typewrite(AUDIT_END_DATE)
    pyautogui.press('enter')
    time.sleep(1)

    # 结束时间 23:59:59
    pyautogui.press('down')
    clear_input()
    pyautogui.typewrite('23:59:59')
    pyautogui.press('enter')
    time.sleep(1)

    # 第一组: SAP_NEW + SAP_ALL
    for i in range(7):
        pyautogui.press('down')
    pyautogui.press('enter')
    pyautogui.typewrite('SAP_NEW')
    pyautogui.press('enter')
    time.sleep(1)
    for i in range(2):
        pyautogui.press('down')
    pyautogui.typewrite('SAP_ALL')
    pyautogui.press('enter')
    time.sleep(1)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_16_筛选1.png'))
    time.sleep(1)

    pyautogui.hotkey('ctrl', 'tab')
    pyautogui.press('enter')
    time.sleep(3)

    # 第二组: SAP_NEW + SAP_ALL
    for i in range(6):
        pyautogui.press('down')
    pyautogui.press('enter')
    pyautogui.typewrite('SAP_NEW')
    pyautogui.press('enter')
    time.sleep(1)
    for i in range(2):
        pyautogui.press('down')
    pyautogui.typewrite('SAP_ALL')
    pyautogui.press('enter')
    time.sleep(1)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_16_筛选2.png'))
    time.sleep(1)

    pyautogui.hotkey('ctrl', 'tab')
    pyautogui.press('enter')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_16_筛选3.png'))
    time.sleep(1)

    pyautogui.press('F8')
    time.sleep(5)

    # 完整性截图
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_16_首页.png'))
    ClickMouse_UP()
    pyautogui.press('pagedown')
    time.sleep(1)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_16_尾页1.png'))
    ClickMouse_DOWN()
    pyautogui.hotkey('ctrl', 'shift', 'down')
    time.sleep(3)
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(save_path, 'basis_16_尾页2.png'))
    time.sleep(1)

    # 导出
    GetExcel_shortcutKey_1()
    pyautogui.typewrite('basis_16')
    GetExcel_shortcutKey_2()

    #返回
    for i in range(2):
        pyautogui.press('F3')
        time.sleep(1)

def Getbasis_Info(save_path):
    setup_pyautogui()
    sub_steps = ["Info_T000", "Info_T001"]
    state = load_progress(save_path)
    '''
    # SUIM-用户-按复杂选择条件选择的用户-按复杂选择条件选择的用户-按角色/参数文件
    for i in range(3):
        pyautogui.press('esc')
        time.sleep(0.5)
    time.sleep(1)
    pyautogui.hotkey('ctrl', '/')
    pyautogui.typewrite('/nSE16')
    time.sleep(1.0)
    pyautogui.press('enter')
    time.sleep(5)
    '''

    # ---------- 子步骤 Info_T000 ----------
    skip_info_1 = should_skip_sub_step(state, "Getbasis_Info", "Info_T000", sub_steps)
    if not skip_info_1:
        time.sleep(1)

        # SUIM-用户-按复杂选择条件选择的用户-按复杂选择条件选择的用户-按角色/参数文件
        for i in range(3):
            pyautogui.press('esc')
            time.sleep(0.5)
        time.sleep(1)
        pyautogui.hotkey('ctrl', '/')
        pyautogui.typewrite('/nSE16')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(5)

        clear_input()
        pyautogui.typewrite('T000')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_Info_T000.png'))
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_Info_T000筛选条件.png'))
        time.sleep(1)
        pyautogui.press('F8')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_Info_T000结果.png'))

        # 导出
        for i in range(3):
            pyautogui.hotkey('ctrl', 'tab')
        time.sleep(1)
        GetExcel_pc_1()
        pyautogui.typewrite('basis_Info_T000')
        GetExcel_pc_2()

        pyautogui.press('tab')
        pyautogui.press('enter')

        mark_sub_step_done(save_path, "Getbasis_Info", "Info_T000", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: Info_T000")

    # ---------- 子步骤 Info_T001 ----------
    skip_info_2 = should_skip_sub_step(state, "Getbasis_Info", "Info_T001", sub_steps)
    if not skip_info_2:
        #T001
        time.sleep(1)
        for i in range(2):
            pyautogui.press('F3')
        time.sleep(1)
        clear_input()
        pyautogui.typewrite('T001')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_Info_T001.png'))
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(5)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_Info_T001筛选条件.png'))
        time.sleep(1)
        pyautogui.press('F8')
        time.sleep(5)

        # 完整性截图
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_Info_T001首页.png'))
        ClickMouse_DOWN()
        pyautogui.hotkey('ctrl', 'shift', 'pagedown')
        time.sleep(3)
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.join(save_path, 'basis_Info_T001尾页.png'))

        # 导出
        for i in range(3):
            pyautogui.hotkey('ctrl', 'tab')
        time.sleep(1)
        GetExcel_pc_1()
        pyautogui.typewrite('basis_Info_T001')
        GetExcel_pc_2()

        pyautogui.press('tab')
        pyautogui.press('enter')
        time.sleep(1)

        #返回
        for i in range(3):
            pyautogui.press('F3')
            time.sleep(1)

        mark_sub_step_done(save_path, "Getbasis_Info", "Info_T001", sub_steps)
    else:
        print("[断点续连] 跳过已完成的子步骤: Info_T001")

#配置pyautogui
def setup_pyautogui():
    pyautogui.PAUSE = 1.5
    pyautogui.FAILSAFE = True


def select_steps(all_steps):
    """弹出多选对话框让用户勾选要执行的步骤，返回选中的步骤列表。
    all_steps: [(步骤名称, 步骤函数), ...]
    返回: [(步骤名称, 步骤函数), ...] 保持原始顺序
    """
    root = tk.Tk()
    root.title("选择要执行的步骤")
    root.attributes('-topmost', True)

    # 计算窗口尺寸
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    win_w = 520
    win_h = min(600, screen_h - 100)
    x = (screen_w - win_w) // 2
    y = (screen_h - win_h) // 2
    root.geometry(f"{win_w}x{win_h}+{x}+{y}")

    # 提示标签
    lbl = tk.Label(root, text="请勾选需要执行的步骤（默认全选）：",
                   font=("微软雅黑", 11))
    lbl.pack(pady=(10, 5))

    # 按钮框架
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=(0, 5))

    # 存储每个步骤对应的 BooleanVar
    vars_list = []

    # 滚动框架
    canvas = tk.Canvas(root, borderwidth=0)
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas)

    canvas.configure(yscrollcommand=scrollbar.set)
    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # 只绑定到 canvas 和 scroll_frame，避免全局绑定污染
    canvas.bind("<MouseWheel>", _on_mousewheel)
    scroll_frame.bind("<MouseWheel>", _on_mousewheel)

    # 创建复选框
    for i, (name, func) in enumerate(all_steps):
        var = tk.BooleanVar(value=True)  # 默认全选
        cb = tk.Checkbutton(scroll_frame, text=f"{i + 1}. {name}",
                            variable=var, font=("微软雅黑", 10),
                            anchor="w")
        cb.pack(fill="x", padx=5, pady=1)
        vars_list.append((var, name, func))

    # 全选 / 取消全选 按钮
    def select_all():
        for var, _, _ in vars_list:
            var.set(True)

    def deselect_all():
        for var, _, _ in vars_list:
            var.set(False)

    tk.Button(btn_frame, text="全选", command=select_all,
              font=("微软雅黑", 10), width=10).pack(side="left", padx=5)
    tk.Button(btn_frame, text="取消全选", command=deselect_all,
              font=("微软雅黑", 10), width=10).pack(side="left", padx=5)

    # 结果容器
    result = {"selected": None}

    def on_confirm():
        selected = [(name, func) for var, name, func in vars_list if var.get()]
        if not selected:
            messagebox.showwarning("提示", "至少需要选择一个步骤！", parent=root)
            return
        result["selected"] = selected
        root.quit()
        root.destroy()

    def on_cancel():
        root.quit()
        root.destroy()

    # 确定/取消按钮 — 必须在 canvas 之前 pack，否则会被 expand 的 canvas 挤出窗口
    action_frame = tk.Frame(root)
    action_frame.pack(side="bottom", pady=(5, 10))
    tk.Button(action_frame, text="确定执行", command=on_confirm,
              font=("微软雅黑", 11), width=12, bg="#4CAF50", fg="white").pack(side="left", padx=10)
    tk.Button(action_frame, text="取消退出", command=on_cancel,
              font=("微软雅黑", 11), width=12, bg="#f44336", fg="white").pack(side="left", padx=10)

    canvas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(0, 10))
    scrollbar.pack(side="right", fill="y", padx=(0, 5), pady=(0, 10))

    root.protocol("WM_DELETE_WINDOW", on_cancel)

    # 确保窗口获得焦点
    root.focus_force()
    root.mainloop()

    return result["selected"]


def main():
    show_input_reminder()

    # 1.5 用户自定义日期参数
    input_dates()

    # 2. 选择保存路径
    save_path = select_save_path()
    time.sleep(3)

    # ==================== 断点续连核心逻辑 ====================
    # 定义全部可用步骤列表：每个元素为 (步骤名称, 步骤函数)
    all_steps = [
        ("Getbasis_1_T000", Getbasis_1_T000),
        ("Getbasis_1_table_a", Getbasis_1_table_a),
        ("Getbasis_1_table_b", Getbasis_1_table_b),
        #("Getbasis_2_2", Getbasis_2_2), 无权限
        ("Getbasis_4", Getbasis_4),
        ("Getbasis_5", Getbasis_5),
        ("Getbasis_6", Getbasis_6),
        ("Getbasis_7", Getbasis_7),
        ("Getbasis_8_1", Getbasis_8_1),
        ("Getbasis_8_2", Getbasis_8_2),
        ("Getbasis_9", Getbasis_9),
        ("Getbasis_10", Getbasis_10),
        ("Getbasis_11", Getbasis_11),
        ("Getbasis_12", Getbasis_12),
        ("Getbasis_13", Getbasis_13),
        ("Getbasis_14", Getbasis_14),
        ("Getbasis_15", Getbasis_15),
        ("Getbasis_16", Getbasis_16), #测试账号无结果
        ("Getbasis_Info", Getbasis_Info),
        ("GetTB", GetTB),
        ("GetJE", GetJE),
    ]

    # 让用户选择要执行的步骤（默认全选）
    steps = select_steps(all_steps)
    if steps is None:
        # 用户点击"取消退出"
        print("[用户取消] 未选择任何步骤，程序退出。")
        return

    # 尝试读取上次执行状态
    state = load_progress(save_path)
    start_index = 0

    if state and state.get("status") == "failed":
        # 上次执行失败，询问是否从断点继续
        # 检查断点步骤是否在用户当前选中的步骤列表中
        saved_step_name = state["step_name"]
        matching_indices = [idx for idx, (name, _) in enumerate(steps) if name == saved_step_name]
        if matching_indices:
            if ask_resume(state["step_name"], state.get("sub_step")):
                start_index = matching_indices[0]
                sub_info = f" 子步骤({state.get('sub_step')})" if state.get("sub_step") else ""
                print(f"[断点续连] 从步骤 {start_index + 1}/{len(steps)} ({steps[start_index][0]}{sub_info}) 继续执行...")
            else:
                print("[断点续连] 用户选择从头开始，清除旧进度...")
                clear_progress(save_path)
                state = None
        else:
            # 断点步骤不在用户选中的步骤中，清除旧进度
            print(f"[断点续连] 上次断点步骤({saved_step_name})不在当前选中的步骤中，从头执行。")
            clear_progress(save_path)
            state = None
    elif state and state.get("status") == "running":
        # 上次异常退出（直接崩溃）
        saved_step_name = state["step_name"]
        matching_indices = [idx for idx, (name, _) in enumerate(steps) if name == saved_step_name]
        if matching_indices:
            if ask_resume(state["step_name"], state.get("sub_step")):
                start_index = matching_indices[0]
                sub_info = f" 子步骤({state.get('sub_step')})" if state.get("sub_step") else ""
                print(f"[断点续连] 从步骤 {start_index + 1}/{len(steps)} ({steps[start_index][0]}{sub_info}) 继续执行...")
            else:
                clear_progress(save_path)
                state = None
        else:
            print(f"[断点续连] 上次断点步骤({saved_step_name})不在当前选中的步骤中，从头执行。")
            clear_progress(save_path)
            state = None

    # 依次执行各步骤
    try:
        for i in range(start_index, len(steps)):
            step_name, step_func = steps[i]
            print(f"[执行中] 步骤 {i + 1}/{len(steps)}: {step_name}")

            # 先保存状态为"运行中"，记录当前步骤索引。
            # 注意：如果 state 里已有 sub_step（表示正在断点续连），
            # 保留 sub_step 让函数内部自行判断跳过逻辑。
            existing_sub = state.get("sub_step") if state and state.get("step_name") == step_name else None
            save_progress(save_path, i, step_name, sub_step=existing_sub, status="running")

            # 执行该步骤
            step_func(save_path)

            # 该大步骤已完成，清除可能残留的 sub_step
            if state and state.get("step_name") == step_name:
                state["sub_step"] = None

        # 全部成功完成后，清除进度文件
        clear_progress(save_path)
        messagebox.showinfo("执行完毕", "所有选中的步骤已成功执行完毕！")

    except Exception as e:
        # 捕获异常，记录失败状态
        current_step_name = steps[i][0] if 'i' in locals() else "未知"
        current_index = i if 'i' in locals() else start_index

        # 尽量保留已有的 sub_step（函数内部可能已经设置了更细粒度的断点）
        existing_state = load_progress(save_path)
        existing_sub = existing_state.get("sub_step") if existing_state and existing_state.get("step_name") == current_step_name else None
        save_progress(save_path, current_index, current_step_name, sub_step=existing_sub, status="failed")

        # 打印错误信息到控制台
        print(f"\n[执行失败] 步骤 {current_step_name} 发生异常：")
        traceback.print_exc()

        # 弹窗提示用户
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        sub_info = f" 子步骤({existing_sub})" if existing_sub else ""
        messagebox.showerror(
            "执行中断",
            f"程序在执行步骤【{current_step_name}】{sub_info}时发生错误，已自动保存断点。\n\n"
            f"错误摘要：{str(e)}\n\n"
            f"下次运行时，程序将询问是否从该断点继续执行。\n"
            f"进度文件路径：{get_state_file_path(save_path)}"
        )
        root.destroy()
        raise
    # =========================================================

if __name__ == "__main__":
    main()

