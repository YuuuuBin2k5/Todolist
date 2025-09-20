# -*- coding: utf-8 -*-
"""
    Cửa sổ chính chạy Main Menu
"""

import sys
import sqlite3
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QMessageBox, QFileDialog, QSizePolicy, QStackedWidget
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtCore import QDateTime, QDate

# Import các lớp widget đã được module hóa từ các file khác
from MainMenu.side_panel import SidePanel
from MainMenu.calendar_widget import CalendarWidget
from MainMenu.components import TaskWidget
from MainMenu.home_page import HomePageWidget
from config import *

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
    #SidePanel QPushButton:hover { background-color: #f0f0f0; } /* Hiệu ứng khi di chuột */

    /* Style cho các nút khi chúng đang ở trạng thái không được chọn */
    #SidePanel QPushButton[state="active"] {
        background-color: #e0e0e0;
        color: #888888;
        border: 1px solid #b0b0b0;
    }

    #CalendarWidget {
        background-color: #f8f8f8;
        border-radius: 10px;
        padding: 20px;
    }

    #DayWidget {
        background-color: #ffffff;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        padding: 5px;
        margin: 5px;
    }
    #DayWidget:hover { border: 1px solid #a0a0a0; }

    #DayLabel {
        font-weight: bold;
        font-size: 16px;
    }
    #MonthYearLabel {
        font-weight: bold;
        font-size: 20px;
    }
    #TaskWidget {
        background-color: #e6eefc;
        border-radius: 5px;
        padding: 5px;
        margin-bottom: 3px;
    }
    #TaskWidget:hover { background-color: #d1e2f8; }
    #TaskCheckbox {
        spacing: 5px;
    }
    QScrollArea {
        border: none;
    }
    QScrollBar:vertical {
        border: 1px solid #999999;
        background: #f0f0f0;
        width: 10px;
    }
    QScrollBar::handle:vertical {
        background: #cccccc;
        border-radius: 5px;
        min-height: 20px;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        border: none;
        background: none;
    }
"""

class MainWindow(QMainWindow):
    """
        Cửa sổ chính của ứng dụng To-do List.
        Chứa thanh bên (SidePanel) và khu vực hiển thị lịch (CalendarWidget).
    """

    def __init__(self, user_id, user_name, default_role='Cá nhân', parent=None):
        """
            Khởi tạo cửa sổ chính.
            Args:
                user_id (int): ID của người dùng đã đăng nhập.
                user_name (str): Tên của người dùng.
                default_role (str): Vai trò mặc định (ví dụ: 'Cá nhân').
        """
        super().__init__(parent)
        self.user_id = user_id
        self.user_name = user_name
        self.default_role = default_role
        self.setWindowTitle("To-do List - Lịch")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(STYLESHEET)
        self.setObjectName("MainWindow")

        self.initUI()
        self.side_panel.set_user_info(self.user_name, self.default_role)
        # Khởi tạo với trang chủ cá nhân
        self.side_panel.update_view_buttons('personal', 'home')
        self.home_widget.load_data()

    def initUI(self):
        """
            Thiết lập giao diện người dùng cho cửa sổ chính.
        """
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Thanh điều hướng bên trái
        self.side_panel = SidePanel()
        self.main_layout.addWidget(self.side_panel)

        # StackedWidget để chuyển đổi giữa trang chủ và lịch
        self.content_stack = QStackedWidget()
        self.content_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout.addWidget(self.content_stack)

        # Trang chủ
        self.home_widget = HomePageWidget(self.user_id)
        self.content_stack.addWidget(self.home_widget)

        # Khu vực lịch
        self.calendar_widget = CalendarWidget()
        self.content_stack.addWidget(self.calendar_widget)

        # Mặc định hiển thị trang chủ
        self.content_stack.setCurrentWidget(self.home_widget)
        self.current_area = 'personal'
        self.current_content = 'home'

        # Kết nối các tín hiệu từ SidePanel
        self.side_panel.personal_area_requested.connect(self._handle_personal_view)
        self.side_panel.group_area_requested.connect(self._handle_group_view)
        self.side_panel.home_requested.connect(self._handle_home_view)
        self.side_panel.calendar_requested.connect(self._handle_calendar_view)
        self.side_panel.exit_requested.connect(self.close)

    def _handle_personal_view(self):
        """
            Xử lý việc chuyển đổi sang chế độ xem cá nhân.
        """
        print("Chuyển sang khu vực cá nhân...")
        self.current_area = 'personal'
        self.side_panel.set_user_info(self.user_name, self.default_role)
        self.side_panel.update_view_buttons('personal', self.current_content)
        
        # Cập nhật dữ liệu cho trang hiện tại
        if self.current_content == 'home':
            self.home_widget.user_id = self.user_id
            self.home_widget.load_data()
        elif self.current_content == 'calendar':
            self.load_personal_tasks()

    def _handle_group_view(self):
        """
            Xử lý việc chuyển đổi sang chế độ xem nhóm.
        """
        print("Chuyển sang khu vực nhóm...")
        self.current_area = 'group'
        self.side_panel.update_view_buttons('group', self.current_content)
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
                
                # Cập nhật dữ liệu cho trang hiện tại (chỉ calendar hỗ trợ group hiện tại)
                if self.current_content == 'calendar':
                    self.load_group_tasks(group_id)
                # TODO: Thêm hỗ trợ group cho home page
                    
            else:
                self.side_panel.set_user_info(self.user_name, "Chưa tham gia nhóm")
                QMessageBox.information(self, "Thông báo", "Bạn chưa tham gia nhóm nào.")
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Lỗi khi kết nối hoặc truy vấn CSDL: {e}")
        finally:
            if conn:
                conn.close()
                
    def _handle_home_view(self):
        """
            Xử lý việc chuyển đổi sang trang chủ.
        """
        print("Chuyển sang trang chủ...")
        self.current_content = 'home'
        self.content_stack.setCurrentWidget(self.home_widget)
        self.side_panel.update_view_buttons(self.current_area, 'home')
        
        # Cập nhật dữ liệu cho trang chủ
        self.home_widget.user_id = self.user_id
        self.home_widget.load_data()
        
    def _handle_calendar_view(self):
        """
            Xử lý việc chuyển đổi sang lịch.
        """
        print("Chuyển sang lịch...")
        self.current_content = 'calendar'
        self.content_stack.setCurrentWidget(self.calendar_widget)
        self.side_panel.update_view_buttons(self.current_area, 'calendar')
        
        # Cập nhật dữ liệu cho lịch
        if self.current_area == 'personal':
            self.load_personal_tasks()
        elif self.current_area == 'group':
            # Cần load group tasks nếu đã có group
            try:
                conn = sqlite3.connect("todolist_database.db")
                cursor = conn.cursor()
                cursor.execute("SELECT group_id FROM group_members WHERE user_id = ? LIMIT 1", (self.user_id,))
                group_result = cursor.fetchone()
                if group_result:
                    self.load_group_tasks(group_result[0])
                conn.close()
            except sqlite3.Error as e:
                print(f"Lỗi khi load group tasks: {e}")

    def load_personal_tasks(self):
        """
            Tải và hiển thị các công việc cá nhân từ cơ sở dữ liệu.
        """
        tasks_by_day = {}
        try:
            conn = sqlite3.connect("todolist_database.db")
            cursor = conn.cursor()
            
            cursor.execute("SELECT due_at, title, is_done, note FROM tasks WHERE user_id = ?", (self.user_id,))
            tasks = cursor.fetchall()

            for due_at_str, title, is_done, note in tasks:
                # Nếu có due_at, chuyển đổi chuỗi ngày tháng thành đối tượng QDate
                if due_at_str:
                    task_date = QDate.fromString(due_at_str[:10], "yyyy-MM-dd")  # Lấy phần date từ timestamp
                    if task_date.year() == self.calendar_widget.current_date.year and task_date.month() == self.calendar_widget.current_date.month:
                        day = task_date.day()
                        if day not in tasks_by_day:
                            tasks_by_day[day] = []
                        tasks_by_day[day].append((title, is_done, note))

            self.calendar_widget.populate_calendar(tasks_by_day)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Lỗi khi tải công việc cá nhân: {e}")
        finally:
            if conn:
                conn.close()

    def load_group_tasks(self, group_id):
        """
            Tải và hiển thị các công việc nhóm từ cơ sở dữ liệu.
        """
        tasks_by_day = {}
        try:
            conn = sqlite3.connect("todolist_database.db")
            cursor = conn.cursor()
            
            cursor.execute("SELECT due_at, title, is_done, note FROM group_tasks WHERE group_id = ?", (group_id,))
            tasks = cursor.fetchall()

            for due_at_str, title, is_done, note in tasks:
                # Nếu có due_at, chuyển đổi chuỗi ngày tháng thành đối tượng QDate
                if due_at_str:
                    task_date = QDate.fromString(due_at_str[:10], "yyyy-MM-dd")  # Lấy phần date từ timestamp
                    if task_date.year() == self.calendar_widget.current_date.year and task_date.month() == self.calendar_widget.current_date.month:
                        day = task_date.day()
                        if day not in tasks_by_day:
                            tasks_by_day[day] = []
                        tasks_by_day[day].append((title, is_done, note))

            self.calendar_widget.populate_calendar(tasks_by_day)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Lỗi khi tải công việc nhóm: {e}")
        finally:
            if conn:
                conn.close()

