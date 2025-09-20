# -*- coding: utf-8 -*-
"""
    Cửa sổ chính chạy Main Menu.
    Đây là file đã được hợp nhất từ hai phiên bản có xung đột.
"""

import os
import sys
import sqlite3
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                             QVBoxLayout, QLabel, QMessageBox, QFileDialog, 
                             QSizePolicy, QStackedWidget, QDialog)
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtCore import QDateTime, QDate, Qt

# Import các lớp widget đã được module hóa từ các file khác
from MainMenu.side_panel import SidePanel
from MainMenu.calendar_widget import CalendarWidget
from MainMenu.home_page import HomePageWidget
from MainMenu.group_dialogs import GroupSelectionDialog, MemberListDialog, AddMemberDialog
from config import *

# [SỬA 1] THÊM HÀM TRỢ GIÚP NÀY VÀO ĐẦU FILE
def _find_database_path():
    """Hàm trợ giúp để tìm đường dẫn tuyệt đối đến file database."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.dirname(current_dir)
        db_path = os.path.join(src_dir, 'Data', 'todolist_database.db')
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Không tìm thấy file database tại: {db_path}")
        return db_path
    except Exception as e:
        print(f"LỖI NGHIÊM TRỌNG: Không thể xác định đường dẫn database. {e}")
        return None

# Định nghĩa một chuỗi chứa mã CSS (QSS) để tạo kiểu cho toàn bộ ứng dụng
# ĐÃ HỢP NHẤT TỪ CẢ HAI FILE
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
    #SidePanel QPushButton:hover { background-color: #f5f5f5; } /* Hiệu ứng khi di chuột */

    /* Style cho các nút khi chúng đang ở trạng thái không được chọn */
    #SidePanel QPushButton[state="active"] {
        background-color: #e0e0e0;
        color: #888888;
        border: 1px solid #b0b0b0;
    }
    
    /* Style cho nút bị vô hiệu hóa */
    #SidePanel QPushButton:disabled {
        background-color: #e0e0e0;
        color: #888888;
        border-color: #b0b0b0;
    }

    /* Kiểu riêng cho nút Exit */
    #ExitButton { background-color: #ffe0e0; border-color: #ffaaaa; }
    #ExitButton:hover { background-color: #ffcccc; }
    
    /* --- CSS cho các thành phần trong CalendarWidget --- */
    DayWidget { background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 4px; }
    TaskWidget { background-color: white; border: 1px solid #d0d0d0; border-radius: 8px; padding: 5px; margin-bottom: 3px; }
    #WeekDayLabel { font-weight: bold; color: #555; padding-bottom: 5px; }
    #DateLabel { font-size: 11px; font-weight: bold; padding: 2px; color: #333; }
    
    /* Ghi đè kiểu nút bấm cho các nút trong lịch (Trước/Sau) */
    CalendarWidget QPushButton { 
        background-color: #f0f0f0; border: 1px solid #c0c0c0; 
        border-radius: 4px; padding: 5px 10px; font-weight: normal; 
    }
    CalendarWidget QPushButton:hover { background-color: #e0e0e0; }
    
    /* --- CSS cho cửa sổ chi tiết ngày (DayDetailDialog) --- */
    #DayDetailDialog { background-color: #f9f9f9; }
    #DateHeaderLabel { font-size: 18px; font-weight: bold; color: #333; padding: 10px; border-bottom: 2px solid #eee; }
    #TaskDetailItem { background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 12px; margin-bottom: 8px; }
    #NoteLabelInDialog { color: #555; font-style: italic; }
    #DayDetailDialog QPushButton { padding: 8px 16px; border-radius: 4px; background-color: #007bff; color: white; border: none; font-weight: bold; }
    #DayDetailDialog QPushButton:hover { background-color: #0056b3; }

    /* --- CSS cho tiêu đề nhóm --- */
    #GroupTitleLabel {
        font-size: 16pt;
        font-weight: bold;
        color: #444;
        padding-bottom: 2px;
    }
"""

class MainWindow(QMainWindow):
    """
        Cửa sổ chính của ứng dụng To-do List.
        Chứa thanh bên (SidePanel) và khu vực hiển thị nội dung (HomePage hoặc Calendar).
    """

    def __init__(self, user_id, user_name, default_role='Cá nhân', parent=None):
        """
            Khởi tạo cửa sổ chính.
        """
        super().__init__(parent)
        self.user_id = user_id
        self.user_name = user_name
        self.default_role = default_role
        self.current_view = 'personal'
        self.current_content = 'home'
        self.current_group_id = None
        self.current_group_name = None
        self.is_leader_of_current_group = False
        self._is_logging_out = False

        # Sử dụng hàm trợ giúp để lấy đường dẫn CSDL một cách an toàn
        self.db_path = _find_database_path()
        if not self.db_path:
            QMessageBox.critical(self, "Lỗi nghiêm trọng", "Không tìm thấy file database. Ứng dụng sẽ đóng.")
            # Dùng QTimer để đóng cửa sổ sau khi hàm __init__ hoàn tất
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, self.close)
            return

        self.setWindowTitle("To-do List")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(STYLESHEET)
        self.setObjectName("MainWindow")

        self.initUI()
        self.side_panel.set_user_info(self.user_name, self.default_role)
        self.side_panel.update_view(self.current_view, False)  # Khởi tạo với personal view, không phải leader
        self.home_widget.load_data()

    def closeEvent(self, event):
        """
        Hiển thị hộp thoại xác nhận khi người dùng cố gắng đóng cửa sổ chính bằng nút X.
        """
        if self._is_logging_out:
            event.accept()
            return

        reply = QMessageBox.question(
            self,
            "Xác nhận Thoát",
            "Bạn có chắc chắn muốn thoát khỏi ứng dụng chứ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def _prompt_for_exit(self):
        """
        Hàm này xử lý việc đăng xuất (Sign Out).
        """
        from login import LoginRegisterApp
        
        reply = QMessageBox.question(
            self,
            "Xác nhận Đăng xuất",
            "Bạn có chắc chắn muốn đăng xuất không?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Đặt cờ thành True trước khi đóng để bypass closeEvent
            self._is_logging_out = True
            self.close()
            # Mở lại cửa sổ đăng nhập
            self.login_window = LoginRegisterApp()
            self.login_window.show()

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
        
        # Panel bên phải, chứa tiêu đề nhóm và QStackedWidget
        right_panel_layout = QVBoxLayout()
        right_panel_layout.setContentsMargins(10, 0, 10, 10) # Thêm chút padding
        right_panel_layout.setSpacing(10)

        self.group_title_label = QLabel("Tên Nhóm")
        self.group_title_label.setObjectName("GroupTitleLabel")
        self.group_title_label.setFixedHeight(40)
        self.group_title_label.setAlignment(Qt.AlignCenter)
        right_panel_layout.addWidget(self.group_title_label)
        self.group_title_label.hide()

        # StackedWidget để chuyển đổi giữa trang chủ và lịch
        self.content_stack = QStackedWidget()
        self.content_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_panel_layout.addWidget(self.content_stack)
        self.main_layout.addLayout(right_panel_layout, 1)

        # Trang chủ
        self.home_widget = HomePageWidget(self.user_id)
        self.content_stack.addWidget(self.home_widget)

        # Khu vực lịch
        self.calendar_widget = CalendarWidget(self.user_id, self.db_path)
        self.content_stack.addWidget(self.calendar_widget)

        # Mặc định hiển thị trang chủ
        self.content_stack.setCurrentWidget(self.home_widget)
        
        # Kết nối các tín hiệu từ SidePanel
        self.side_panel.personal_area_requested.connect(self._handle_personal_view)
        self.side_panel.group_area_requested.connect(self._handle_group_view)
        self.side_panel.home_requested.connect(self._handle_home_view)
        self.side_panel.calendar_requested.connect(self._handle_calendar_view)
        self.side_panel.exit_requested.connect(self._prompt_for_exit)
        self.side_panel.member_list_requested.connect(self._show_member_list)
        self.side_panel.add_member_requested.connect(self._add_member)

    def _load_group_context(self, group_id, group_name):
        self.current_view = 'group'
        self.current_group_id = group_id
        self.current_group_name = group_name
        self.group_title_label.setText(f"Nhóm: {self.current_group_name}")
        self.group_title_label.show()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT leader_id FROM groups WHERE group_id = ?", (self.current_group_id,))
            leader_id = cursor.fetchone()[0]
            self.is_leader_of_current_group = (self.user_id == leader_id)
            role = "Quản trị viên" if self.is_leader_of_current_group else "Thành viên"
            self.side_panel.set_user_info(self.user_name, role)
            self.side_panel.update_view(self.current_view, self.is_leader_of_current_group)
            conn.close()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Không thể tải thông tin nhóm: {e}")
    
    def _handle_personal_view(self):
        """
            Xử lý việc chuyển đổi sang chế độ xem cá nhân.
        """
        print("Chuyển sang khu vực cá nhân...")
        self.current_view = 'personal'
        self.current_group_id = None # Reset thông tin nhóm
        self.is_leader_of_current_group = False
        self.group_title_label.hide()
        self.side_panel.set_user_info(self.user_name, self.default_role)
        self.side_panel.update_view('personal', False)  # Personal view, không có leader
        
        # Cập nhật dữ liệu cho trang hiện tại
        if self.current_content == 'home':
            self.home_widget.user_id = self.user_id
            self.home_widget.load_data()
        elif self.current_content == 'calendar':
            self.load_personal_tasks()

    def _handle_group_view(self):
        """
            Xử lý việc chuyển đổi sang chế độ xem nhóm.
            Mở hộp thoại để người dùng chọn nhóm.
        """
        print("Chuyển sang khu vực nhóm...")
        dialog = GroupSelectionDialog(self.user_id, self)
        if dialog.exec_() == QDialog.Accepted and dialog.selected_group:
            group_id, group_name = dialog.selected_group
            self._load_group_context(group_id, group_name)
            
            # Sau khi chọn nhóm, load dữ liệu tùy thuộc vào trang đang hiển thị
            if self.current_content == 'home':
                self.home_widget.user_id = self.user_id
                self.home_widget.load_data()
            elif self.current_content == 'calendar':
                self.load_group_tasks(group_id)
        else: # Nếu người dùng hủy hoặc không chọn nhóm, quay lại view cũ
            is_leader = self.is_leader_of_current_group if self.current_view == 'group' else False
            self.side_panel.update_view(self.current_view, is_leader)


    def _handle_home_view(self):
        """
            Xử lý việc chuyển đổi sang trang chủ.
        """
        print("Chuyển sang trang chủ...")
        self.current_content = 'home'
        self.content_stack.setCurrentWidget(self.home_widget)
        is_leader = self.is_leader_of_current_group if self.current_view == 'group' else False
        self.side_panel.update_view(self.current_view, is_leader)
        
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
        is_leader = self.is_leader_of_current_group if self.current_view == 'group' else False
        self.side_panel.update_view(self.current_view, is_leader)
        
        # Cập nhật dữ liệu cho lịch
        if self.current_view == 'personal':
            self.load_personal_tasks()
        elif self.current_view == 'group' and self.current_group_id:
            self.load_group_tasks(self.current_group_id)

    def _show_member_list(self):
        if self.current_group_id:
            dialog = MemberListDialog(self.current_group_id, self)
            dialog.exec_()
    
    def _add_member(self):
        if self.current_group_id and self.is_leader_of_current_group:
            dialog = AddMemberDialog(self.current_group_id, self)
            dialog.exec_()

    def load_personal_tasks(self):
        """
            Tải và hiển thị các công việc cá nhân từ cơ sở dữ liệu.
        """
        tasks_by_day = {}
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT due_at, title, is_done, note FROM tasks WHERE user_id = ?", (self.user_id,))
            tasks = cursor.fetchall()

            for due_at_str, title, is_done, note in tasks:
                if due_at_str:
                    task_date = QDate.fromString(due_at_str[:10], "yyyy-MM-dd")
                    if task_date.year() == self.calendar_widget.current_date.year and \
                       task_date.month() == self.calendar_widget.current_date.month:
                        day = task_date.day()
                        if day not in tasks_by_day:
                            tasks_by_day[day] = []
                        tasks_by_day[day].append({'title': title, 'is_done': is_done, 'note': note})

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
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT gt.due_at, gt.title, gt.is_done, gt.note, u.user_name as assignee_name
                FROM group_tasks gt
                LEFT JOIN users u ON gt.assignee_id = u.user_id
                WHERE gt.group_id = ?
            """, (group_id,))
            tasks = cursor.fetchall()

            for due_at_str, title, is_done, note, assignee_name in tasks:
                if due_at_str:
                    task_date = QDate.fromString(due_at_str[:10], "yyyy-MM-dd")
                    if task_date.year() == self.calendar_widget.current_date.year and \
                       task_date.month() == self.calendar_widget.current_date.month:
                        day = task_date.day()
                        if day not in tasks_by_day:
                            tasks_by_day[day] = []
                        tasks_by_day[day].append({
                            'title': title, 
                            'is_done': is_done, 
                            'note': note,
                            'assignee_name': assignee_name or "Chưa phân công"
                        })

            self.calendar_widget.populate_calendar(tasks_by_day)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Lỗi khi tải công việc nhóm: {e}")
        finally:
            if conn:
                conn.close()