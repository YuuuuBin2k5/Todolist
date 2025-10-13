# -*- coding: utf-8 -*-
"""
    Cửa sổ chính chạy Main Menu.
    Đây là file đã được hợp nhất từ hai phiên bản có xung đột.
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, 
                             QVBoxLayout, QLabel, QMessageBox, 
                             QSizePolicy, QStackedWidget, QDialog)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QGuiApplication
import shutil
from pathlib import Path
import os

# --- Nhập các module và widget tùy chỉnh của dự án ---
from MainMenu.side_panel import SidePanel
from MainMenu.calendar_widget import CalendarWidget
from MainMenu.statistics_page import StatisticsPage
from Managers.database_manager import Database
from MainMenu.home_page import DoNowView
from MainMenu.group_dialogs import GroupSelectionDialog, MemberListDialog, AddMemberDialog
from config import *


# ==============================================================================
# STYLESHEET (QSS) - Dùng để định dạng giao diện cho toàn bộ cửa sổ
# ==============================================================================
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

# ==============================================================================
# LỚP 1: MainWindow - Cửa sổ chính của ứng dụng
# ==============================================================================
class MainWindow(QMainWindow):
    """
        Cửa sổ chính của ứng dụng To-do List.
        Chứa thanh bên (SidePanel) và khu vực hiển thị nội dung (HomePage hoặc Calendar).
        Đây là "trung tâm điều khiển" của ứng dụng sau khi người dùng đăng nhập.
    """

    def __init__(self, user_id, user_name, default_role='Cá nhân', parent=None):
        """
            Khởi tạo cửa sổ chính.
        """
        super().__init__(parent)

        # --- Các biến trạng thái (state) của cửa sổ ---
        self.user_id = user_id
        self.user_name = user_name
        self.default_role = default_role

        self.current_view = 'personal' # 'personal' hoặc 'group'
        self.current_content = 'home' # 'home' hoặc 'calendar' hoặc 'statistics'

        self.current_group_id = None
        self.current_group_name = None
        self.is_leader_of_current_group = False
        self._is_logging_out = False # Cờ để kiểm soát việc đăng xuất

        # Tạo một đối tượng quản lý CSDL duy nhất để chia sẻ cho các widget con
        self.db = Database()


         # Cài đặt thuộc tính cơ bản cho cửa sổ
        self.setWindowTitle("To-do List")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(STYLESHEET)
        self.setObjectName("MainWindow")

        self.initUI() # Bắt đầu xây dựng giao diện người dùng
        # Đặt cửa sổ chính ở giữa màn hình
        self.vi_tri_screen()
        
        # Cập nhật thông tin ban đầu cho SidePanel
        self.side_panel.set_user_info(self.user_name, self.default_role)
        self.side_panel.update_view(self.current_view, False)  # Khởi tạo với personal view, không phải leader
        # Ensure home widget uses the shared Database instance
        try:
            if hasattr(self.home_widget, 'load_data_from_db'):
                self.home_widget.load_data_from_db()
        except Exception:
            pass

    def initUI(self):
        """
            Thiết lập giao diện người dùng cho cửa sổ chính.
        """
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Layout chính, chia cửa sổ thành 2 phần: thanh bên và nội dung
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

        # Nhãn hiển thị tên nhóm (mặc định sẽ bị ẩn)
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

        # Khu vực trang chủ
        self.home_widget = DoNowView(self.user_id, db=self.db)
        self.content_stack.addWidget(self.home_widget)

        # Khu vực thống kê
        self.statistics_page = StatisticsPage()
        self.content_stack.addWidget(self.statistics_page)

        # Khu vực lịch
        self.calendar_widget = CalendarWidget(self.user_id, self.db)
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
        self.side_panel.statistics_requested.connect(self.show_statistics_page)
        
        # Kết nối tín hiệu avatar_changed để MainWindow lưu ảnh đại diện vào hệ thống tệp
        self.side_panel.avatar_changed.connect(self._on_avatar_changed)

        # Sau khi đã thiết lập SidePanel, cố gắng load avatar nếu đã tồn tại
        self.load_user_avatar_if_exists()
    
    def vi_tri_screen(self):
        """Chỉnh cửa sổ chính phù hợp vị trí màn hình."""
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return
        screen_geo = screen.availableGeometry()
        win_geo = self.frameGeometry()
        center_point = screen_geo.center()
        win_geo.moveCenter(center_point)
        self.move(win_geo.topLeft())

    def showEvent(self, event):
        """Đảm bảo căn giữa ngay khi cửa sổ hiển thị (frameGeometry đã chính xác)."""
        super().showEvent(event)
        try:
            self.vi_tri_screen()
        except Exception:
            pass

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

    def _load_group_context(self, group_id, group_name):
        self.current_view = 'group'
        self.current_group_id = group_id
        self.current_group_name = group_name
        self.group_title_label.setText(f"Nhóm: {self.current_group_name}")
        self.group_title_label.show()
        
        try:
            leader_id = self.db.get_group_leader(self.current_group_id)
            self.is_leader_of_current_group = (self.user_id == leader_id)
            role = "Trưởng Nhóm" if self.is_leader_of_current_group else "Thành viên"
            self.side_panel.set_user_info(self.user_name, role)
            self.side_panel.update_view(self.current_view, self.is_leader_of_current_group)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Không thể tải thông tin nhóm: {e}")
            return

        # Inform calendar about group context and switch its view mode
        try:
            self.calendar_widget.set_group_context(self.current_group_id)
            self.calendar_widget.switch_view_mode('group')
        except Exception:
            pass
    
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
            self.home_widget.load_data_from_db()
        elif self.current_content == 'calendar':
            # Ensure calendar knows we're in personal mode
            try:
                self.calendar_widget.switch_view_mode('personal')
            except Exception:
                pass
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
            try:
                self.calendar_widget.switch_view_mode('personal')
            except Exception:
                pass
            self.load_personal_tasks()
        elif self.current_view == 'group' and self.current_group_id:
            try:
                self.calendar_widget.set_group_context(self.current_group_id)
                self.calendar_widget.switch_view_mode('group')
            except Exception:
                pass
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
            month_str = self.calendar_widget.current_date.strftime('%Y-%m')
            tasks = self.db.get_tasks_for_user_month(self.user_id, month_str)
            for task in tasks:
                # task: (task_id, title, is_done, note, due_at)
                task_id, title, is_done, note, due_at_str = task
                if due_at_str:
                    task_date = QDate.fromString(due_at_str[:10], "yyyy-MM-dd")
                    if task_date.year() == self.calendar_widget.current_date.year and \
                       task_date.month() == self.calendar_widget.current_date.month:
                        day = task_date.day()
                        if day not in tasks_by_day:
                            tasks_by_day[day] = []
                        tasks_by_day[day].append({'task_id': task_id, 'title': title, 'is_done': is_done, 'note': note, 'due_at': due_at_str})

            # Also include group tasks assigned to this user in the same month
            try:
                month_str = self.calendar_widget.current_date.strftime('%Y-%m')
                group_tasks = self.db.get_group_tasks_for_user_month(self.user_id, month_str)
                for gt in group_tasks:
                    # gt: (task_id, group_id, assignee_id, title, note, is_done, due_at)
                    g_task_id, g_group_id, g_assignee_id, g_title, g_note, g_is_done, g_due_at = gt
                    if g_due_at:
                        g_date = QDate.fromString(g_due_at[:10], "yyyy-MM-dd")
                        if g_date.year() == self.calendar_widget.current_date.year and g_date.month() == self.calendar_widget.current_date.month:
                            g_day = g_date.day()
                            if g_day not in tasks_by_day:
                                tasks_by_day[g_day] = []
                            assignee_name = self.db.get_user_name(g_assignee_id) or "Chưa phân công"
                            tasks_by_day[g_day].append({
                                'task_id': g_task_id,
                                'title': g_title,
                                'is_done': g_is_done,
                                'note': g_note,
                                'due_at': g_due_at,
                                'assignee_name': assignee_name
                            })
            except Exception:
                pass

            self.calendar_widget.populate_calendar(tasks_by_day)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Lỗi khi tải công việc cá nhân: {e}")

    def load_group_tasks(self, group_id):
        """
            Tải và hiển thị các công việc nhóm từ cơ sở dữ liệu.
        """
        tasks_by_day = {}
        try:
            month_str = self.calendar_widget.current_date.strftime('%Y-%m')
            all_tasks = self.db.get_group_tasks_for_month(group_id, month_str)
            for task in all_tasks:
                # (task_id, group_id, assignee_id, title, note, is_done, due_at)
                task_id, group_id, assignee_id, title, note, is_done, due_at_str = task
                if due_at_str:
                    task_date = QDate.fromString(due_at_str[:10], "yyyy-MM-dd")
                    if task_date.year() == self.calendar_widget.current_date.year and \
                       task_date.month() == self.calendar_widget.current_date.month:
                        day = task_date.day()
                        if day not in tasks_by_day:
                            tasks_by_day[day] = []
                        assignee_name = self.db.get_user_name(assignee_id) or "Chưa phân công"
                        tasks_by_day[day].append({
                            'task_id': task_id,
                            'title': title,
                            'is_done': is_done,
                            'note': note,
                            'due_at': due_at_str,
                            'assignee_name': assignee_name
                        })

            self.calendar_widget.populate_calendar(tasks_by_day)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Lỗi khi tải công việc nhóm: {e}")

    def show_statistics_page(self):
        """
        Hiển thị trang thống kê công việc cá nhân VÀ chi tiết từng nhóm.
        """
        print("Chuyển sang trang Thống kê chi tiết...")
        
        if self.current_view != 'personal':
            self._handle_personal_view()

        # 1. Lấy dữ liệu thống kê cá nhân
        personal_stats_data = self.db._get_personal_completion_stats(self.user_id)

        # 2. Lấy danh sách dữ liệu thống kê của từng nhóm
        group_stats_list = self.db._get_stats_per_group(self.user_id)

        # 3. Cập nhật toàn bộ giao diện thống kê
        self.statistics_page.update_all_stats(personal_stats_data, group_stats_list)
        
        # 4. Hiển thị trang thống kê
        self.content_stack.setCurrentWidget(self.statistics_page)

    def _on_avatar_changed(self, src_path: str):
        """
        Sao chép ảnh đại diện người dùng từ src_path vào thư mục assets/avatars
        với tên định dạng user_{user_id}.ext (giữ nguyên đuôi gốc).
        Nếu đã có ảnh đại diện cho user_id, ghi đè lên.
        """
        try:
            src = Path(src_path)
            if not src.exists():
                return
            avatars_dir = Path(__file__).resolve().parents[2] / 'src' / 'assets' / 'avatars'
            avatars_dir.mkdir(parents=True, exist_ok=True)
            ext = src.suffix.lower() or '.png'
            dest = avatars_dir / f'user_{self.user_id}{ext}'
            # Overwrite existing avatar for this user
            shutil.copyfile(str(src), str(dest))
            try:
                # Tell side panel to show the newly saved avatar
                self.side_panel.set_avatar_from_path(str(dest))
            except Exception:
                pass
        except Exception as e:
            QMessageBox.warning(self, "Lỗi lưu ảnh", f"Không thể lưu ảnh đại diện: {e}")

    def load_user_avatar_if_exists(self):
        """
        Trên hệ thống tệp, tìm ảnh đại diện cho user_id trong assets/avatars.
        Nếu tìm thấy, tải ảnh này vào SidePanel.
        """
        try:
            avatars_dir = Path(__file__).resolve().parents[2] / 'src' / 'assets' / 'avatars'
            if not avatars_dir.exists():
                return
            # look for any extension (png/jpg/jpeg/bmp)
            pattern = f'user_{self.user_id}.*'
            matches = list(avatars_dir.glob(f'user_{self.user_id}.*'))
            if not matches:
                return
            # Prefer common formats by order
            preferred = None
            for ext in ['.png', '.jpg', '.jpeg', '.bmp']:
                for m in matches:
                    if m.suffix.lower() == ext:
                        preferred = m
                        break
                if preferred:
                    break
            if not preferred:
                preferred = matches[0]
            self.side_panel.set_avatar_from_path(str(preferred))
        except Exception:
            pass