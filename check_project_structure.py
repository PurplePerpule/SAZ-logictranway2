# create_test_fonts.py - создайте этот файл в корне проекта
import os
from pathlib import Path

def check_project_structure():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Текущая директория: {current_dir}")
    print(f"Содержимое текущей директории:")
    for item in os.listdir(current_dir):
        print(f"  - {item}")

    fonts_dir = os.path.join(current_dir, 'fonts')
    print(f"\nПапка fonts существует: {os.path.exists(fonts_dir)}")
    if os.path.exists(fonts_dir):
        print("Файлы в папке fonts:")
        for item in os.listdir(fonts_dir):
            print(f"  - {item}")

if __name__ == "__main__":
    check_project_structure()
