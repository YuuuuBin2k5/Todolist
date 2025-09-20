# FILE: src/MainMenu/main_windows.py

import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QMessageBox, QDialog
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtCore import Qt

from MainMenu.side_panel import SidePanel
from MainMenu.calendar_widget import CalendarWidget
from MainMenu.group_dialogs import GroupSelectionDialog, MemberListDialog, AddMemberDialog

# [SỬA LỖI] STYLESHEET đã được chuẩn hóa
STYLESHEET = """
    #MainWindow { background-color: #f0f0f0; } 
    #SidePanel { background-color: #e9e9e9; border-right: 1px solid #d0d0d0; } 
    #InfoValueLabel { font-weight: bold; font-size: 14px; }
    
    #SidePanel QPushButton { 
        background-color: #ffffff; 
        border: 1px solid #c0c0c0; 
        border-radius: 15px; 
        padding: 10px; 
        font-weight: bold; 
    }
    #SidePanel QPushButton:hover { background-color: #f5f5f5; }
    #SidePanel QPushButton:disabled {
        background-color: #e0e0e0;
        color: #888888;
        border-color: #b0b0b0;
    }
    
    #ExitButton { background-color: #ffe0e0; border-color: #ffaaaa; }
    #ExitButton:hover { background-color: #ffcccc; }
    
    DayWidget { background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 4px; }
    TaskWidget { background-color: white; border: 1px solid #d0d0d0; border-radius: 8px; padding: 5px; margin-bottom: 3px; }
    #WeekDayLabel { font-weight: bold; color: #555; padding-bottom: 5px; }
    .DateLabel { font-size: 11px; font-weight: bold; padding: 2px; color: #333; }
    CalendarWidget QPushButton { background-color: #f0f0f0; border: 1px solid #c0c0c0; border-radius: 4px; padding: 5px 10px; font-weight: normal; }
    CalendarWidget QPushButton:hover { background-color: #e0e0e0; }
    
    #DayDetailDialog { background-color: #f9f9f9; }
    #DateHeaderLabel { font-size: 18px; font-weight: bold; color: #333; padding: 10px; border-bottom: 2px solid #eee; }
    
    #GroupTitleLabel {
        font-size: 16pt;
        font-weight: bold;
        color: #444;
        padding-bottom: 2px;
    }

    #TaskDetailItem { background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 12px; margin-bottom: 8px; }
    #NoteLabelInDialog { color: #555; font-style: italic; }
    #DayDetailDialog QPushButton { padding: 8px 16px; border-radius: 4px; background-color: #007bff; color: white; border: none; font-weight: bold; }
    #DayDetailDialog QPushButton:hover { background-color: #0056b3; }
"""

class MainWindow(QMainWindow):
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.user_id = user_data[0]
        self.user_name = user_data[1]
        self.default_role = "Quản trị viên"
        self.current_view = 'personal'
        self.current_group_id = None
        self.current_group_name = None
        self.is_leader_of_current_group = False

        self.setWindowTitle("Dashboard - Calendar")
        self.setGeometry(100, 100, 1400, 900)
        self.setObjectName("MainWindow")
        self.setStyleSheet(STYLESHEET)
        
        self.initUI()
        self._handle_personal_view()

    def initUI(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.side_panel = SidePanel()
        main_layout.addWidget(self.side_panel)
        
        right_panel_layout = QVBoxLayout()
        # [SỬA LỖI] Xóa lề và khoảng cách để kiểm soát chặt chẽ
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        right_panel_layout.setSpacing(0)
        main_layout.addLayout(right_panel_layout, 1)

        self.group_title_label = QLabel("Tên Nhóm")
        self.group_title_label.setObjectName("GroupTitleLabel")
        self.group_title_label.setFixedHeight(40)
        right_panel_layout.addWidget(self.group_title_label, 0, Qt.AlignCenter)
        self.group_title_label.hide()

        # Thêm một khoảng trống nhỏ (5px) ở trên title
        right_panel_layout.addSpacing(5)
        right_panel_layout.addWidget(self.group_title_label)
        # Thêm một khoảng trống nhỏ (5px) ở dưới title
        right_panel_layout.addSpacing(5)

        self.calendar = CalendarWidget()
        right_panel_layout.addWidget(self.calendar)
        # right_panel_layout.addStretch(1)

        self.side_panel.personal_area_requested.connect(self._handle_personal_view)
        self.side_panel.group_area_requested.connect(self._handle_group_view)
        self.side_panel.member_list_requested.connect(self._show_member_list)
        self.side_panel.add_member_requested.connect(self._add_member)
        self.side_panel.exit_btn.clicked.connect(self.close)

    def _load_group_context(self, group_id, group_name):
        self.current_view = 'group'
        self.current_group_id = group_id
        self.current_group_name = group_name
        self.group_title_label.setText(f"Nhóm: {self.current_group_name}")
        self.group_title_label.show()
        
        try:
            conn = sqlite3.connect("todolist_database.db")
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
        self.current_view = 'personal'
        self.group_title_label.hide()
        self.side_panel.set_user_info(self.user_name, "Quản trị viên")
        self.side_panel.update_view(self.current_view)
        
    def _handle_group_view(self):
        dialog = GroupSelectionDialog(self.user_id, self)
        if dialog.exec_() == QDialog.Accepted and dialog.selected_group:
            group_id, group_name = dialog.selected_group
            self._load_group_context(group_id, group_name)
    
    def _show_member_list(self):
        if self.current_group_id:
            dialog = MemberListDialog(self.current_group_id, self)
            dialog.exec_()
    
    def _add_member(self):
        if self.current_group_id and self.is_leader_of_current_group:
            dialog = AddMemberDialog(self.current_group_id, self)
            dialog.exec_()