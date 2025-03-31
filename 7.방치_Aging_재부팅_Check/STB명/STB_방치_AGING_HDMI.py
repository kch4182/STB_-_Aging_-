import numpy as np
from PIL import ImageGrab
import time, csv, os, sys, cv2, ast, mss
from datetime import datetime

# GUI에서 한글 출력하기 위해 encoding 형식 수정
sys.stdout.reconfigure(encoding="utf-8")
# 색상 기준
BLACK_RGB = (19, 19, 19)  # 화면 Black
# *********************************IDIS or SmartViewer Tool 적용*********************************
BLUE_RGB_IDIS = (8,6,247)  # IDIS 화면 (450, 200) 좌표의 RGB 평균값
BLUE_RGB_IDIS2 = (58,0,196) # LG IDIS 화면 -> 기존 IDIS 화면이랑 다르게 SmartViewer 처럼 파란색임

BLUE_RGB_SMART = (8, 8, 252)  # SmartViewer화면 Blue
# BLUE_RGB_SMART = (31,31,31) # Composite 화면 끊김 변수
########################################################

#******************STB Model 마다 변경해야 할 거******************
AC_AGING_IDIS = tuple(map(int,sys.argv[14].strip("()").split(", ")))   # 1. Booting 완료 색상(IDIS)
AC_AGING_SMART = tuple(map(int,sys.argv[16].strip("()").split(", ")))  # 2. Booting 완료 색상(SMART)
CAPTURE_INTERVAL = 0.2                                                # 5. 캡처 간격

MOVE_IDIS = tuple(map(int,sys.argv[18].strip("()").split(", ")))
MOVE_SMART = tuple(map(int,sys.argv[20].strip("()").split(", ")))
STB_NAME = str(sys.argv[22])
#******************STB Model 마다 변경해야 할 거******************



STB_POSITIONS_IDIS  = [
    (0, 0), (640, 0), (1280, 0),
    (0, 360), (640, 360), (1280, 360),
    (0, 720), (640, 720), (1280, 720)
]
STB_POSITIONS_SMART = [
    (0, 0), (636, 0), (1272, 0),
    (0, 360), (636, 360), (1272, 360),
    (0, 720), (636, 720), (1272, 720)
]
# Tool 받아옴
select_tool_value = str(sys.argv[12])
if select_tool_value == "IDIS" or  select_tool_value == "IDIS_LGU+":
    if select_tool_value == "IDIS" :
        BLUE_RGB = BLUE_RGB_IDIS
    else :
        BLUE_RGB = BLUE_RGB_IDIS2
    AC_AGING = AC_AGING_IDIS
    x_move = MOVE_IDIS[0] # 3. 각 화면에서 움직일 x축
    y_move = MOVE_IDIS[1] # 4. 각 화면에서 움직일 y축
    STB_POSITIONS_default = STB_POSITIONS_IDIS
else :
    BLUE_RGB = BLUE_RGB_SMART
    AC_AGING = AC_AGING_SMART
    x_move = MOVE_SMART[0] # 3. 각 화면에서 움직일 x축
    y_move = MOVE_SMART[1] # 4. 각 화면에서 움직일 y축
    STB_POSITIONS_default = STB_POSITIONS_SMART # SMARTVIEWER 맨 오른쪽에 Padding 10정도 있어 위치 수정
#*********************************IDIS or SmartViewer Tool 적용*********************************

#ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ변수 설정ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ

# 여기서 구분으로 GUI에서 STB 위치 받아옴
STB_POSITIONS = tuple(ast.literal_eval(sys.argv[24]))

# STB1 기준일 때 
if len(STB_POSITIONS) == 1 :
   STB_POSITIONS = [(x + STB_POSITIONS[0][0], y + STB_POSITIONS[0][1]) for x, y in STB_POSITIONS_default] # SMARTVIEWER 16:9 => 9개 layout    
# 개별마다 따로 설정할 때 그대로
else :
    # 각각의 좌표로 받는다면 Default 값으로 사용
    STB_POSITIONS_default = STB_POSITIONS_IDIS
    
###################################################

###################################################
STB_AC_LIST = sys.argv[2].split(',')  # list로 반환해야 함
STB_AC_LIST = [int(STB_AC_LIST[i])-1 for i in range(len(STB_AC_LIST))] # List index - 1 해서 실제 값
STB_AC_LIST_N = len(STB_AC_LIST) # List 개수
# AC_적용 STB 위치
STB_AC_POSITIONS = [STB_POSITIONS[i] for i in STB_AC_LIST]

# AC 설정 관련 변수
STB_AC_ON_TIME = int(sys.argv[4])
STB_AC_OFF_TIME = int(sys.argv[6])
STB_AC_CHECK_TIME = int(sys.argv[8])

# AC ON 기준 STB Input
STB_AC_CHECK = STB_AC_LIST[0]  # List[0]을 기준으로 AC Check 기준 잡음
# AC_CHECK 좌표를 고정시킬 거임
STB_POSITIONS_default = [(x+450, y+ 200) for x,y in STB_POSITIONS_default]
STB_AC_CHECK_POSITIONS = []
[{STB_AC_CHECK_POSITIONS.append(STB_POSITIONS_default[j])} for i, j in enumerate(STB_AC_LIST)]





# 첫 부팅 시간 저장
start_time = None

# 로그 관련
START_DAY = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
stb_log_state = {f"STB {STB_AC_LIST[i]+1}": {"start_time": None, "first_print": True, "blue_state" : True, "last_log" : None} for i in range(len(STB_AC_LIST))}

log_path = sys.argv[10] # log 저장 경로
stb_rgb_counts = {
    f"STB {i+1}": {"screen_black": 0,"screen_blue":0,"screen_stop":0, "last_rgb": None, "black_count" :0, "last_rgb2": None, "last_print":None,} for i in range(len(STB_POSITIONS))
}
stb_check_counts = {
    f"CHECK_STB {i+1}" : {"screen_blue":0} for j, i in enumerate(STB_AC_LIST)
}

print("￣￣￣￣￣￣￣￣￣￣￣￣Test STB Number￣￣￣￣￣￣￣￣￣￣￣￣￣￣")

[print(f"{j+1}. STB {i+1}") for j, i in enumerate(STB_AC_LIST)]

# 사용자의 모니터 해상도 
MAIN_WIDTH, MAIN_HEIGHT = 1920, 1080
SUB_WIDTH, SUB_HEIGHT = 1920, 1080
# ImageGrab : bbox = (x1, y1, x2, y2)
# mss : bbox = {"left": x1, "top": y1, "width": w, "height": h}
# 이런 식으로 인자값을 받아와서 left, top 좌표를 지정하고 여기서 해상도에 맞게 캡처
# ImageGrab은 Main화면에서 왼쪽 위 좌표부터 -> 오른쪽 아래 좌표까지 캡처
def capture_screen():
    """현재 모니터 위치에 따라 화면을 캡처하고 RGB 배열 반환"""
    x_pos = STB_AC_POSITIONS[0][0]  # STB 위치 정보

    with mss.mss() as sct:
        # 서브 모니터가 왼쪽에 있는 경우
        if x_pos < 0:
            # 좌측 서브 모니터 캡처: 화면이 음수 좌표에 있으므로 이를 처리
            bbox = {"left": -MAIN_WIDTH, "top": 0, "width": SUB_WIDTH, "height": MAIN_HEIGHT}
        # 서브 모니터가 오른쪽에 있는 경우
        elif x_pos > MAIN_WIDTH:
            bbox = {"left": MAIN_WIDTH, "top": 0, "width": SUB_WIDTH, "height": MAIN_HEIGHT}
        # 메인 모니터 캡처
        else:
            bbox = {"left": 0, "top": 0, "width": MAIN_WIDTH, "height": MAIN_HEIGHT}

        # 화면 캡처
        screenshot = sct.grab(bbox)
        # 캡처된 이미지를 RGB로 변환
        img = np.array(screenshot)  # BGRA -> BGR
        img = img[..., :3]  # Alpha 채널 제외하고 RGB만 추출
        screenshot = img[..., ::-1]  # BGR을 RGB로 변환
        return np.array(screenshot)
    
# 2. 좌표 확인용 함수
def show_stb_positions(image, positions, scale=0.6):  # 화면 축소 비율
    # 화면 축소
    small_image = cv2.resize(image, (0, 0), fx=scale, fy=scale)  # fx, fy: 가로, 세로 비율 설정

    # OpenCV에서 사용할 이미지로 변환 (Pillow 이미지를 BGR 형식으로 변환)
    image_bgr = cv2.cvtColor(small_image, cv2.COLOR_RGB2BGR)

    # 축소된 이미지의 좌표 변환
    scaled_positions = [(int(x * scale), int(y * scale)) for x, y in positions]
    # STB 포지션에 빨간 점 그리기
    for x, y in scaled_positions:
        # 좌표가 이미지 크기 내에 있는지 확인
        if 0 <= x < image_bgr.shape[1] and 0 <= y < image_bgr.shape[0]:
            cv2.circle(image_bgr, (x, y), 3, (0, 0, 255), -1)  # 빨간색 원
        else :
            pass

    # 이미지 창 띄우기
    cv2.imshow("STB Positions", image_bgr)

    # 7초 동안 창을 표시한 후 자동 닫기
    cv2.waitKey(7000)
    cv2.destroyAllWindows()  # 창 닫기
    
    # 사용한 이미지 메모리 해제
    small_image = None  
    image_bgr = None    
    del small_image     
    del image_bgr       

# 3. 로그 기록 함수
def log_event(stb_key, event, already_flag):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    current_time2 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    compare_log = ["stb :", stb_key, "time : ", current_time, "event :", event ]
    if already_flag != compare_log :  # 이미 기록된 시간과 같으면 기록 안함
        print(f"[{current_time2}] : {stb_key} : {event} 로그 저장")
        # 경로가 존재하지 않으면 생성
        os.makedirs(log_path, exist_ok=True)
        
        log_file = os.path.join(log_path, f"NOAction_{START_DAY}.csv")
        
        with open(log_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([ stb_key, current_time2,event])
        
        already_flag = compare_log  # 기록 후 flag 갱신
            
    return already_flag  # 갱신된 flag 반환

CHANGE_CHECK_STB = 0
#ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡMain 함수ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ
def ac_check(image, positions, STB_AC_LIST):
    global start_time, stb_rgb_counts, stb_log_state
    # count 설정 
    count_range = 300 # Test할 때 수정하기 귀찮아서 만든 변수
    try :
        for i, (x, y) in enumerate(positions):
            # 만약 서브 모니터에 해당하는 좌표라면
            if x >= MAIN_WIDTH:
                x = x - MAIN_WIDTH  # 서브 모니터 좌표를 메인 모니터에 맞게 변환
            # Screen 끊김 check
            check_x = STB_AC_CHECK_POSITIONS[i][0]
            check_y = STB_AC_CHECK_POSITIONS[i][1]
            screen_rgb = tuple(image[check_y,check_x])

            rgb = tuple(image[y, x])
            stb_key = f"STB {STB_AC_LIST[i]+1}"
            
            
            # 중복 IF문 진입 방지
            already_flag = stb_log_state[stb_key]["last_log"]

            # 1. 처음 조금이라도 화면이 끊기면 해당 IF문 진입
            # BLUE_RGB 상태 확인
            if np.linalg.norm(np.array(screen_rgb) - np.array(BLUE_RGB)) < 25  :
                stb_log_state[stb_key]["blue_state"] = False # blue 상태 업데이트
                stb_rgb_counts[stb_key]["screen_blue"] += 1 # count => 10번 찍히면
                stb_rgb_counts[stb_key]["screen_black"] = 0

                # rgb blue가 계속 유지된다면 STB Screen 끊김 로그 찍음
                if int(stb_rgb_counts[stb_key]["screen_blue"]) == count_range :
                    # 여기서 초기화를 안 하는 이유는 screen_blue가 계속 유지되면 count가 계속 늘어나기 때문
                    stb_log_state[stb_key]["last_log"] = log_event(stb_key, "STB Screen 끊김 유지됨", already_flag)
                elif int(stb_rgb_counts[stb_key]["screen_blue"]) < count_range :
                    stb_log_state[stb_key]["last_log"] = log_event(stb_key, "STB Screen 끊김 의심", already_flag) 
                else : 
                    pass
                    

            
            # 2. blue가 이미 나왔다면 이제 재부팅인지 Check 하는 함수
                # 여기서 부팅 시간 조절 => 캡처시간(0.3초 * reboot_check_time)
                # Ex) reboot_check_time이 2라면 => 0.6초간 Reboot 색상이 유지되면 Reboot으로 간주
            
            if stb_log_state[stb_key]["blue_state"] == False :
            # BLUE RGB에서 변경되면 해당 조건문 진입
                if np.linalg.norm(np.array(screen_rgb) - np.array(BLUE_RGB)) > 30 :
                    # stb_rgb_counts[stb_key]["black_count"] += 1 # 재부팅 Cover 변수
                    stb_rgb_counts[stb_key]["screen_black"] += 1 # 화면 끊김 변수
                    stb_log_state[stb_key]["last_log"] = log_event(stb_key, "STB Reboot 의심", already_flag)
                    stb_rgb_counts[stb_key]["screen_blue"] = 0 # screen_blue 초기화

                    # 로그 찍고 초기화
                    stb_log_state[stb_key]["blue_state"] = True # blue 상태 초기화
                    # 3. Black 화면 유지된다면 로그 저장
                    if np.linalg.norm(np.array(screen_rgb) - np.array(BLACK_RGB)) < 30:
                        if int(stb_rgb_counts[stb_key]["screen_black"]) == count_range :
                            stb_log_state[stb_key]["last_log"] = log_event(stb_key, "STB 화면 Black 유지됨", already_flag)
                           
                else :
                    stb_rgb_counts[stb_key]["black_count"] = 0
                    stb_rgb_counts[stb_key]["screen_black"] = 0

            # 4. Aging 중 Black 화면일 경우 로그 저장
            if np.linalg.norm(np.array(screen_rgb) - np.array(BLACK_RGB)) < 30 :
                stb_rgb_counts[stb_key]["screen_black"] += 1 # 화면 끊김 변수
                stb_rgb_counts[stb_key]["screen_blue"] = 0 # screen_blue 초기화
                if int(stb_rgb_counts[stb_key]["screen_black"]) == count_range :
                    stb_log_state[stb_key]["last_log"] = log_event(stb_key, "STB 화면 Black 유지됨", already_flag)
            
            else : 
                # Black이 아니라면 초기화
                stb_rgb_counts[stb_key]["screen_black"] = 0
    except Exception as e :
        print("Error :", e)

            
    

#ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡMain 함수ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ    

def main():
    while True: 
        # Image 캡처
        image = capture_screen()
        # 각 STB 화면에 대해 check
        ac_check(image, STB_AC_POSITIONS, STB_AC_LIST) # 여기서 필요한게 사용자 설정한 STB_POSITIONS, STB_AC_LIST
        time.sleep(CAPTURE_INTERVAL)
        
print("***5초 후 Test 좌표 캡처 시작***")
time.sleep(5)
screenshot = capture_screen()
show_stb_positions(screenshot, STB_AC_CHECK_POSITIONS, scale=0.7)
print(STB_AC_CHECK_POSITIONS)
# 메모리 삭제
screenshot = None
print("3초 후 NO Action Aging Detecting Start ")
time.sleep(3)
print("Start Detecting")
time.sleep(2)
main()    
 
