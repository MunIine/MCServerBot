import win32gui
import win32process
import psutil

def find_console_hwnd_by_title(title_substring):
    def enum_windows_proc(hwnd, results):
        window_title = win32gui.GetWindowText(hwnd)
        if title_substring.lower() in window_title.lower():
            results.append(hwnd)

    results = []
    win32gui.EnumWindows(enum_windows_proc, results)
    return results

def get_command_line_by_hwnd(hwnd):
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        command_line = process.cmdline()
        return command_line[2]
    
    except Exception as e:
        print(f"Ошибка: {e}")
        return None

def check(PATH):
    console_title_substring = 'C:\Windows\System32\cmd.exe'
    hwnds = find_console_hwnd_by_title(console_title_substring)

    for hwnd in hwnds:
        path = get_command_line_by_hwnd(hwnd);
        if path.strip() == PATH.strip():
            return hwnd
            
    return None