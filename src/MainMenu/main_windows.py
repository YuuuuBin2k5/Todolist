"""
    Cửa sổ chính chạy Main Menu
"""
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout

# Import các lớp widget đã được module hóa từ các file khác
from MainMenu.side_panel import SidePanel
from MainMenu.calendar_widget import CalendarWidget
from PyQt5.QtGui import QFont, QFontDatabase


# Định nghĩa một chuỗi chứa mã CSS (QSS) để tạo kiểu cho toàn bộ ứng dụng
STYLESHEET = """
    /* --- Kiểu chung --- */
    #MainWindow { background-color: #f0f0f0; } /* Nền cửa sổ chính */
    #SidePanel { background-color: #e9e9e9; border-right: 1px solid #d0d0d0; } /* Nền và viền phải cho thanh bên */
    
    #InfoLabel { font-size: 13px; } /* Kiểu cho nhãn Tên, Vai trò */
    /*Style cho phần giá trị (tên, vai trò) để in đậm */
    #InfoValueLabel {
        font-weight: bold;
        font-size: 14px;
    }
    
    /* Kiểu chung cho các nút bấm trong thanh bên */
    QPushButton {
        background-color: #ffffff; border: 1px solid #c0c0c0;
        border-radius: 15px; padding: 10px; font-weight: bold;
    }
    QPushButton:hover { background-color: #f5f5f5; } /* Hiệu ứng khi di chuột vào */
    
    /* Kiểu riêng cho nút Exit */
    #ExitButton { background-color: #ffe0e0; border-color: #ffaaaa; }
    #ExitButton:hover { background-color: #ffcccc; }

    /* --- CSS riêng cho các thành phần trong CalendarWidget --- */
    DayWidget { background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 4px; }
    TaskWidget {
        background-color: white; border: 1px solid #d0d0d0;
        border-radius: 8px; padding: 5px; margin-bottom: 3px;
    }
    #WeekDayLabel { font-weight: bold; color: #555; padding-bottom: 5px; }
    .DateLabel { font-size: 11px; font-weight: bold; padding: 2px; color: #333; }
    
    /* Ghi đè kiểu nút bấm cho các nút trong lịch (Trước/Sau) */
    CalendarWidget QPushButton {
        background-color: #f0f0f0; border: 1px solid #c0c0c0;
        border-radius: 4px; padding: 5px 10px; font-weight: normal;
    }
    CalendarWidget QPushButton:hover { background-color: #e0e0e0; }
    
    /* --- CSS cho cửa sổ chi tiết --- */
    #DayDetailDialog {
        background-color: #f9f9f9;
    }
    #DateHeaderLabel {
        font-size: 18px;
        font-weight: bold;
        color: #333;
        padding: 10px;
        border-bottom: 2px solid #eee;
        margin-bottom: 10px;
    }
    #TaskDetailItem {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
    }
    #NoteLabelInDialog {
        color: #555;
        font-style: italic;
    }
    #DayDetailDialog QPushButton {
        padding: 8px 16px;
        border-radius: 4px;
        background-color: #007bff;
        color: white;
        border: none;
        font-weight: bold;
    }
    #DayDetailDialog QPushButton:hover {
        background-color: #0056b3;
    }
"""

class MainWindow(QMainWindow):
    """
        Cửa sổ chính của ứng dụng.
        Nhiệm vụ chính là lắp ráp các widget con (SidePanel, CalendarWidget) lại với nhau.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard - Calendar")
        self.setGeometry(100, 100, 1400, 900)
        self.setObjectName("MainWindow") # Đặt tên để áp dụng CSS
        self.setStyleSheet(STYLESHEET) # Áp dụng CSS cho cửa sổ và các widget con của nó
        self.initUI()

    def initUI(self):
        # Tạo một widget trung tâm để chứa layout chính
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Bố cục chính của cửa sổ là layout ngang (QHBoxLayout)
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0) # Xóa mọi khoảng đệm ở viền
        main_layout.setSpacing(0) # Xóa khoảng cách giữa các widget con

        # --- Lắp ráp các thành phần ---

        # 1. Tạo một thực thể của SidePanel và thêm vào bên trái layout
        self.side_panel = SidePanel()
        main_layout.addWidget(self.side_panel)
        
        # 2. Tạo một thực thể của CalendarWidget và thêm vào bên phải layout
        self.calendar = CalendarWidget()
        # Thêm calendar với hệ số co giãn là 1. Điều này làm cho nó chiếm hết không gian
        # còn lại theo chiều ngang, trong khi SidePanel có chiều rộng cố định.
        main_layout.addWidget(self.calendar, 1)

        # --- Kết nối tín hiệu (Signals) và hành động (Slots) ---
        # Khi nút exit_btn trong side_panel được nhấn (clicked), gọi hàm close() của cửa sổ chính.
        self.side_panel.exit_btn.clicked.connect(self.close)

if __name__ == '__main__':

    # Tạo đối tượng ứng dụng
    app = QApplication(sys.argv)

    # --- Tải và áp dụng font chữ với đường dẫn ĐÚNG ---
    font_path = "assets/Fonts/BeVietnamPro-Regular.ttf"
    
    font_id = QFontDatabase.addApplicationFont(font_path)
    
    if font_id < 0:
        print(f"LỖI: Không thể tải font từ đường dẫn: '{font_path}'")
    else:
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        print(f"Font '{font_family}' đã được tải thành công.")
        app_font = QFont(font_family, 8)
        app.setFont(app_font)

    # Tạo và hiển thị cửa sổ chính
    window = MainWindow()
    window.show()
    
    # Bắt đầu vòng lặp sự kiện
    sys.exit(app.exec_())