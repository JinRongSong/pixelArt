import tkinter as tk
from tkinter import filedialog
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
from tkinter import filedialog, messagebox

# 參數
GRID_SIZE = 64        # 像素化格子數 (可調整)
NUM_COLORS = 14       # 使用幾種顏色 (可調整)
CELL_SIZE = 10        # 每格大小(px)

# 全域變數
current_color_id = 0
color_palette = []
correct_map = []
# -4次添加-
color_block_refs = []  # 儲存 (canvas, rect_id)
selected_color_index = None  # 當前選中的顏色編號
#26/02/06新增
numbers_visible = True   # 數字目前是否顯示
#26/02/07新增
fill_mode_region = True   # True=局部填充(相鄰同數字), False=單個填充

# -1次添加-
def flood_fill(x, y, target_number):
    stack = [(x, y)]
    visited = set()

    while stack:
        cx, cy = stack.pop()
        if (cx, cy) in visited:
            continue
        visited.add((cx, cy))
        # -2次替換-
        if 0 <= cx < len(correct_map[0]) and 0 <= cy < len(correct_map):
        # -2次換掉-
        # if 0 <= cx < GRID_SIZE and 0 <= cy < GRID_SIZE:
            if correct_map[cy][cx] == target_number:
                # 上色
                canvas.create_rectangle(
                    cx * CELL_SIZE, cy * CELL_SIZE,
                    (cx + 1) * CELL_SIZE, (cy + 1) * CELL_SIZE,
                    fill=color_palette[current_color_id],
                    outline="gray"
                )
                
                #26/02/06替换后
                create_number_text(cx, cy, correct_map[cy][cx])

                # 檢查四個方向
                stack.extend([
                    (cx+1, cy),
                    (cx-1, cy),
                    (cx, cy+1),
                    (cx, cy-1)
                ]) 

#26/02/07新增
def fill_single(x, y):
    """只填一個格子"""
    if 0 <= y < len(correct_map) and 0 <= x < len(correct_map[0]):
        val = correct_map[y][x]
        if val is None:
            return

        canvas.create_rectangle(
            x * CELL_SIZE, y * CELL_SIZE,
            (x + 1) * CELL_SIZE, (y + 1) * CELL_SIZE,
            fill=color_palette[current_color_id],
            outline="gray"
        )
        create_number_text(x, y, val)   # 你前面已加過這個函數


def toggle_fill_mode():
    global fill_mode_region
    fill_mode_region = not fill_mode_region

    if fill_mode_region:
        fill_mode_btn.config(text="填色模式：局部填充")
    else:
        fill_mode_btn.config(text="填色模式：單個填充")

# -1次替換-
def on_canvas_click(event):
    x = event.x // CELL_SIZE
    y = event.y // CELL_SIZE
    # -2次替換-
    if 0 <= y < len(correct_map) and 0 <= x < len(correct_map[0]):
    # -2次換掉-
    # if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
        target_number = correct_map[y][x]
        
        #26/02/07替换后
        if target_number is None:
            return

        if fill_mode_region:
            flood_fill(x, y, target_number)   # 原本行為：相鄰同數字一起填
        else:
            fill_single(x, y) 

def pad_correct_map_to_square(correct_map):
    h = len(correct_map)
    w = len(correct_map[0])
    size = max(w, h)

    if w < size:
        total_pad = size - w
        left_pad = total_pad // 2
        right_pad = total_pad - left_pad
        for row in correct_map:
            row[:0] = [None] * left_pad
            row.extend([None] * right_pad)

    if h < size:
        total_pad = size - h
        top_pad = total_pad // 2
        bottom_pad = total_pad - top_pad
        empty_row = [None] * size
        for _ in range(top_pad):
            correct_map.insert(0, empty_row[:])
        for _ in range(bottom_pad):
            correct_map.append(empty_row[:])



def process_image(image_path):
    global color_palette, correct_map

    # Step 1: 載入並壓縮圖片
    img = Image.open(image_path).convert("RGB")
    target_w, target_h = img.size
    cell_w = GRID_SIZE
    cell_h = int(GRID_SIZE * target_h / target_w)
    small_img = img.resize((cell_w, cell_h), Image.NEAREST)
    pixels = np.array(small_img).reshape(-1, 3)

    # Step 2: 使用 KMeans 做色彩分類
    try:
        n_colors = min(NUM_COLORS, len(pixels))  # 安全處理：不能比像素多
        kmeans = KMeans(n_clusters=n_colors, random_state=42).fit(pixels)
        labels = kmeans.labels_
        palette = kmeans.cluster_centers_.astype(int)
    except Exception as e:
        tk.messagebox.showerror("錯誤", f"圖片處理失敗：\n{e}")
        return

    # Step 3: 設定顏色表與正確答案地圖
    color_palette.clear()
    color_palette.extend([f'#{r:02x}{g:02x}{b:02x}' for r, g, b in palette])
    correct_map.clear()
    correct_map.extend(labels.reshape((cell_h, cell_w)).tolist())

    # Step 4: 補成正方形畫布（空格補 None）
    pad_correct_map_to_square(correct_map)

    # Step 5: 繪製像素畫格子
    #26/02/06替换后
    cell_h = len(correct_map)
    cell_w = len(correct_map[0])
    auto_fit_cell_size(cell_w, cell_h)
    draw_number_grid()

    # Step 6: 畫出顏色選擇器（兩欄排列）
    for widget in color_frame.winfo_children():
        widget.destroy()

    max_columns = 2
    SQUARE_SIZE = 128
    color_block_refs.clear()

    for i, color in enumerate(color_palette):
        row = i // max_columns
        col = i % max_columns

        c = tk.Canvas(color_frame, width=SQUARE_SIZE, height=SQUARE_SIZE, highlightthickness=1)
        c.grid(row=row, column=col, padx=0, pady=0)

        rect_id = c.create_rectangle(0, 0, SQUARE_SIZE, SQUARE_SIZE, fill=color, outline="black", width=2)
        c.create_text(SQUARE_SIZE // 2, SQUARE_SIZE // 2, text=str(i), fill="white", font=("Arial", 10))

        c.bind("<Button-1>", lambda event, i=i: choose_color(i))
        color_block_refs.append((c, rect_id))

# -4次添加-
def choose_color(i):
    global current_color_id, selected_color_index
    current_color_id = i

    # 恢復前一個的邊框
    if selected_color_index is not None:
        prev_canvas, prev_rect = color_block_refs[selected_color_index]
        prev_canvas.itemconfig(prev_rect, outline="black", width=2)

    # 更新目前選中的邊框
    canvas_i, rect_id = color_block_refs[i]
    canvas_i.itemconfig(rect_id, outline="white", width=5)

    selected_color_index = i  # 更新當前選擇記錄


def open_file():
    file_path = filedialog.askopenfilename(filetypes=[
        ("Image files", "*.jpg *.png *.jpeg *.bmp *.gif"),
        ("All files", "*.*")
    ])
    if file_path:
        process_image(file_path)

# -5次添加-
def fill_all():
    cell_h = len(correct_map)
    cell_w = len(correct_map[0])
    for y in range(cell_h):
        for x in range(cell_w):
            color_id = correct_map[y][x]
            if color_id is None:
                continue  # 跳過空白格

            canvas.create_rectangle(
                x * CELL_SIZE, y * CELL_SIZE,
                (x + 1) * CELL_SIZE, (y + 1) * CELL_SIZE,
                fill=color_palette[color_id],
                outline="gray"
            )
            #26/02/06替换后
            create_number_text(x, y, color_id)
            
#26/02/06替换后
def apply_settings(new_grid, new_colors, new_cell):
    global GRID_SIZE, NUM_COLORS, CELL_SIZE
    GRID_SIZE = new_grid
    NUM_COLORS = new_colors
    CELL_SIZE = new_cell

    if correct_map and len(correct_map) > 0 and len(correct_map[0]) > 0:
        map_h = len(correct_map)
        map_w = len(correct_map[0])
        auto_fit_cell_size(map_w, map_h)
        draw_number_grid()
    else:
        # 尚未載入圖片時，用預設比例先顯示
        map_w = GRID_SIZE
        map_h = int(GRID_SIZE * 1.5)
        auto_fit_cell_size(map_w, map_h)
        canvas.delete("all")
        canvas.config(width=map_w * CELL_SIZE, height=map_h * CELL_SIZE)

    print(f"新設定 -> GRID_SIZE: {GRID_SIZE}, NUM_COLORS: {NUM_COLORS}, CELL_SIZE: {CELL_SIZE}")

def open_settings_window():
    settings_win = tk.Toplevel(root)
    settings_win.title("參數設定")
    settings_win.geometry("300x300")

    tk.Label(settings_win, text="寬度格子數 (GRID_SIZE)").pack()
    grid_slider = tk.Scale(settings_win, from_=8, to=64, orient=tk.HORIZONTAL)
    grid_slider.set(GRID_SIZE)
    grid_slider.pack()

    tk.Label(settings_win, text="顏色分類數 (NUM_COLORS)").pack()
    color_slider = tk.Scale(settings_win, from_=2, to=36, orient=tk.HORIZONTAL)
    color_slider.set(NUM_COLORS)
    color_slider.pack()

    tk.Label(settings_win, text="格子大小 (CELL_SIZE)").pack()
    cell_slider = tk.Scale(settings_win, from_=5, to=20, orient=tk.HORIZONTAL)
    cell_slider.set(CELL_SIZE)
    cell_slider.pack()

    def on_confirm():
        new_grid = grid_slider.get()
        new_colors = color_slider.get()
        new_cell = cell_slider.get()
        apply_settings(new_grid, new_colors, new_cell)
        settings_win.destroy()

    tk.Button(settings_win, text="確認設定", command=on_confirm).pack(pady=10)

#26/02/06新增
def get_canvas_available_size():
    """計算右側主畫布可用顯示區域（依目前視窗大小）"""
    root.update_idletasks()

    root_w = root.winfo_width()
    root_h = root.winfo_height()

    left_w = btn_frame.winfo_width() if 'btn_frame' in globals() else 0
    mid_w = color_area.winfo_width() if 'color_area' in globals() else 0

    # 預留 main_frame padding / grid padx / 邊框空間
    avail_w = root_w - left_w - mid_w - 80
    avail_h = root_h - 80

    return max(80, avail_w), max(80, avail_h)


def auto_fit_cell_size(map_w, map_h):
    """
    若目前 CELL_SIZE 太大，會自動縮小到「可完整放進主畫布可見區」。
    只縮小，不自動放大。
    """
    global CELL_SIZE

    avail_w, avail_h = get_canvas_available_size()
    fit_cell = max(1, min(avail_w // max(1, map_w), avail_h // max(1, map_h)))

    if CELL_SIZE > fit_cell:
        CELL_SIZE = fit_cell
        return True
    return False


def draw_number_grid():
    """依 correct_map + CELL_SIZE 重畫數字格"""
    if not correct_map or not correct_map[0]:
        return

    cell_h = len(correct_map)
    cell_w = len(correct_map[0])

    canvas.delete("all")
    canvas.config(width=cell_w * CELL_SIZE, height=cell_h * CELL_SIZE)

    for y in range(cell_h):
        for x in range(cell_w):
            val = correct_map[y][x]
            text = "" if val is None else str(val)

            canvas.create_rectangle(
                x * CELL_SIZE, y * CELL_SIZE,
                (x + 1) * CELL_SIZE, (y + 1) * CELL_SIZE,
                fill="white", outline="gray"
            )
            canvas.create_text(
                x * CELL_SIZE + CELL_SIZE // 2,
                y * CELL_SIZE + CELL_SIZE // 2,
                text=text,
                fill="black", font=("Arial", 10)
            )

def create_number_text(cell_x, cell_y, number):
    """在指定格子中心畫數字；用 tag=cell_number 方便統一顯示/隱藏"""
    if number is None:
        return
    state = "normal" if numbers_visible else "hidden"
    canvas.create_text(
        cell_x * CELL_SIZE + CELL_SIZE // 2,
        cell_y * CELL_SIZE + CELL_SIZE // 2,
        text=str(number),
        fill="black",
        font=("Arial", 10),
        tags=("cell_number",),
        state=state
    )

def toggle_numbers():
    global numbers_visible
    numbers_visible = not numbers_visible
    canvas.itemconfigure("cell_number", state=("normal" if numbers_visible else "hidden"))
    toggle_numbers_btn.config(text="隱藏數字" if numbers_visible else "顯示數字")


# === 建立主視窗 ===
root = tk.Tk()
root.title("數字填色像素畫")

# -3次添加-
root.geometry("512x512")  # 設置初始視窗

# -3次添加-
# === 建立主要水平框架 ===
main_frame = tk.Frame(root)
main_frame.pack(pady=20)

# -3次替換-
# === 畫布 ===
canvas = tk.Canvas(main_frame, bg="white")
#26/02/06替换 canvas.grid(row=0, column=1, padx=10)
canvas.grid(row=0, column=2, padx=10)
canvas.bind("<Button-1>", on_canvas_click)

# -3次替換-
# === 選擇圖片按鈕 ===
btn_frame = tk.Frame(main_frame)

#26/02/06替换 btn_frame.grid(row=0, column=2, padx=10)
btn_frame.grid(row=0, column=0, padx=10)

btn = tk.Button(btn_frame, text="選擇圖片", font=("Arial", 12), command=open_file)
btn.pack()

# -5次添加-
btn_complete = tk.Button(btn_frame, text="自動填充", font=("Arial", 12), command=fill_all)
btn_complete.pack(pady=5)

# -6次添加-
settings_btn = tk.Button(btn_frame, text="設定", font=("Arial", 12), command=open_settings_window)
settings_btn.pack(pady=5)
#26/02/06新增
toggle_numbers_btn = tk.Button(btn_frame, text="隱藏數字", font=("Arial", 12), command=toggle_numbers)
toggle_numbers_btn.pack(pady=5)
#26/02/07新增
fill_mode_btn = tk.Button(
    btn_frame,
    text="填色模式：局部填充",
    font=("Arial", 12),
    command=toggle_fill_mode
)
fill_mode_btn.pack(pady=5)

# === 顏色選擇欄 ===
# -7次添加-
# 顏色側欄的容器
color_area = tk.Frame(main_frame, width=100)
#26/02/06替换 color_area.grid(row=0, column=0, sticky="ns")
color_area.grid(row=0, column=1, sticky="ns")

# 用 Canvas 支援滾動
color_canvas = tk.Canvas(color_area, width=256, height=500)
color_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# 滾動條
color_scrollbar = tk.Scrollbar(color_area, orient="vertical", command=color_canvas.yview)
color_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# 真正放色塊的 Frame
color_frame = tk.Frame(color_canvas)

# 把 color_frame 嵌進 canvas
color_canvas.create_window((0, 0), window=color_frame, anchor="nw")
color_canvas.configure(yscrollcommand=color_scrollbar.set)

# -7次添加-
# 自動更新滾動區域
def update_scrollregion(event):
    color_canvas.configure(scrollregion=color_canvas.bbox("all"))

color_frame.bind("<Configure>", update_scrollregion)

# 支援滑鼠滾動（Windows / Linux / macOS）
def on_mousewheel(event):
    color_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

color_canvas.bind_all("<MouseWheel>", on_mousewheel)  # Windows/macOS
color_canvas.bind_all("<Button-4>", lambda e: color_canvas.yview_scroll(-1, "units"))  # Linux
color_canvas.bind_all("<Button-5>", lambda e: color_canvas.yview_scroll(1, "units"))   # Linux

#26/02/06新增
def on_root_resize(event):
    if event.widget is not root:
        return
    if not correct_map or not correct_map[0]:
        return

    map_h = len(correct_map)
    map_w = len(correct_map[0])

    changed = auto_fit_cell_size(map_w, map_h)
    if changed:
        draw_number_grid()

root.bind("<Configure>", on_root_resize)

root.mainloop()
