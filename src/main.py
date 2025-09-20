import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFontDatabase, QFont
from login import LoginRegisterApp

if __name__ == "__main__":
    # Tạo đối tượng ứng dụng
    app = QApplication(sys.argv)
    
    # --- Tải và áp dụng font chữ với đường dẫn ĐÚNG ---
    font_path = "assets/Fonts/BeVietnamPro-Regular.ttf"
    font_id = QFontDatabase.addApplicationFont(font_path)
    
    if font_id < 0:
        # Xử lý lỗi nếu không tải được font, sử dụng font mặc định
        print(f"LỖI: Không thể tải font từ đường dẫn: '{font_path}'. Sử dụng font hệ thống.")
        app.setStyleSheet(f"""
            QWidget {{
                font-family: 'Times New Roman', serif;
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
                font-family: '{font_family}', serif;
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
