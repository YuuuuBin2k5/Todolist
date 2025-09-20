"""
    Cửa sổ chính chạy Main Menu
"""
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout

# Import các lớp widget đã được module hóa từ các file khác
from side_panel import SidePanel
from calendar_widget import CalendarWidget
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

"""
    Cửa sổ chính chạy Main Menu
"""
import sys
# MỚI: Import thêm QStackedWidget
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QStackedWidget
from PyQt5.QtGui import QFont, QFontDatabase

# Import các lớp widget đã được module hóa
from MainMenu.side_panel import SidePanel
from MainMenu.calendar_widget import CalendarWidget
from MainMenu.week_widget import WeekWidget # MỚI: Import WeekWidget

# Định nghĩa STYLESHEET (giữ nguyên như của bạn)
STYLESHEET = """
    /* ... (toàn bộ CSS của bạn ở đây) ... */
"""

class MainWindow(QMainWindow):
    """
        Cửa sổ chính của ứng dụng.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard - Calendar")
        self.setGeometry(100, 100, 1400, 900)
        self.setObjectName("MainWindow")
        self.setStyleSheet(STYLESHEET)
        self.initUI()

    def initUI(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Lắp ráp các thành phần ---
        
        # 1. SidePanel vẫn giữ nguyên
        self.side_panel = SidePanel()
        main_layout.addWidget(self.side_panel)
        
        # THAY ĐỔI: Sử dụng QStackedWidget để quản lý các view
        # 2. Tạo một QStackedWidget để chứa các chế độ xem (tháng, tuần)
        self.view_stack = QStackedWidget()
        
        # 3. Tạo các widget con cho từng chế độ xem
        self.calendar_view = CalendarWidget()
        self.week_view = WeekWidget()
        
        # 4. Thêm các widget con vào QStackedWidget
        self.view_stack.addWidget(self.calendar_view)
        self.view_stack.addWidget(self.week_view)
        
        # 5. Thêm QStackedWidget vào layout chính
        main_layout.addWidget(self.view_stack, 1)

        # 6. Đặt chế độ xem mặc định là lịch tháng
        self.view_stack.setCurrentWidget(self.calendar_view)

        # --- Kết nối tín hiệu (Signals) và hành động (Slots) ---
        self.side_panel.exit_btn.clicked.connect(self.close)
        
        # MỚI: Kết nối các nút chuyển view trong side_panel với các hàm trong MainWindow
        self.side_panel.month_view_btn.clicked.connect(self.show_month_view)
        self.side_panel.week_view_btn.clicked.connect(self.show_week_view)

    # MỚI: Hàm để chuyển sang chế độ xem tháng
    def show_month_view(self):
        self.view_stack.setCurrentWidget(self.calendar_view)

    # MỚI: Hàm để chuyển sang chế độ xem tuần
    def show_week_view(self):
        self.view_stack.setCurrentWidget(self.week_view)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # ... (Code tải font của bạn giữ nguyên)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())