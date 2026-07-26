# ASMR Cleaner GUI 代码详解

> 写给想看懂这个项目 UI 代码的人。不需要任何前置知识，一行一行拆给你看。

---

## 先搞清楚：这个软件的 UI 是怎么组织起来的

整个软件的界面是一个**大窗口**，里面从上到下塞了 7 个**区域**，像搭积木：

```
┌────────────────────────────────┐
│  菜单栏 (设置 / 帮助)           │  ← _build_menu()
├────────────────────────────────┤
│  📁 输入文件   [________] [浏览]│  ← _build_input_frame()
├────────────────────────────────┤
│  文件信息面板                   │  ← _build_file_info()
│  格式: WAV 时长: 01:23:45      │
│  采样率: 48kHz 位深: 16bit     │
├────────────────────────────────┤
│  处理参数                       │  ← _build_params_frame()
│  静音阈值 [-55] dB  ──○─── ?   │
│  最小时长 [5.0] 秒  ──○─── ?   │
│  淡入淡出 [30] 毫秒 ──○─── ?   │
│  输出格式 [FLAC ▼]             │
├────────────────────────────────┤
│  [▶ 开始处理]    [📋 查看日志]  │  ← _build_buttons()
├────────────────────────────────┤
│  阶段指示器                     │  ← _build_stage_indicator()
│  ⬜ 加载 → ⬜ 分析 → ...        │
├────────────────────────────────┤
│  进度条 ████████░░░░ 67%       │  ← _build_progress()
│  已找到静音区: 3 段            │
├────────────────────────────────┤
│  状态栏: 就绪                   │  ← _build_statusbar()
└────────────────────────────────┘
```

每个 `_build_xxx()` 方法**只管自己那一块区域**，互不干扰。这是最重要的设计原则。

---

## 文件分工（一共 5 个文件）

打开 `gui/` 文件夹，你会看到：

| 文件 | 干什么的 | 类比 |
|---|---|---|
| `main_window.py` | 主窗口，把所有东西拼起来 | 房子的框架+地板 |
| `widgets.py` | 两个自定义控件 | 预制家具 |
| `file_info.py` | 文件信息面板 | 门牌号 |
| `log_viewer.py` | 日志查看弹窗 | 抽屉 |
| `__init__.py` | 空文件，标记"这是一个 Python 包" | 门牌 |

### 为什么拆成 5 个文件而不是写一个 2000 行的大文件？

因为人脑一次只能装 200 行代码。拆开后：
- 改按钮样式？只动 `main_window.py`
- 改参数滑块？只动 `widgets.py`
- 改日志弹窗？只动 `log_viewer.py`

**互不影响**。这就是"模块化"——这个项目最重要的设计原则。

---

## 文件 1：`main_window.py`（主窗口，~600 行）

这是最大的文件，但别怕——它的结构非常清晰。

### 第一块：导入依赖（第 1-17 行）

```python
import os, gc, queue, threading       # Python 自带工具
import tkinter as tk                  # 窗口库
from tkinter import ttk, filedialog, messagebox  # tkinter 的子模块

from asmr_cleaner.i18n import t       # 翻译函数 t("key") → 当前语言的文字
from asmr_cleaner import settings     # 读写配置文件
from asmr_cleaner.core import process # 核心处理函数（引擎层）
from gui.widgets import ...           # 自定义控件
from gui.file_info import ...         # 文件信息面板
from gui.log_viewer import ...        # 日志查看器
```

**关键规则**：`from asmr_cleaner.xxx import yyy` —— GUI 只**调用**引擎层，绝不碰引擎的内部实现。

### 第二块：类定义和初始化（第 20-78 行）

```python
class MainWindow(tk.Tk):   # 继承 tkinter 的窗口类
    def __init__(self):
        super().__init__()  # 先执行父类的初始化（创建窗口）

        # 1. 加载用户设置（上次用的语言、参数等）
        self._app_settings = settings.load()

        # 2. 设置窗口标题和最小尺寸
        self.title(t("app.title"))     # t("app.title") → "ASMR Cleaner"
        self.minsize(800, 600)         # 最小 800x600 像素

        # 3. 初始化内部变量
        self._input_path = None        # 当前选中的文件路径
        self._processing = False       # 是否正在处理中
        self._progress_queue = queue.Queue()  # 线程通信用的队列

        # 4. 设置主题（clam 是 ttk 最好看的内置主题）
        style = ttk.Style()
        style.theme_use("clam")

        # 5. 搭建界面——按顺序从上到下
        self._build_menu()             # 菜单栏
        self._build_input_frame()      # 文件选择区
        self._build_file_info()        # 文件信息面板
        self._build_params_frame()     # 参数设置区
        self._build_buttons()          # 按钮区
        self._build_stage_indicator()  # 阶段指示器
        self._build_progress()         # 进度条
        self._build_statusbar()        # 状态栏

        # 6. 注册"关闭窗口"的回调
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # 7. 启动定时器，每 100ms 检查一次后台线程的消息
        self._poll_progress()
```

### 第三块：菜单栏（第 84-153 行）

```python
def _build_menu(self):
    menubar = tk.Menu(self)                      # 创建菜单栏
    self.config(menu=menubar)                    # 挂到窗口上

    settings_menu = tk.Menu(menubar, tearoff=0)  # 设置菜单
    menubar.add_cascade(label="设置", menu=settings_menu)

    lang_menu = tk.Menu(settings_menu, tearoff=0)  # 子菜单：语言
    settings_menu.add_cascade(label="语言", menu=lang_menu)
    lang_menu.add_radiobutton(label="中文", ...)   # 单选按钮
    lang_menu.add_radiobutton(label="English", ...)
```

`tearoff=0` 的意思是"不允许把菜单撕下来变成浮动窗口"——这是 tkinter 的老特性，关掉。

### 第四块：输入文件区（第 175-186 行）

```python
def _build_input_frame(self):
    frame = ttk.LabelFrame(self, text="输入文件")  # 带标题的框
    frame.pack(fill=tk.X, padx=10, pady=5)        # 横向填满，留边距

    self._input_var = tk.StringVar()               # 存储文件路径的变量
    entry = ttk.Entry(frame, textvariable=self._input_var, state="readonly")
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True)  # 输入框，左边，横向拉伸

    browse_btn = ttk.Button(frame, text="浏览...", command=self._browse_file)
    browse_btn.pack(side=tk.RIGHT)                 # 按钮，右边
```

**tkinter 布局核心概念**：`.pack()` 是三种布局方式之一，参数含义：
- `side=tk.LEFT`：往左靠
- `fill=tk.X`：横向撑满
- `expand=True`：有多余空间就占掉
- `padx=10`：左右留 10 像素空白

### 第五块：点击"浏览"按钮后发生了什么（第 319-347 行）

```python
def _browse_file(self):
    # 1. 弹出文件选择对话框
    path = filedialog.askopenfilename(
        title="输入文件",
        filetypes=[("音频文件", "*.wav *.mp3 *.flac"), ("所有文件", "*.*")]
    )
    if not path:        # 用户点了取消
        return

    # 2. 保存路径
    self._input_path = path
    self._input_var.set(path)

    # 3. 记住上次打开的目录，存到设置文件
    self._app_settings["last_input_dir"] = os.path.dirname(path)
    settings.save(self._app_settings)

    # 4. 更新文件信息面板（调用 ffprobe 读元信息）
    self._file_info.show_file(path)

    # 5. 启用"开始处理"按钮
    self._start_btn.configure(state=tk.NORMAL)
```

### 第六块：点击"开始处理"后发生了什么（第 353-408 行）

这是**最关键的流程**：

```python
def _start_processing(self):
    # 1. 安全检查
    if self._processing:          # 正在处理中，别重复点
        return
    if not self._input_path:      # 没选文件
        return

    # 2. 大文件警告（>2GB 弹窗确认）
    file_size = os.path.getsize(self._input_path)
    if file_size > 2 * 1024 * 1024 * 1024:
        ok = messagebox.askokcancel("大文件警告", "文件较大...继续？")
        if not ok: return

    # 3. 构造输出路径：原文件名_cleaned.flac
    base, ext = os.path.splitext(self._input_path)
    output_path = f"{base}_cleaned.{self._format_var.get()}"

    # 4. 如果输出文件已存在，弹窗确认是否覆盖
    if os.path.exists(output_path):
        ok = messagebox.askokcancel("文件已存在", "是否覆盖？")
        if not ok: return

    # 5. 从三个滑块读取参数
    params = {
        "threshold_db": float(self._threshold_slider.get()),
        "min_silence_sec": float(self._min_silence_slider.get()),
        "crossfade_ms": float(self._crossfade_slider.get()),
        "output_format": self._format_var.get(),
    }

    # 6. 禁用按钮、启动动画、显示状态
    self._processing = True
    self._start_btn.configure(text="处理中...", state=tk.DISABLED)
    self._progress_bar.configure(mode='indeterminate')  # 来回滚动的动画条
    self._progress_bar.start(20)
    self._status_var.set("正在加载... (512 MB)")

    # 7. 启动后台线程（关键！）
    self._worker_thread = threading.Thread(
        target=self._worker_run,
        args=(self._input_path, output_path, params),
        daemon=True,
    )
    self._worker_thread.start()
```

### 第七块：为什么需要后台线程？（第 410-434 行）

**问题**：如果直接在主线程调用 `process()`，处理大文件时要等几十秒——整个窗口会变成"白屏"，Windows 会标记"无响应"。

**解决**：把重活扔到后台线程，主线程继续刷新界面：

```python
def _worker_run(self, input_path, output_path, params):
    """这个方法在后台线程运行，绝对不能碰任何 tkinter 控件"""
    try:
        def progress_cb(stage, frac, extra):
            # 唯一能做的事：往队列里塞消息
            self._progress_queue.put(("progress", stage, frac, extra))

        result = process(           # ← 这里会卡几十秒，但在后台线程，不影响界面
            input_path, output_path,
            params["threshold_db"],
            params["min_silence_sec"],
            params["crossfade_ms"],
            progress_callback=progress_cb,
            output_format=params["output_format"],
        )
        self._progress_queue.put(("done", result))  # 处理完成
    except Exception as e:
        self._progress_queue.put(("error", str(e)))  # 出错了
```

### 第八块：主线程怎么知道后台发生了什么？（第 436-457 行）

每 100 毫秒，主线程检查队列：

```python
def _poll_progress(self):
    try:
        while True:
            msg = self._progress_queue.get_nowait()  # 非阻塞取消息
            if msg[0] == "progress":
                self._update_progress_ui(...)       # 更新进度条
            elif msg[0] == "done":
                self._on_processing_done(result)    # 显示完成信息
            elif msg[0] == "error":
                self._on_processing_error(msg)      # 显示错误
    except queue.Empty:
        pass  # 队列空了，没关系，100ms 后再看

    self.after(100, self._poll_progress)  # 100ms 后再调用自己
```

`after(100, func)` 是 tkinter 的定时器——100 毫秒后执行 `func`。这里它让 `_poll_progress` 每秒检查 10 次队列。

**一句话总结线程模型**：后台线程干活 → 往队列发消息 → 主线程每 100ms 收消息 → 更新界面。两边各干各的，不打架。

### 第九块：处理完成后（第 501-541 行）

```python
def _on_processing_done(self, result):
    self._processing = False                           # 解锁
    self._start_btn.configure(text="▶ 开始处理", state=tk.NORMAL)  # 恢复按钮
    self._stage_indicator.set_all_done()               # 5 个阶段全打勾
    self._progress_bar.configure(value=100)            # 进度条 100%

    summary = result["summary"]
    removed = result["removed_segments"]

    if len(removed) == 0:
        self._status_var.set("✅ 未发现长静音区，无需处理")
    elif summary["reduction_percent"] > 95:
        messagebox.showwarning("整个文件几乎都是静音，确认是否选错了文件")
    else:
        self._status_var.set("✅ 处理完成！")
        # 显示切除详情：切除 3 段，共 8m 15s，耗时 12.3s
        self._progress_detail.configure(text=...)
```

---

## 文件 2：`widgets.py`（自定义控件，~149 行）

### LabeledSlider（参数滑块）

这个控件把**标签 + 滑动条 + 数字框 + 单位 + 帮助按钮**打包成一个整体。

```python
class LabeledSlider(ttk.Frame):
    def __init__(self, parent, label_key, unit_key, tooltip_key,
                 from_, to, default, step):
        # label_key 和 unit_key 是 i18n 的 key，比如 "label.threshold"
        from asmr_cleaner.i18n import t

        self.label = ttk.Label(self, text=t(label_key) + ":")     # "静音阈值:"
        self.scale = ttk.Scale(self, from_=-90, to=-20, ...)      # 滑动条
        self.spinbox = ttk.Spinbox(self, from_=-90, to=-20, ...)  # 数字框
        self.unit_label = ttk.Label(self, text=t(unit_key))       # "dB"
        self.help_btn = ttk.Label(self, text="?", ...)            # 帮助按钮
```

**双向同步**：拖动滑动条 → 数字框跟着变；手动输数字 → 滑动条跟着动。这是通过共享一个 `tk.DoubleVar` 实现的——它像一个"共享内存"，任何一方改它，另一方自动感知。

```python
self._value = tk.DoubleVar(value=-55)   # 初始值 -55
self.scale = ttk.Scale(variable=self._value)    # 滑动条绑这个变量
self.spinbox = ttk.Spinbox(textvariable=self._value)  # 数字框也绑这个变量
```

### StageIndicator（处理阶段指示器）

5 个文字节点，中间用箭头连起来。`set_stage(2)` 表示当前在第 3 步（从 0 开始数）：
- 节点 0、1 → 绿色 ✅（已完成）
- 节点 2 → 蓝色 > （当前正在做）
- 节点 3、4 → 灰色 ⬜（还没开始）

```python
def set_stage(self, stage_index):
    for i, lbl in enumerate(self._labels):
        base = self._base_labels[i]   # 原始文字，如 "加载"
        if i < stage_index:
            lbl.configure(text=f"✅ {base}", foreground="green")
        elif i == stage_index:
            lbl.configure(text=f"> {base}", foreground="blue")
        else:
            lbl.configure(text=f"⬜ {base}", foreground="gray")
```

---

## 文件 3：`file_info.py`（文件信息面板，~97 行）

```python
class FileInfoPanel(ttk.LabelFrame):
    def show_file(self, filepath):
        info = get_audio_info(filepath)  # ← 调用引擎层，调用 ffprobe
        # info 是一个字典：{"format": "WAV", "sample_rate": 48000, ...}

        # 把每个字段填到对应的标签上
        self._value_labels["info.format"].configure(text=info["format"])
        self._value_labels["info.duration"].configure(text=_format_duration(...))
        # ...
```

**布局方式**：用了 `grid()` 而不是 `pack()`。grid 是按行列定位：
```python
lbl.grid(row=i // 2, column=(i % 2) * 2)  # 每行两列，自动换行
```

结果是 3 行 × 2 列的网格布局（6 个信息字段）。

**辅助格式化函数**：
```python
def _format_duration(seconds):   # 3661 → "1:01:01"
def _format_size(bytes_val):     # 512000000 → "488.3 MB"
def _format_channels(ch):        # 2 → "立体声"
```

---

## 文件 4：`log_viewer.py`（日志查看弹窗，~240 行）

这个文件有三个部分：

### 入口函数（给别人调的）
```python
def show_log_viewer(parent, log_path):
    data = read_log(log_path)    # 读 JSON 日志
    _LogDialog(parent, data, log_path)  # 打开弹窗

def show_log_selector(parent, input_path):
    logs = find_logs_for_file(input_path)  # 搜索日志文件
    if len(logs) == 1:
        show_log_viewer(parent, logs[0])  # 只有一份，直接打开
    else:
        _LogSelectionDialog(parent, logs)  # 多份，让用户选
```

### _LogDialog（主要弹窗）
用 `tk.Toplevel` 创建独立窗口。里面包含：
1. 摘要信息（输入文件、输出文件、处理时间、时长、减少比例）
2. 切除段详情表格（`ttk.Treeview`——类似 Excel 的列表控件）
3. 处理参数
4. 三个按钮：打开文件位置、复制为文本、关闭

### _LogSelectionDialog（选择弹窗）
只有一个 `tk.Listbox`，列出多个日志文件的修改时间，双击打开。

---

## 文件 5：`i18n.py`（国际化，~250 行）

这是整个项目"语言切换"的基础。原理极简单：

```python
STRINGS = {
    "zh": {"btn.start": "▶ 开始处理", "status.ready": "就绪", ...},
    "en": {"btn.start": "▶ Start",   "status.ready": "Ready", ...},
}

def t(key):
    lang = get_language()                      # 当前是 "zh" 还是 "en"
    return STRINGS[lang].get(key, key)          # 找不到就用 key 本身
```

**所有 GUI 代码里只调 `t("key")`，绝不硬编码文字。** 所以要加英文支持，只需在 `STRINGS["en"]` 里加一行翻译，一行代码都不用改。

---

## 数据流向图

```
用户点击"浏览"                  用户点击"开始处理"
    │                                │
    ▼                                ▼
_browse_file()                 _start_processing()
    │                                │
    ├─ filedialog 弹窗               ├─ 读参数（三个滑块的 get()）
    ├─ 存路径                        ├─ 禁用按钮 + 动画条
    └─ file_info.show_file()         └─ 启动后台线程 ─────────┐
         │                                                    │
         └─ get_audio_info()  ←── ffprobe 读元信息            ▼
                                                _worker_run() [后台线程]
                                                     │
                                                     └─ process() ←── 引擎层
                                                          │
                                                          ├─ audio_io.load_audio()
                                                          ├─ silence_detector.detect_silence()
                                                          ├─ _crossfade()
                                                          ├─ audio_io.save_audio()
                                                          └─ log_writer.write_log()
                                                          │
                                                    发消息到队列
                                                          │
                              ┌───────────────────────────────┘
                              ▼
                    _poll_progress() [主线程，每 100ms]
                         │
                         ├─ "progress" → 更新进度条 + 阶段指示器
                         ├─ "done"     → 显示完成 + 恢复按钮
                         └─ "error"    → 弹窗报错
```

---

## 常见修改指南

### 想改窗口大小？
`main_window.py` 第 50 行的 `self.minsize(800, 600)`

### 想加一个新参数（比如"输出采样率"）？
1. `widgets.py` 不需要改——`LabeledSlider` 本身就是通用控件
2. `main_window.py` 的 `_build_params_frame()` 里加一行 `LabeledSlider(...)`
3. `_start_processing()` 里把它的值加入 `params` 字典
4. `core.py` 的 `process()` 里接收并使用这个新参数

### 想换皮肤/颜色？
`main_window.py` 第 62 行：`style.theme_use("clam")` 改成 `"vista"` / `"winnative"` / `"alt"` / `"classic"`

### 想加暗色模式？
tkinter 原生不支持，需要换 ttk 主题包（如 `ttkbootstrap`），或者用 `tkinter.Tk` 的 `configure(bg='#1e1e1e')` 手动设置——但 ttk 控件不太听这套。目前的最佳方案是换到 `ttkbootstrap` 库（v2 可以考虑）。
