import os
import time
import cv2
import numpy as np

device = "127.0.0.1:5555"

# Координаты и шаги
start_x = 250
start_y = 400
click_step = 100
final_click = (1925, 1369)

# Имя временного файла для анализа
TEMP_SCREEN_FILE = "_temp_analysis.png"

# --- FUNCTIONS ---

def has_green_area():
    """Функция проверки зелёной области"""
    img = cv2.imread(TEMP_SCREEN_FILE)
    if img is None:
        print(f"Warning: Could not read image {TEMP_SCREEN_FILE} in has_green_area.")
        return False
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_green = np.array([40, 50, 50])
    upper_green = np.array([90, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)
    return cv2.countNonZero(mask) > 500

def red_bottom_y():
    """Функция поиска красного фона и возвращает нижнюю границу по Y"""
    img = cv2.imread(TEMP_SCREEN_FILE)
    if img is None:
        print(f"Warning: Could not read image {TEMP_SCREEN_FILE} in red_bottom_y.")
        return None
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)
    
    ys = np.where(mask > 0)[0]
    if len(ys) == 0:
        return None
    return np.max(ys)

def take_screenshot_for_analysis():
    """Скриншот (для анализа во временный файл)"""
    os.system(f"adb -s {device} shell screencap -p /sdcard/temp_screen.png")
    os.system(f"adb -s {device} pull /sdcard/temp_screen.png ./{TEMP_SCREEN_FILE}")
    print(f"Скриншот сделан для анализа: {TEMP_SCREEN_FILE}")

def click(x, y):
    """Клик"""
    os.system(f"adb -s {device} shell input tap {x} {y}")
    print(f"Клик выполнен по координатам ({x},{y})")
    time.sleep(1)

def scroll_down():
    """Скролл"""
    os.system(f"adb -s {device} shell input swipe 600 1200 600 600 500")
    print("Скролл вниз выполнен")
    time.sleep(1)

# --- MAIN EXECUTION LOOP ---

for i in range(68):
    print(f"\n\n--- НАЧАЛО ВЫПОЛНЕНИЯ #{i + 1}/10 ---")
    
    # 1. Первый скриншот перед началом кликов
    print("--- Делаем 1-й скриншот (перед началом кликов) ---")
    take_screenshot_for_analysis()
    
    # Сохраняем скриншот с уникальным именем для каждого выполнения
    initial_screenshot_name = f"1_before_clicks_run_{i + 1}.png"
    if os.path.exists(TEMP_SCREEN_FILE):
        os.replace(TEMP_SCREEN_FILE, initial_screenshot_name)
        print(f"Сохранен постоянный скриншот: {initial_screenshot_name}")
    else:
        print("Warning: Не удалось создать первый скриншот.")

    is_in_fine_search_mode = False
    current_y = start_y

    while True:
        green_found = False
        red_found = False

        # Определяем начальную Y координату для поиска
        if is_in_fine_search_mode:
            print("\n--- Начинаем точный поиск после красного фона ---")
            take_screenshot_for_analysis()
            red_y = red_bottom_y()
            current_y = red_y + click_step if red_y is not None else start_y
            if red_y is not None:
                print(f"Красный фон найден на Y={red_y}. Начинаем поиск с Y={current_y}")
            else:
                print(f"Красный фон не найден после скролла. Начинаем поиск с Y={current_y}")
        else:
            print("\n--- Начинаем широкий поиск ---")
            current_y = start_y

        # Основной цикл поиска на текущем экране
        while current_y < 1350:
            click(start_x, current_y)
            take_screenshot_for_analysis()

            if has_green_area():
                print("Найдена зеленая область!")
                green_screenshot_name = f"2_green_found_run_{i + 1}.png"
                if os.path.exists(TEMP_SCREEN_FILE):
                    os.replace(TEMP_SCREEN_FILE, green_screenshot_name)
                    print(f"Сохранен постоянный скриншот: {green_screenshot_name}")

                click(final_click[0], final_click[1])
                green_found = True
                break # Выход из цикла поиска на экране

            red_y = red_bottom_y()
            if red_y is not None:
                print(f"Найден красный фон. Нижняя граница Y={red_y}.")
                red_found = True
                break # Выход из цикла поиска на экране

            # Если ничего не найдено, смещаемся вниз
            print(f"Ничего не найдено, кликаем ниже по Y={current_y + click_step}")
            current_y += click_step

        # Обработка результатов поиска на экране
        if green_found:
            print(f"--- ЗАВЕРШЕНИЕ ВЫПОЛНЕНИЯ #{i + 1}/10 (найден зеленый фон) ---")
            break # Выход из while True для текущего выполнения

        if red_found:
            scroll_down()
            is_in_fine_search_mode = True
            # `current_y` будет пересчитан в начале следующей итерации `while True`
            continue

        # Если дошли до конца экрана и ничего не нашли
        if not green_found and not red_found:
            print("Поиск на текущем экране не дал результатов, скроллим.")
            scroll_down()
            is_in_fine_search_mode = False # Возвращаемся к широкому поиску
            current_y = start_y # Сбрасываем Y на начальное значение
    
    print("Пауза 5 секунд перед следующим выполнением...")
    time.sleep(5)

