"""
    Cửa sổ chính chạy Main Menu
"""

import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QMessageBox

# Import các lớp widget đã được module hóa từ các file khác
from MainMenu.side_panel import SidePanel
from MainMenu.calendar_widget import CalendarWidget
from PyQt5.QtGui import QFont, QFontDatabase


# Định nghĩa một chuỗi chứa mã CSS (QSS) để tạo kiểu cho toàn bộ ứng dụng
STYLESHEET = """
    /* --- Kiểu chung --- */
    #MainWindow { background-color: #f0f0f0; } /* Nền cửa sổ chính */
    #SidePanel { background-color: #e9e9e9; border-right: 1px solid #d0d0d0; } /* Nền và viền phải cho thanh bên */
    
    /*Style cho phần giá trị (tên, vai trò) để in đậm */
    #InfoValueLabel {
        font-weight: bold;
        font-size: 14px;
    }
    
    /* Kiểu chung cho các nút bấm trong thanh bên */
    #SidePanel QPushButton { 
        background-color: #ffffff; 
        border: 1px solid #c0c0c0; 
        border-radius: 15px; 
        padding: 10px; 
        font-weight: bold; 
    }
    #SidePanel QPushButton:hover { background-color: #f5f5f5; }/* Hiệu ứng khi di chuột vào */
    
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
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        
        self.user_id = user_data[0]
        self.user_name = user_data[1]
        self.default_role = "Quản trị viên"

        self.setWindowTitle("Dashboard - Calendar")
        self.setGeometry(100, 100, 1400, 900)
        self.setObjectName("MainWindow") # Đặt tên để áp dụng CSS
        self.setStyleSheet(STYLESHEET) # Áp dụng CSS cho cửa sổ và các widget con của nó
        
        self.initUI()
        self._handle_personal_view()

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

        # Giao diện personal
        self.side_panel.personal_area_requested.connect(self._handle_personal_view)
        self.side_panel.group_area_requested.connect(self._handle_group_view)

        # --- Kết nối tín hiệu (Signals) và hành động (Slots) ---
        # Khi nút exit_btn trong side_panel được nhấn (clicked), gọi hàm close() của cửa sổ chính.
        self.side_panel.exit_btn.clicked.connect(self.close)

    def _handle_personal_view(self):
        print("Chuyển sang khu vực cá nhân...")
        self.side_panel.set_user_info(self.user_name, self.default_role)

    def _handle_group_view(self):
        print("Chuyển sang khu vực nhóm...")
        group_role = "Thành viên" 
        try:
            conn = sqlite3.connect("todolist_database.db")
            cursor = conn.cursor()
            
            cursor.execute("SELECT group_id FROM group_members WHERE user_id = ? LIMIT 1", (self.user_id,))
            group_result = cursor.fetchone()
            
            if group_result:
                group_id = group_result[0]
                
                cursor.execute("SELECT leader_id FROM groups WHERE group_id = ?", (group_id,))
                leader_result = cursor.fetchone()

                if leader_result:
                    leader_id = leader_result[0]
                    if self.user_id == leader_id:
                        group_role = "Quản trị viên"
                
                self.side_panel.set_user_info(self.user_name, group_role)
            else:
                self.side_panel.set_user_info(self.user_name, "Chưa tham gia nhóm")
                QMessageBox.information(self, "Thông báo", "Bạn chưa tham gia nhóm nào.")
            
            conn.close()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Không thể truy vấn vai trò nhóm: {e}")


