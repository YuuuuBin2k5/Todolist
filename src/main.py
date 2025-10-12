# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFontDatabase, QFont
from login import LoginRegisterApp
from config import FONT_PATH

if __name__ == "__main__":
    # Tạo đối tượng ứng dụng
    app = QApplication(sys.argv)
    
    # --- Tải và áp dụng font chữ với đường dẫn ĐÚNG ---
    # Use centralized FONT_PATH from config
    font_id = QFontDatabase.addApplicationFont(FONT_PATH)
    
    if font_id < 0:
        # Xử lý lỗi nếu không tải được font, sử dụng font mặc định
        print(f"LỖI: Không thể tải font từ đường cấu hình: '{FONT_PATH}'. Sử dụng font hệ thống.")
        app.setStyleSheet(f"""
            QWidget {{
                font-family: 'Segoe UI', 'Arial', 'DejaVu Sans', sans-serif;
            }}
            QPushButton {{
                cursor: pointhuyer;
            }}
        """)
    else:
        # Lấy tên font đã tải và áp dụng cho toàn bộ ứng dụng
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        print(f"Font '{font_family}' đã được tải thành công.")
        app.setStyleSheet(f"""
            QWidget {{
                font-family: '{font_family}', 'Segoe UI', 'Arial', 'DejaVu Sans', sans-serif;
            }}
            QPushButton {{
                cursor: pointer;
            }}
        """)

    # Tạo và hiển thị cửa sổ đăng nhập
    window = LoginRegisterApp()
    window.show()
    
    # Bắt đầu vòng lặp sự kiện
    sys.exit(app.exec_())
