'''******************경로 수정 필요******************'''
# 5가지만 수정하면 됨 -> 모두 일반화 완료
STB_NAME = "STB명"             # 0. STB Model명
MOVE_IDIS = (0,0)             # 1. 색상 확인 좌표(IDIS)
MOVE_SMART = (0,0)            # 2. 색상 확인 좌표(SMART)  
AC_AGING_IDIS = (145, 187, 213)   # 3. Booting 완료 색상(IDIS)
AC_AGING_SMART = (0, 222, 254)  # 4. Booting 완료 색상(SMART)
APPLY_SCRIPT = "STB_방치_AGING_HDMI.py"
'''******************경로 수정 필요******************'''

'''코드 재활용 위한 변수 -> 의미없음'''
STB_AC_ON_TIME = 0
STB_AC_OFF_TIME = 0 
STB_AC_CHECK_TIME = 0 
import subprocess, sys, os, threading
import tkinter as tk
from tkinter import messagebox, filedialog, ttk, scrolledtext


# Pakage 설치
try:
    import PIL 
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
    print("pillow 설치 성공")
try :
    import numpy as np
except ImportError :
    subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy"])
    print("numpy 설치 성공")
try :
    import cv2
except ImportError :
    subprocess.check_call([sys.executable, "-m", "pip", "install", "opencv-python"])
try :
    import mms
except ImportError :
    subprocess.check_call([sys.executable,'-m', 'pip', 'install', 'mss', 'screeninfo'])


# 실행할 Python 파일 경로
# parent_dir = os.path.dirname(os.path.dirname(__file__))

# 현재 모듈의 2단계 상위 디렉토리 경로
parent_dir =  os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__)))))

# 상위 폴더의 'Python' 폴더에 있는 'python.py' 경로 생성
script_path = os.path.join(os.path.dirname(__file__), STB_NAME, APPLY_SCRIPT)


# 글로벌 변수로 현재 실행 중인 프로세스를 추적
process = None

# 폴더 선택 다이얼로그
def choose_folder():
    folder_selected = filedialog.askdirectory(title="폴더 선택")
    if folder_selected:
        folder_path.set(folder_selected)  # 폴더 경로를 변수에 저장
        print(f"선택한 폴더: {folder_selected}")  # 선택된 폴더 경로 출력
    else:
        print("폴더를 선택하지 않았습니다.")

# STB 좌표 모드 변경 함수
def update_coordinate_mode():
    mode = mode_var.get()
    if mode == "stb1":
        # STB1 좌표만 활성화
        for stb, (x_entry, y_entry) in coordinate_entries.items():
            if stb == "1":
                x_entry.config(state=tk.DISABLED, bg="lightgray")
                y_entry.config(state=tk.DISABLED, bg="lightgray")
            else:
                x_entry.config(state=tk.DISABLED, bg="lightgray")
                y_entry.config(state=tk.DISABLED, bg="lightgray")
    else:
        # 모든 STB 좌표 활성화
        for x_entry, y_entry in coordinate_entries.values():
            x_entry.config(state=tk.NORMAL, bg="white")
            y_entry.config(state=tk.NORMAL, bg="white")

# 좌표값과 MOVE_SMART 업데이트 함수
def update_move_smart_based_on_tool():
    global MOVE_SMART, MOVE_IDIS
    
    selected_tool = select_tool.get()  # 선택한 Viewer Program
    if selected_tool == "SMARTVIEWER":
        # SMARTVIEWER가 선택되면 STB1 좌표값을 MOVE_SMART에 반영
        stb1_x = MOVE_SMART[0]  # MOVE_SMART에서 X값 가져오기
        stb1_y = MOVE_SMART[1]  # MOVE_SMART에서 Y값 가져오기
    
        # 실시간으로 STB1 X, Y 값을 GUI에서 변경하여 표시
        coordinate_entries["1"][0].delete(0, tk.END)  # 기존 값 삭제
        coordinate_entries["1"][0].insert(0, str(stb1_x))  # 새로운 X 값 입력
        coordinate_entries["1"][1].delete(0, tk.END)  # 기존 값 삭제
        coordinate_entries["1"][1].insert(0, str(stb1_y))  # 새로운 Y 값 입력
        
        # print(f"MOVE_SMART updated: {MOVE_SMART}")  # 업데이트된 값 확인용 출력
    else :
        # SMARTVIEWER가 선택되면 STB1 좌표값을 MOVE_SMART에 반영
        stb1_x = MOVE_IDIS[0]  # MOVE_SMART에서 X값 가져오기
        stb1_y = MOVE_IDIS[1]  # MOVE_SMART에서 Y값 가져오기
    
        # 실시간으로 STB1 X, Y 값을 GUI에서 변경하여 표시
        coordinate_entries["1"][0].delete(0, tk.END)  # 기존 값 삭제
        coordinate_entries["1"][0].insert(0, str(stb1_x))  # 새로운 X 값 입력
        coordinate_entries["1"][1].delete(0, tk.END)  # 기존 값 삭제
        coordinate_entries["1"][1].insert(0, str(stb1_y))  # 새로운 Y 값 입력

# python Script 실행 함수
def start_ac_check():
    global process  # 글로벌 변수 사용
     # 이전에 실행 중인 프로세스가 있으면 종료
    if process and process.poll() is None:  # 프로세스가 아직 실행 중이면
        print("AC Program 종료 후 재 실행.")
        process.terminate()  # 프로세스 종료

    STB_AC_LIST = [stb for stb, var in stb_vars.items() if var.get()]

    if not STB_AC_LIST:
        messagebox.showwarning("최소 1EA 이상 STB 선택")
        return
    ############################################################
    mode = mode_var.get()
    coordinates = [(0, 0)]
    
    if mode == "stb1":
        # STB1 좌표를 기준으로 모든 STB 좌표 설정
        x1, y1 = int(coordinate_entries["1"][0].get()), int(coordinate_entries["1"][1].get())
        coordinates.append((x1, y1))
        
    else:
        # 개별 좌표 설정
        for stb in range(9):  # 0~8까지 반복 (STB 1~9번)
            x, y = int(coordinate_entries[str(stb + 1)][0].get()), int(coordinate_entries[str(stb + 1)][1].get())
            coordinates.append((x, y))  # 좌표 튜플 추가
    
    ############################################################

    # 폴더 경로 가져오기
    folder_path_value = folder_path.get()
    select_tool_value = select_tool.get()
    coordinates = [(0, 0)]
    if not folder_path_value:
        messagebox.showwarning("폴더 경로 미지정", "폴더를 선택해 주세요.")
        return
    
    try:
        # subprocess.run을 통해 Python 스크립트 실행
        process = subprocess.Popen(
            ['pythonw.exe', "-u", script_path, 
             '--stb_list', ','.join(map(str, STB_AC_LIST)),  # STB 리스트를 문자열로 변환
             '--on_time', str(STB_AC_ON_TIME), 
             '--off_time', str(STB_AC_OFF_TIME), 
             '--check_time', str(STB_AC_CHECK_TIME),
             '--folder', folder_path_value,  # 폴더 경로 전달
             '--tool', select_tool_value,
             'AC_AGING_IDIS', str(AC_AGING_IDIS),
             'AC_AGING_SMART', str(AC_AGING_SMART),
             'MOVE_IDIS', str(MOVE_IDIS),
             'MOVE_SMART', str(MOVE_SMART),
             'STB_NAME', str(STB_NAME),
             '--positions', str(coordinates), # 여기서 좌표 보냄
             ],
            stdout=subprocess.PIPE,  # stdout 캡처
            stderr=subprocess.PIPE,  # stderr 캡처
            encoding='utf-8',  # 출력을 UTF-8로 디코딩
            errors='replace',  # 디코딩 오류 시 대체 문자 사용
            bufsize=1,  # 라인 버퍼링 활성화
            universal_newlines=True  # 텍스트 모드 활성화
        )
        def read_output():
        # 서브 프로세스의 출력을 실시간으로 읽어서 GUI에 출력
            for line in process.stdout:
                output_text.insert(tk.END, line)  # 출력 추가
                output_text.see(tk.END)  # 스크롤 자동 이동
        
        # 별도 스레드에서 실행 (GUI 멈춤 방지)
        thread = threading.Thread(target=read_output, daemon=True)
        thread.start()

    except Exception as e:
        messagebox.showerror("오류", f"스크립트 실행 중 오류 발생: {str(e)}")

# Tkinter 윈도우 설정
root = tk.Tk()
root.title("방치 Aging 재부팅 Check")

# 창 위치 설정
# root.geometry("+{}+{}".format(0, 0))
root.geometry("1400x600")  # 창 크기 설정

# 0. Viewer Program 선택
tool_label = tk.Label(root, text="1. Viewer Program 선택")
tool_label.grid(row=0, column=0, padx=5, pady=(30,10), sticky="w")

select_tool = tk.StringVar()  # Viewer Tool 선택 변수
tool_combobox = ttk.Combobox(root, textvariable=select_tool)
tool_combobox['values'] = ("SMARTVIEWER", "IDIS", "IDIS_LGU+")  # 옵션 설정

tool_combobox['state'] = 'readonly'  # 읽기 전용으로 설정
tool_combobox.grid(row=0, column=1, padx=5, pady=(30,10), sticky="w")

tool_combobox.bind("<<ComboboxSelected>>", lambda event: update_move_smart_based_on_tool())

# 1. STB 번호 체크박스 변수 설정
stb_label = tk.Label(root, text="2. STB 번호 선택")
stb_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

stb_vars = {str(i): tk.BooleanVar() for i in range(1, 10)}

stb_frame = tk.Frame(root)
stb_frame.grid(row=1, column=1, padx=2, pady=2, sticky="w")

for stb, var in stb_vars.items():
    checkbox = tk.Checkbutton(stb_frame, text=f"STB {stb}", variable=var)
    checkbox.pack(side=tk.LEFT, padx=1)


####################################################################
# 좌표 입력 모드 선택
mode_var = tk.StringVar(value="stb1")
mode_frame = tk.Frame(root)
mode_frame.grid(row=2, column=0, padx=5, pady=5, sticky="w")
tk.Label(mode_frame, text="3. 좌표 입력 방식 선택").pack()

radio_frame = tk.Frame(root)
radio_frame.grid(pady=20, sticky="n")
tk.Radiobutton(radio_frame, text="STB1 기준", variable=mode_var, value="stb1", state="disabled").pack()
tk.Radiobutton(radio_frame, text="개별 설정", variable=mode_var, value="individual", state="disabled").pack()

# STB 좌표 입력
coordinate_entries = {}

coord_frame = tk.Frame(root)
tk.Label(coord_frame, text="좌표 설정 필요X").pack()
coord_frame.grid(row=3, column=1, padx=10, pady=15, sticky="w")
stb_positions = [
    (0, 0), (640, 0), (1270, 0),
    (0, 360), (640, 360), (1270, 360),
    (0, 720), (640, 720), (1270, 720)
]
for i, stb in enumerate(stb_vars.keys()):
    frame = tk.Frame(coord_frame)
    frame.pack(anchor="w", padx=10, pady=2)
    tk.Label(frame, text=f"STB {stb} X:").pack(side=tk.LEFT)
    x_entry = tk.Entry(frame, width=5)
    x_entry.insert(0, str(stb_positions[i][0]))
    x_entry.pack(side=tk.LEFT, padx=5)
    tk.Label(frame, text=f"Y:").pack(side=tk.LEFT)
    y_entry = tk.Entry(frame, width=5)
    y_entry.insert(0, str(stb_positions[i][1]))
    y_entry.pack(side=tk.LEFT, padx=5)
    coordinate_entries[stb] = (x_entry, y_entry)

# 초기 모드 설정 (STB1 기준)
update_coordinate_mode()
####################################################################

# 4. 폴더 경로를 저장할 변수
path_label = tk.Label(root, text="4. 로그 저장 경로 선택")
path_label.grid(row=8, column=0, padx=5, pady=3, sticky="w")

folder_path = tk.StringVar()

choose_folder_button = tk.Button(root, text="경로 지정", command=choose_folder)
choose_folder_button.grid(row=8, column=1, padx=5, pady=5, sticky="w")

folder_label = tk.Label(root, textvariable=folder_path)
folder_label.grid(row=9, column=1, padx=5, pady=3, sticky="w")

# 5. 제출 버튼
submit_button = tk.Button(root, text="Start AC Check", command=lambda: threading.Thread(target=start_ac_check).start())
submit_button.grid(row=10, column=1, padx=5, pady=5, sticky="w")

# 6. 출력 결과 표시 Text 위젯
tk.Label(root, text="결과 출력").grid(row = 0, column =2, padx=10, pady=3, sticky="news")
output_text = scrolledtext.ScrolledText(root, height=30, width=90, font=("맑은 고딕", 10))
output_text.grid(row=1, column=2, rowspan=11, padx=10, pady=5, sticky="news")

# Tkinter 이벤트 루프 시작
root.mainloop()
