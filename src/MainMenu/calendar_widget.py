"""
    Chứa Widget chính và logic của nó       ---> CalendarWidget
"""

import calendar
from datetime import datetime, timedelta
import sqlite3
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGridLayout, QApplication
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from MainMenu.components import DayWidget, TaskWidget

calendar.setfirstweekday(calendar.SUNDAY)

VIETNAMESE_MONTHS = [
    "Tháng Một", "Tháng Hai", "Tháng Ba", "Tháng Tư", "Tháng Năm", "Tháng Sáu",
    "Tháng Bảy", "Tháng Tám", "Tháng Chín", "Tháng Mười", "Tháng Mười Một", "Tháng Mười Hai"
]

class CalendarWidget(QWidget):
    """
        Widget này chứa toàn bộ giao diện và logic của lịch,
        để hiển thị ở khu vực bên phải của cửa sổ chính.
    """
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.current_date = datetime.now()
        
        # Lưu thông tin về người dùng và chế độ xem
        self.user_id = user_id
        self.group_id = None
        self.view_mode = 'personal' # Mặc định là 'personal'
        
        self.initUI()
        self.populate_calendar()

    def switch_view_mode(self, view_mode, user_id, group_id=None):
        """Hàm để chuyển đổi chế độ xem và tải lại lịch."""
        self.view_mode = view_mode
        self.user_id = user_id
        self.group_id = group_id
        self.populate_calendar() # Tải lại dữ liệu cho chế độ xem mới

    def initUI(self):
        self.main_layout = QVBoxLayout(self)
        
        # --- Tạo thanh điều hướng tháng (VD: < Tháng Chín 2025 >) ---
        nav_layout = QHBoxLayout()
        self.prev_month_btn = QPushButton("< Trước")
        self.prev_month_btn.clicked.connect(self.prev_month)
        
        self.month_label = QLabel()
        self.month_label.setAlignment(Qt.AlignCenter)
        
        title_font = QApplication.instance().font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.month_label.setFont(title_font)
        
        self.next_month_btn = QPushButton("Sau >")
        self.next_month_btn.clicked.connect(self.next_month)
        
        nav_layout.addWidget(self.prev_month_btn)
        nav_layout.addWidget(self.month_label, 1)
        nav_layout.addWidget(self.next_month_btn)
        self.main_layout.addLayout(nav_layout)
        
        # --- Tạo lưới (grid) để chứa các ngày trong tháng ---
        self.grid_layout = QGridLayout()
        self.main_layout.addLayout(self.grid_layout)
        self.setup_week_headers()

    def setup_week_headers(self):
        """Tạo các nhãn cho tiêu đề các ngày trong tuần."""
        days = ["Chủ Nhật", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy"]
        for i, day in enumerate(days):
            label = QLabel(day)
            label.setObjectName("WeekDayLabel")
            label.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(label, 0, i)

    def clear_calendar(self):
        """Xóa tất cả các DayWidget cũ khỏi lưới trước khi vẽ tháng mới."""
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if isinstance(widget, DayWidget):
                widget.deleteLater()
                
    def populate_calendar(self):
        """Vẽ lại toàn bộ lịch cho tháng hiện tại."""
        self.clear_calendar()
        self.setup_week_headers()
        
        month_name = VIETNAMESE_MONTHS[self.current_date.month - 1]
        self.month_label.setText(f"{month_name} {self.current_date.year}")
        
        month_calendar = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        
        for week_num, week_data in enumerate(month_calendar):
            for day_num, day_data in enumerate(week_data):
                if day_data != 0:
                    day_widget = DayWidget(
                        str(day_data), 
                        self.current_date.year, 
                        self.current_date.month,
                        user_id=self.user_id,
                        group_id=self.group_id,
                        view_mode=self.view_mode
                    )
                    self.grid_layout.addWidget(day_widget, week_num + 1, day_num)
        
        self.load_tasks_from_db()

    def load_tasks_from_db(self):
        """Tải công việc từ CSDL và thêm vào các DayWidget tương ứng."""
        if self.view_mode == 'group' and self.group_id is None:
            return

        try:
            conn = sqlite3.connect("todolist_database.db")
            cursor = conn.cursor()
            
            month_str = self.current_date.strftime('%Y-%m')
            
            if self.view_mode == 'personal':
                query = "SELECT task_id, title, is_done, note, due_at FROM tasks WHERE user_id = ? AND strftime('%Y-%m', due_at) = ?"
                params = (self.user_id, month_str)
            else:
                query = "SELECT task_id, title, is_done, note, due_at FROM group_tasks WHERE group_id = ? AND strftime('%Y-%m', due_at) = ?"
                params = (self.group_id, month_str)

            cursor.execute(query, params)
            tasks_for_month = cursor.fetchall()
            conn.close()

            tasks_by_day = {}
            for task_id, title, is_done, note, due_at_str in tasks_for_month:
                day = datetime.fromisoformat(due_at_str).day
                if day not in tasks_by_day:
                    tasks_by_day[day] = []
                tasks_by_day[day].append({'id': task_id, 'title': title, 'is_done': bool(is_done), 'note': note or ""})

            for i in range(self.grid_layout.count()):
                widget = self.grid_layout.itemAt(i).widget()
                if isinstance(widget, DayWidget):
                    day_number = widget.day
                    if day_number in tasks_by_day:
                        for task_data in tasks_by_day[day_number]:
                            task_widget = TaskWidget(
                                text=task_data['title'],
                                is_done=task_data['is_done'],
                                note=task_data['note'],
                                task_id=task_data['id'],
                                view_mode=self.view_mode
                            )
                            widget.add_task(task_widget)
        except sqlite3.Error as e:
            print(f"Lỗi khi tải công việc từ CSDL: {e}")
    
    def prev_month(self):
        self.current_date = self.current_date.replace(day=1) - timedelta(days=1)
        self.populate_calendar()

    def next_month(self):
        days_in_month = calendar.monthrange(self.current_date.year, self.current_date.month)[1]
        self.current_date = self.current_date.replace(day=days_in_month) + timedelta(days=1)
        self.populate_calendar()