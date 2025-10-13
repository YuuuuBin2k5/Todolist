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
import logging

# --- Nhập các module và widget tùy chỉnh của dự án ---
from MainMenu.side_panel import SidePanel
from MainMenu.calendar_widget import CalendarWidget
from MainMenu.statistics_page import StatisticsPage
from Managers.database_manager import Database
from MainMenu.home_page import DoNowView
from MainMenu.group_dialogs import GroupSelectionDialog, MemberListDialog, AddMemberDialog
from config import *
import datetime


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
        self.setGeometry(100, 100, 1600, 900)
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
        # Log initial window size after loading data for diagnostics
        try:
            self._log_window_size(event_note='init_load')
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
        try:
            # Protect against child widgets requesting overly large sizeHints by
            # capping the content area to the available screen width minus the side panel.
            screen = QGuiApplication.primaryScreen()
            if screen and hasattr(self, 'content_stack'):
                try:
                    screen_geo = screen.availableGeometry()
                    screen_w = screen_geo.width()
                    side_w = self.side_panel.frameGeometry().width() if hasattr(self, 'side_panel') else 300
                    # leave some margin for window frame
                    avail = max(400, screen_w - side_w - 80)
                    # apply cap to content stack and calendar widget to prevent expansion
                    try:
                        self.content_stack.setMaximumWidth(avail)
                    except Exception:
                        pass
                    try:
                        if hasattr(self, 'calendar_widget') and self.calendar_widget:
                            self.calendar_widget.setMaximumWidth(avail)
                    except Exception:
                        pass
                except Exception:
                    pass
            self._log_window_size(event_note='show')
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

        if self.current_content == 'home':
            self.home_widget.set_view_context(
                mode='group', 
                group_id=self.current_group_id, 
                is_leader=self.is_leader_of_current_group
            )
        
        # Cập nhật context cho lịch khi đang ở trang lịch
        if self.current_content == 'calendar':
            try:
                self.calendar_widget.set_group_context(self.current_group_id)
                self.calendar_widget.switch_view_mode('group')
            except Exception:
                pass
        # Log size when switching to group context for diagnostics
        try:
            self._log_window_size(event_note=f'load_group_{self.current_group_id}')
        except Exception:
            pass

    def _log_window_size(self, event_note=''):
        """Append a small diagnostic record with timestamp, user and window geometry."""
        try:
            assets_dir = Path(os.path.dirname(os.path.dirname(__file__))) / 'assets'
            assets_dir.mkdir(parents=True, exist_ok=True)
            log_path = assets_dir / 'window_sizes.log'
            w = self.frameGeometry().width()
            h = self.frameGeometry().height()
            # screen / DPI info
            try:
                screen = QGuiApplication.primaryScreen()
                screen_geo = screen.availableGeometry() if screen else None
                screen_w = screen_geo.width() if screen_geo else 0
                screen_h = screen_geo.height() if screen_geo else 0
                dpr = screen.devicePixelRatio() if screen else 1
            except Exception:
                screen_w = screen_h = dpr = 0
            # window state
            try:
                is_max = bool(self.isMaximized())
                is_full = bool(self.isFullScreen())
            except Exception:
                is_max = is_full = False
            # sizes of important child widgets
            try:
                content_sz = self.content_stack.frameGeometry() if hasattr(self, 'content_stack') else None
                content_w = content_sz.width() if content_sz else 0
                content_h = content_sz.height() if content_sz else 0
            except Exception:
                content_w = content_h = 0
            # sizeHint / minimumSizeHint diagnostics for content and key children
            try:
                content_hint = self.content_stack.sizeHint() if hasattr(self, 'content_stack') else None
                content_hint_w = content_hint.width() if content_hint else 0
                content_hint_h = content_hint.height() if content_hint else 0
                content_min = self.content_stack.minimumSizeHint() if hasattr(self, 'content_stack') else None
                content_min_w = content_min.width() if content_min else 0
                content_min_h = content_min.height() if content_min else 0
            except Exception:
                content_hint_w = content_hint_h = content_min_w = content_min_h = 0
            try:
                side_sz = self.side_panel.frameGeometry() if hasattr(self, 'side_panel') else None
                side_w = side_sz.width() if side_sz else 0
                side_h = side_sz.height() if side_sz else 0
            except Exception:
                side_w = side_h = 0
            # home widget diagnostics
            try:
                hw = getattr(self, 'home_widget', None)
                hw_hint = hw.sizeHint() if hw else None
                hw_hint_w = hw_hint.width() if hw_hint else 0
                hw_hint_h = hw_hint.height() if hw_hint else 0
            except Exception:
                hw_hint_w = hw_hint_h = 0
            try:
                tasks_c = getattr(hw, 'tasks_container', None)
                tc_hint = tasks_c.sizeHint() if tasks_c else None
                tc_hint_w = tc_hint.width() if tc_hint else 0
                tc_hint_h = tc_hint.height() if tc_hint else 0
            except Exception:
                tc_hint_w = tc_hint_h = 0
            # calendar widget diagnostics
            try:
                cal = getattr(self, 'calendar_widget', None)
                cal_hint = cal.sizeHint() if cal else None
                cal_hint_w = cal_hint.width() if cal_hint else 0
                cal_hint_h = cal_hint.height() if cal_hint else 0
            except Exception:
                cal_hint_w = cal_hint_h = 0
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            user_info = f"user_id={self.user_id};user_name={self.user_name}"
            content = (
                f"{now}\t{event_note}\t{user_info}\twidth={w}\theight={h}"
                f"\tscreen={screen_w}x{screen_h}\tdpr={dpr}\tis_max={is_max}\tis_full={is_full}"
                f"\tcontent={content_w}x{content_h}\tside={side_w}x{side_h}"
                f"\tcontent_hint={content_hint_w}x{content_hint_h}\tcontent_min={content_min_w}x{content_min_h}"
                f"\thome_hint={hw_hint_w}x{hw_hint_h}\ttasks_hint={tc_hint_w}x{tc_hint_h}\tcal_hint={cal_hint_w}x{cal_hint_h}"
                f"\n"
            )
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(content)
            # also echo to stdout so running the app shows the record in console
            try:
                logging.debug('WINDOW_LOG: %s', content.strip())
            except Exception:
                pass
        except Exception:
            pass
    
    def _handle_personal_view(self):
        """
            Xử lý việc chuyển đổi sang chế độ xem cá nhân.
        """
        logging.debug("Chuyển sang khu vực cá nhân...")
        self.current_view = 'personal'
        self.current_group_id = None # Reset thông tin nhóm
        self.is_leader_of_current_group = False
        self.group_title_label.hide()
        self.side_panel.set_user_info(self.user_name, self.default_role)
        self.side_panel.update_view('personal', False)  # Personal view, không có leader
        
        # Cập nhật dữ liệu cho trang hiện tại
        if self.current_content == 'home':
            self.home_widget.user_id = self.user_id
            # Ensure home page is reset to personal context and reload data
            try:
                self.home_widget.set_view_context(mode='personal')
            except Exception:
                pass
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
        logging.debug("Chuyển sang khu vực nhóm...")
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
        logging.debug("Chuyển sang trang chủ...")
        self.current_content = 'home'
        self.content_stack.setCurrentWidget(self.home_widget)
        is_leader = self.is_leader_of_current_group if self.current_view == 'group' else False
        self.side_panel.update_view(self.current_view, is_leader)
        
        # Cập nhật dữ liệu cho trang chủ
        self.home_widget.user_id = self.user_id
        self.home_widget.load_data()

        if self.current_view == 'personal':
            self.home_widget.set_view_context(mode='personal')
        elif self.current_view == 'group':
            self.home_widget.set_view_context(
                mode='group',
                group_id=self.current_group_id,
                is_leader=self.is_leader_of_current_group
            )

    def _handle_calendar_view(self):
        """
            Xử lý việc chuyển đổi sang lịch.
        """
        logging.debug("Chuyển sang lịch...")
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
            # Personal view should display only personal tasks.
            # Do not include group tasks here; group tasks are displayed via the group view.
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
            # Determine whether current user is leader of this group
            try:
                leader_id = self.db.get_group_leader(group_id)
            except Exception:
                leader_id = None

            for task in all_tasks:
                # (task_id, group_id, assignee_id, title, note, is_done, due_at)
                task_id, group_id, assignee_id, title, note, is_done, due_at_str = task
                # If current user is not leader, only include tasks assigned to this user
                if leader_id is None or self.user_id != leader_id:
                    if assignee_id is None or assignee_id != self.user_id:
                        continue
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
        logging.debug("Chuyển sang trang Thống kê chi tiết...")
        
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
            # Remove any existing avatar files for this user (different extensions)
            for old in avatars_dir.glob(f'user_{self.user_id}.*'):
                old.unlink()
            ext = src.suffix.lower() or '.png'
            dest = avatars_dir / f'user_{self.user_id}{ext}'
            # Copy new avatar into place
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