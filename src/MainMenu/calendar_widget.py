# Trong file MainMenu/calendar_widget.py

import sqlite3
import calendar
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGridLayout, QApplication, QMessageBox
from PyQt5.QtCore import Qt
from MainMenu.components import DayWidget, TaskWidget, GroupTaskWidget

calendar.setfirstweekday(calendar.SUNDAY)

VIETNAMESE_MONTHS = [
    "Tháng Một", "Tháng Hai", "Tháng Ba", "Tháng Tư", "Tháng Năm", "Tháng Sáu",
    "Tháng Bảy", "Tháng Tám", "Tháng Chín", "Tháng Mười", "Tháng Mười Một", "Tháng Mười Hai"
]

class CalendarWidget(QWidget):
    def __init__(self, user_id, db_path, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.db_path = db_path
        self.current_date = datetime.now()
        
        # [MỚI] Thêm trạng thái để biết đang xem lịch cá nhân hay nhóm
        self.current_view_mode = 'personal' 
        self.user_names_cache = {} # Cache để lưu tên user, tránh query nhiều lần

        self.initUI()
        self.populate_calendar()

    # [MỚI] Hàm để chuyển đổi chế độ xem
    def switch_view_mode(self, mode):
        print(f"CalendarWidget chuyển sang chế độ: {mode}")
        self.current_view_mode = mode
        self.populate_calendar() # Tải lại lịch với chế độ mới

    def initUI(self):
        # ... (hàm initUI giữ nguyên, không cần thay đổi) ...
        self.main_layout = QVBoxLayout(self)
        nav_layout = QHBoxLayout()
        self.prev_month_btn = QPushButton("< Trước")
        self.prev_month_btn.clicked.connect(self.prev_month)
        self.month_label = QLabel()
        self.month_label.setAlignment(Qt.AlignCenter)
        font = self.month_label.font()
        font.setPointSize(18)
        font.setBold(True)
        self.month_label.setFont(font)
        self.next_month_btn = QPushButton("Sau >")
        self.next_month_btn.clicked.connect(self.next_month)
        nav_layout.addWidget(self.prev_month_btn)
        nav_layout.addWidget(self.month_label, 1)
        nav_layout.addWidget(self.next_month_btn)
        self.main_layout.addLayout(nav_layout)
        self.grid_layout = QGridLayout()
        self.main_layout.addLayout(self.grid_layout)

    def setup_week_headers(self):
        """
            Tạo các nhãn cho tiêu đề các ngày trong tuần.
        """
        days = ["Chủ Nhật", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy"]
        for i, day in enumerate(days):
            label = QLabel(day)
            label.setObjectName("WeekDayLabel")
            label.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(label, 0, i) # Thêm vào hàng 0, cột i

    def clear_calendar(self):
        """
            Xóa tất cả các DayWidget cũ khỏi lưới trước khi vẽ tháng mới.
        """
        # Duyệt ngược để tránh lỗi khi xóa item
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            # Chỉ xóa các widget là DayWidget (để giữ lại tiêu đề tuần)
            if isinstance(widget, DayWidget):
                widget.deleteLater() # Xóa widget một cách an toàn
                
    def populate_calendar(self, tasks_by_day=None):
        """
            Vẽ lại toàn bộ lịch cho tháng hiện tại (lưu trong self.current_date).
            Args:
                tasks_by_day (dict): Dictionary với key là ngày (int) và value là list các task tuple
        """
        self.clear_calendar() # Xóa lịch cũ
        self.setup_week_headers() # Vẽ lại tiêu đề tuần (vì cũng bị xóa ở trên)
        
        month_name = VIETNAMESE_MONTHS[self.current_date.month - 1]
        self.month_label.setText(f"{month_name} {self.current_date.year}")
        calendar.setfirstweekday(calendar.SUNDAY)
        month_calendar = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        

        # Duyệt qua từng tuần và từng ngày để tạo DayWidget
        today = datetime.now()


        for week_num, week_data in enumerate(month_calendar):
            for day_num, day_data in enumerate(week_data):
                if day_data != 0:
                    day_widget = DayWidget(str(day_data), self.current_date.year, self.current_date.month)
                    self.grid_layout.addWidget(day_widget, week_num + 1, day_num)

                    if(self.current_date.year == today.year and
                       self.current_date.month == today.month and
                       day_data == today.day):
                        day_widget.set_today_highlight(True)

                    # Thêm widget ngày vào lưới tại đúng vị trí hàng (tuần) và cột (thứ)
                    self.grid_layout.addWidget(day_widget, week_num + 1, day_num) # +1 vì hàng 0 là tiêu đề
        
        # [THAY ĐỔI] Quyết định hàm lấy dữ liệu nào sẽ được gọi
        tasks = {}
        if self.current_view_mode == 'personal':
            tasks = self._fetch_personal_tasks_for_month()
        else: # Chế độ 'group'
            tasks = self._fetch_group_tasks_for_month()
        
        if tasks:
            self._display_tasks(tasks)

        # Thêm dữ liệu thực từ database hoặc dữ liệu mẫu
        if tasks_by_day:
            self.add_tasks_from_data(tasks_by_day)
        else:
            # Không có dữ liệu, chỉ hiển thị lịch trống
            pass
        

    def add_tasks_from_data(self, tasks_by_day):
        """
            Thêm tasks từ dữ liệu thực tế vào lịch.
            Args:
                tasks_by_day (dict): Dictionary với key là ngày (int) và value là list các task tuple
        """
        # Duyệt qua các ô trong lưới để tìm DayWidget tương ứng và thêm task
        for row in range(1, self.grid_layout.rowCount()):
            for col in range(self.grid_layout.columnCount()):
                item = self.grid_layout.itemAtPosition(row, col)
                if item and isinstance(item.widget(), DayWidget):
                    day_widget = item.widget()
                    day = int(day_widget.date_label.text()) # Lấy số ngày từ label
                    if day in tasks_by_day:
                        for task_data in tasks_by_day[day]:
                            if isinstance(task_data, dict):
                                # Group tasks với thông tin đầy đủ
                                title = task_data['title']
                                is_done = task_data['is_done']
                                note_text = task_data['note']
                                assignee_name = task_data.get('assignee_name', '')
                                # Tạo TaskWidget cho group task với assignee info
                                day_widget.add_task(GroupTaskWidget(title, is_done, assignee_name, note=note_text))
                            else:
                                # Personal tasks (tuple format): (title, is_done, note)
                                title, is_done, note_text = task_data
                                day_widget.add_task(TaskWidget(title, is_done, note=note_text))

    def _fetch_personal_tasks_for_month(self):
        # Đổi tên hàm cũ _fetch_tasks_for_month thành _fetch_personal_tasks_for_month
        # Logic bên trong giữ nguyên
        tasks_by_day = {}
        month_str = self.current_date.strftime('%Y-%m')
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = "SELECT title, is_done, note, due_at FROM tasks WHERE user_id = ? AND strftime('%Y-%m', due_at) = ?"
            cursor.execute(query, (self.user_id, month_str))
            all_tasks = cursor.fetchall()
            
            for task_data in all_tasks:
                title, is_done_int, note, due_at_str = task_data
                if due_at_str:
                    day = datetime.strptime(due_at_str, '%Y-%m-%d %H:%M:%S').day
                    if day not in tasks_by_day: tasks_by_day[day] = []
                    # Thêm None vào vị trí của assignee_name để đồng bộ cấu trúc
                    tasks_by_day[day].append((title, bool(is_done_int), note, None))
            conn.close()
        except Exception as e:
            print(f"Lỗi khi lấy task cá nhân: {e}")
        return tasks_by_day

    # [MỚI] Hàm để lấy task của nhóm
    def _fetch_group_tasks_for_month(self):
        tasks_by_day = {}
        month_str = self.current_date.strftime('%Y-%m')
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 1. Tìm group_id của user
            cursor.execute("SELECT group_id FROM group_members WHERE user_id = ?", (self.user_id,))
            user_group = cursor.fetchone()
            if not user_group:
                print("User không thuộc nhóm nào.")
                conn.close()
                return {}
            group_id = user_group[0]

            # 2. Lấy tất cả task của nhóm đó trong tháng
            query = "SELECT title, is_done, note, due_at, assignee_id FROM group_tasks WHERE group_id = ? AND strftime('%Y-%m', due_at) = ?"
            cursor.execute(query, (group_id, month_str))
            all_tasks = cursor.fetchall()

            for task_data in all_tasks:
                title, is_done_int, note, due_at_str, assignee_id = task_data
                if due_at_str:
                    day = datetime.strptime(due_at_str, '%Y-%m-%d %H:%M:%S').day
                    
                    # 3. Lấy tên của người được giao việc
                    assignee_name = self._get_user_name(cursor, assignee_id)
                    
                    if day not in tasks_by_day: tasks_by_day[day] = []
                    tasks_by_day[day].append((title, bool(is_done_int), note, assignee_name))
            conn.close()
        except Exception as e:
            print(f"Lỗi khi lấy task nhóm: {e}")
        return tasks_by_day
        
    # [MỚI] Hàm tiện ích để lấy tên user từ id, có sử dụng cache
    def _get_user_name(self, cursor, user_id):
        if not user_id: return "Chưa giao"
        if user_id in self.user_names_cache:
            return self.user_names_cache[user_id]
        
        cursor.execute("SELECT user_name FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        if result:
            name = result[0]
            self.user_names_cache[user_id] = name
            return name
        return "Không rõ"

    # [THAY ĐỔI] Sửa lại để xử lý cấu trúc dữ liệu mới (có thêm assignee_name)
    def _display_tasks(self, tasks):
        for row in range(1, self.grid_layout.rowCount()):
            for col in range(self.grid_layout.columnCount()):
                item = self.grid_layout.itemAtPosition(row, col)
                if item and isinstance(item.widget(), DayWidget):
                    day_widget = item.widget()
                    try:
                        day_text = day_widget.date_label.text().strip()
                        if day_text:
                            day_from_widget = int(day_text)
                            if day_from_widget in tasks:
                                for task_data in tasks[day_from_widget]:
                                    title, is_done, note, assignee_name = task_data
                                    day_widget.add_task(TaskWidget(title, is_done, note, assignee_name))
                    except Exception as e:
                        print(f"Lỗi khi hiển thị task: {e}")
                        
    # ... (các hàm còn lại như clear_calendar, setup_week_headers, prev_month, next_month giữ nguyên) ...
    def clear_calendar(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def setup_week_headers(self):
        days = ["Chủ Nhật", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy"]
        for i, day in enumerate(days):
            label = QLabel(day)
            label.setObjectName("WeekDayLabel")
            label.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(label, 0, i)

    def prev_month(self):
        self.current_date = self.current_date.replace(day=1) - timedelta(days=1)
        self.populate_calendar()

    def next_month(self):
        days_in_month = calendar.monthrange(self.current_date.year, self.current_date.month)[1]
        self.current_date = self.current_date.replace(day=days_in_month) + timedelta(days=1)
        self.populate_calendar()