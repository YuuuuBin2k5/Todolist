# --- Nhập các thư viện và module cần thiết ---
import calendar  # Thư viện để làm việc với lịch
import os  # Thư viện để tương tác với hệ điều hành, dùng để lấy đường dẫn file
from datetime import datetime, timedelta  # Thư viện để xử lý ngày và giờ
from typing import Optional

# Nhập các thành phần giao diện từ PyQt5
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGridLayout, QMessageBox
from PyQt5.QtGui import QFontDatabase, QFont
from PyQt5.QtCore import Qt

# Nhập các widget tùy chỉnh và lớp quản lý database
from MainMenu.components import DayWidget, TaskBadge
from Managers.database_manager import Database
from config import CALENDAR_BG_GRADIENT_START, CALENDAR_BG_GRADIENT_END, CALENDAR_MONTH_PILL_START, CALENDAR_MONTH_PILL_END, FONT_PATH

calendar.setfirstweekday(calendar.SUNDAY)

VIETNAMESE_MONTHS = [
    "Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6",
    "Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12"
]

class CalendarWidget(QWidget):
    def __init__(self, user_id, db_manager, parent=None): 
        """
        Hàm khởi tạo cho CalendarWidget.
        
        Args:
            user_id (int): ID của người dùng đang đăng nhập.
            db_manager (Database): Đối tượng quản lý CSDL được truyền từ MainWindow.
            parent (QWidget, optional): Widget cha. Mặc định là None.
        """
        super().__init__(parent)  # Gọi hàm khởi tạo của lớp cha (QWidget)
        self.current_user_id = user_id  # Lưu ID của người dùng hiện tại
        self.db_manager = db_manager  # Sử dụng đối tượng db_manager được truyền vào
        
        self.current_display_date = datetime.now()  # Ngày hiện tại sẽ được hiển thị trên lịch
        
        # Các thuộc tính để quản lý trạng thái của lịch
        self.view_mode = 'personal'  # Chế độ xem mặc định là 'personal'
        self.user_names_cache = {}  # Bộ đệm để lưu tên người dùng, tránh truy vấn CSDL nhiều lần
        self.current_group_id = None  # ID của nhóm đang được xem (nếu ở chế độ 'group')
        self.current_group_leader_id = None  # ID của trưởng nhóm hiện tại

        self.initialize_ui()  # Khởi tạo các thành phần giao diện người dùng
        self.populate_calendar_grid()  # Điền dữ liệu ngày và công việc vào lưới lịch

    def switch_view_mode(self, mode, group_id=None):
        """
        Chuyển đổi chế độ xem giữa lịch cá nhân và lịch nhóm.
        
        Args:
            mode (str): Chế độ mới ('personal' hoặc 'group').
            group_id (int, optional): ID của nhóm nếu chuyển sang chế độ xem nhóm.
        """
        print(f"CalendarWidget: Chuyển sang chế độ {mode} cho nhóm {group_id}")
        self.view_mode = mode  # Cập nhật chế độ xem
        self.set_group_context(group_id)  # Cập nhật thông tin về nhóm (nếu có)
        self.populate_calendar_grid()  # Tải lại toàn bộ lịch với dữ liệu của chế độ mới

    def set_group_context(self, group_id):
        """
        Thiết lập ID nhóm và ID trưởng nhóm để kiểm tra quyền hạn.
        
        Args:
            group_id (int): ID của nhóm đang được xem.
        """
        self.current_group_id = group_id  # Lưu ID của nhóm
        if group_id is not None:
            try:
                # Lấy ID trưởng nhóm từ CSDL và lưu lại
                self.current_group_leader_id = self.db_manager.get_group_leader(group_id)
            except Exception as error:
                print(f"Lỗi khi lấy thông tin trưởng nhóm: {error}")
                self.current_group_leader_id = None
        else:
            self.current_group_leader_id = None # Reset khi không ở trong nhóm nào

    def initialize_ui(self):
        """
        Xây dựng giao diện người dùng ban đầu cho widget lịch.
        """
        # Tải font chữ tùy chỉnh để giao diện đẹp hơn
        try:
            if os.path.exists(FONT_PATH):
                QFontDatabase.addApplicationFont(FONT_PATH)
                app_font = QFont("BeVietnamPro-Regular", 10)
                self.setFont(app_font)
        except Exception as error:
            print(f"Không thể tải font tùy chỉnh: {error}")

        # Layout chính của widget, sắp xếp các thành phần theo chiều dọc
        self.main_layout = QVBoxLayout(self)
        
        # Thiết lập màu nền gradient cho toàn bộ widget
        self.setStyleSheet(f'''
            QWidget {{ 
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:1, 
                    stop:0 {CALENDAR_BG_GRADIENT_START}, 
                    stop:1 {CALENDAR_BG_GRADIENT_END}
                ); 
            }}
        ''')

        # --- Phần Header (Chứa nút điều hướng và tên tháng) ---
        header_layout = QHBoxLayout()  # Layout cho header, sắp xếp theo chiều ngang

        # Nút "Tháng trước"
        self.prev_month_button = QPushButton("◀")
        self.prev_month_button.setFixedSize(36, 36)
        self.prev_month_button.clicked.connect(self.go_to_previous_month)
        
        # Nút "Tháng sau"
        self.next_month_button = QPushButton("▶")
        self.next_month_button.setFixedSize(36, 36)
        self.next_month_button.clicked.connect(self.go_to_next_month)

        # Nhãn hiển thị tên tháng và năm
        self.month_year_label = QLabel()
        self.month_year_label.setAlignment(Qt.AlignCenter)
        font = self.month_year_label.font()
        font.setPointSize(20)
        font.setBold(True)
        self.month_year_label.setFont(font)
        self.month_year_label.setStyleSheet(f"""
            padding: 10px 24px; 
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0, 
                stop:0 {CALENDAR_MONTH_PILL_START}, 
                stop:1 {CALENDAR_MONTH_PILL_END}
            ); 
            border-radius: 18px; 
            color: white;
        """)

        # Sắp xếp các thành phần trong header
        header_layout.addStretch()
        header_layout.addWidget(self.prev_month_button)
        header_layout.addSpacing(8)
        header_layout.addWidget(self.month_year_label)
        header_layout.addSpacing(8)
        header_layout.addWidget(self.next_month_button)
        header_layout.addStretch()
        self.main_layout.addLayout(header_layout)

        # --- Lưới Lịch ---
        self.calendar_grid_layout = QGridLayout()
        self.calendar_grid_layout.setSpacing(14)
        self.main_layout.addLayout(self.calendar_grid_layout)

    def _get_user_name_from_cache(self, user_id: Optional[int]) -> Optional[str]:
        """
        Lấy tên người dùng từ bộ đệm hoặc từ CSDL nếu chưa có.
        
        Hàm này trả về `None` trong hai trường hợp:
        1. Khi `user_id` không được cung cấp (ví dụ: công việc chưa được giao).
        2. Khi `user_id` có nhưng không tìm thấy người dùng tương ứng trong CSDL.
        
        Args:
            user_id (Optional[int]): ID của người dùng cần lấy tên.
                
        Returns:
            Optional[str]: Tên người dùng nếu tìm thấy, ngược lại là None.
        """
        # Trường hợp 1: Công việc chưa được giao cho ai (user_id là None hoặc 0)
        if not user_id:
            return None 
        
        # Kiểm tra xem tên người dùng đã có trong bộ đệm (cache) hay chưa để tránh truy vấn lại
        if user_id in self.user_names_cache:
            return self.user_names_cache[user_id]
        
        # Nếu không có trong cache, thực hiện truy vấn cơ sở dữ liệu
        name = self.db_manager.get_user_name(user_id)
        
        # Nếu tìm thấy tên trong CSDL
        if name:
            self.user_names_cache[user_id] = name  # Lưu vào cache để sử dụng cho những lần sau
            return name
            
        # Trường hợp 2: Không tìm thấy người dùng trong CSDL với user_id đã cho
        return None

    def clear_calendar_grid(self):
        """
        Xóa tất cả các widget (ô ngày, tiêu đề) khỏi lưới lịch.
        """
        while self.calendar_grid_layout.count():
            layout_item = self.calendar_grid_layout.takeAt(0)
            widget_to_remove = layout_item.widget()
            if widget_to_remove is not None:
                widget_to_remove.deleteLater()

    def setup_weekday_headers(self):
        """
        Tạo và thêm các nhãn cho tiêu đề thứ trong tuần (Chủ Nhật, Thứ Hai, ...).
        """
        weekdays = ["Chủ Nhật", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy"]
        for column_index, day_name in enumerate(weekdays):
            header_label = QLabel(day_name)
            header_label.setObjectName("WeekDayLabel")
            header_label.setAlignment(Qt.AlignCenter)
            header_label.setStyleSheet("""
                color: #02457a; 
                font-weight: 700; 
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #bfe9ff, stop:1 #e6f7ff); 
                padding: 8px; 
                border-radius: 6px;
            """)
            self.calendar_grid_layout.addWidget(header_label, 0, column_index)

    def populate_calendar_grid(self):
        """
        Vẽ lại toàn bộ lịch: điền ngày, công việc và cập nhật tiêu đề tháng.
        """
        self.clear_calendar_grid()  # Dọn dẹp lưới lịch cũ
        self.setup_weekday_headers()  # Tạo lại tiêu đề các thứ trong tuần
        
        # Cập nhật nhãn hiển thị tháng/năm hiện tại
        month_name = VIETNAMESE_MONTHS[self.current_display_date.month - 1]
        self.month_year_label.setText(f"{month_name} {self.current_display_date.year}")
        
        # Lấy ma trận các ngày trong tháng từ thư viện calendar
        month_matrix = calendar.monthcalendar(self.current_display_date.year, self.current_display_date.month)
        
        today = datetime.now()

        # Lặp qua ma trận để tạo các DayWidget cho mỗi ngày
        for row_index, week_list in enumerate(month_matrix):
            for column_index, day_number in enumerate(week_list):
                if day_number != 0:  # Chỉ tạo widget cho những ngày có trong tháng
                    day_widget = DayWidget(
                        date_text=str(day_number), 
                        year=self.current_display_date.year, 
                        month=self.current_display_date.month, 
                        calendar_ref=self
                    )
                    
                    # Đánh dấu ngày hôm nay
                    is_today = (self.current_display_date.year == today.year and
                                self.current_display_date.month == today.month and
                                day_number == today.day)
                    if is_today:
                        day_widget.set_today_highlight(True)
                        
                    # Thêm DayWidget vào lưới tại đúng vị trí hàng và cột
                    self.calendar_grid_layout.addWidget(day_widget, row_index + 1, column_index)
        
        # Lấy dữ liệu công việc dựa trên chế độ xem và hiển thị chúng
        if self.view_mode == 'personal':
            tasks = self._fetch_personal_tasks_for_month()
        else:
            tasks = self._fetch_group_tasks_for_month()

        if tasks:
            self._display_tasks_on_grid(tasks)

    def _fetch_personal_tasks_for_month(self):
        """
        Truy vấn CSDL để lấy công việc cá nhân và công việc nhóm được giao cho người dùng trong tháng.
        
        Returns:
            dict: Một dictionary với key là ngày (int) và value là danh sách các công việc.
        """
        tasks_by_day = {}
        month_string = self.current_display_date.strftime('%Y-%m')
        try:
            # Lấy công việc cá nhân
            personal_tasks = self.db_manager.get_tasks_for_user_month(self.current_user_id, month_string)
            for task_tuple in personal_tasks:
                task_id, title, is_done_int, note, due_at_str = task_tuple
                if due_at_str:
                    datetime_obj = datetime.fromisoformat(due_at_str)
                    day = datetime_obj.day
                    if day not in tasks_by_day:
                        tasks_by_day[day] = []
                    tasks_by_day[day].append({
                        'task_id': task_id, 'title': title, 'is_done': bool(is_done_int),
                        'note': note, 'due_at': due_at_str, 'assignee_name': None
                    })

            # Lấy công việc nhóm được giao cho người dùng này
            assigned_group_tasks = self.db_manager.get_group_tasks_for_user_month(self.current_user_id, month_string)
            for group_task_tuple in assigned_group_tasks:
                g_task_id, _, assignee_id, g_title, g_note, g_is_done, g_due_at = group_task_tuple
                if g_due_at:
                    datetime_obj = datetime.fromisoformat(g_due_at)
                    day = datetime_obj.day
                    if day not in tasks_by_day:
                        tasks_by_day[day] = []
                    assignee_name = self._get_user_name_from_cache(assignee_id)
                    tasks_by_day[day].append({
                        'task_id': g_task_id, 'title': g_title, 'is_done': bool(g_is_done),
                        'note': g_note, 'due_at': g_due_at, 'assignee_name': assignee_name
                    })
        except Exception as error:
            print(f"Lỗi khi lấy công việc cá nhân: {error}")
        return tasks_by_day

    def _fetch_group_tasks_for_month(self):
        """
        Truy vấn CSDL để lấy tất cả công việc của nhóm hiện tại trong tháng.
        
        Returns:
            dict: Một dictionary với key là ngày (int) và value là danh sách các công việc.
        """
        tasks_by_day = {}
        if not self.current_group_id:
            return tasks_by_day # Không có nhóm nào được chọn

        month_string = self.current_display_date.strftime('%Y-%m')
        try:
            all_group_tasks = self.db_manager.get_group_tasks_for_month(self.current_group_id, month_string)
            for task_tuple in all_group_tasks:
                task_id, _, assignee_id, title, note, is_done_int, due_at_str = task_tuple
                if due_at_str:
                    datetime_obj = datetime.fromisoformat(due_at_str)
                    day = datetime_obj.day
                    if day not in tasks_by_day:
                        tasks_by_day[day] = []
                    
                    assignee_name = self._get_user_name_from_cache(assignee_id)
                    tasks_by_day[day].append({
                        'task_id': task_id, 'title': title, 'is_done': bool(is_done_int),
                        'note': note, 'due_at': due_at_str, 'assignee_name': assignee_name
                    })
        except Exception as error:
            print(f"Lỗi khi lấy công việc nhóm: {error}")
        return tasks_by_day

    def _display_tasks_on_grid(self, tasks_by_day):
        """
        Hiển thị các công việc lên các ô ngày tương ứng trên lưới lịch.
        
        Args:
            tasks_by_day (dict): Dictionary chứa các công việc đã được nhóm theo ngày.
        """
        # Lặp qua tất cả các widget trong lưới
        for row in range(1, self.calendar_grid_layout.rowCount()):
            for col in range(self.calendar_grid_layout.columnCount()):
                layout_item = self.calendar_grid_layout.itemAtPosition(row, col)
                if layout_item and isinstance(layout_item.widget(), DayWidget):
                    day_widget = layout_item.widget()
                    day_number = int(day_widget.date_label.text())
                    
                    # Nếu có công việc cho ngày này, thêm chúng vào DayWidget
                    if day_number in tasks_by_day:
                        day_widget.clear_tasks()  # Xóa các công việc cũ trước khi thêm mới
                        for task_details in tasks_by_day[day_number]:
                            is_group_task = task_details.get('assignee_name') is not None
                            
                            badge = TaskBadge(
                                title=task_details['title'],
                                color='#5c6bc0' if is_group_task else '#66bb6a',
                                note=task_details.get('note', ''),
                                assignee_name=task_details.get('assignee_name', ''),
                                task_id=task_details.get('task_id'),
                                is_group=is_group_task,
                                calendar_ref=self
                            )
                            
                            is_done = task_details.get('is_done', False)
                            badge.checkbox.setChecked(is_done)
                            
                            day_widget.add_task(badge)

    def go_to_previous_month(self):
        """
        Chuyển lịch sang tháng trước đó và tải lại dữ liệu.
        """
        self.current_display_date = self.current_display_date.replace(day=1) - timedelta(days=1)
        self.populate_calendar_grid()

    def go_to_next_month(self):
        """
        Chuyển lịch sang tháng kế tiếp và tải lại dữ liệu.
        """
        days_in_month = calendar.monthrange(self.current_display_date.year, self.current_display_date.month)[1]
        self.current_display_date = self.current_display_date.replace(day=days_in_month) + timedelta(days=1)
        self.populate_calendar_grid()
        
    def add_task_to_db(self, date_obj, task_title, note_text=""):
        """
        Thêm một công việc cá nhân mới vào cơ sở dữ liệu.
        
        Args:
            date_obj (datetime): Ngày hết hạn của công việc.
            task_title (str): Tiêu đề công việc.
            note_text (str): Ghi chú cho công việc.
        """
        try:
            due_date_str = date_obj.strftime('%Y-%m-%d %H:%M:%S')
            self.db_manager.add_task(self.current_user_id, task_title, note_text, 0, due_date_str)
            self.populate_calendar_grid()  # Tải lại lịch để hiển thị công việc mới
            print(f"Đã thêm công việc cá nhân: '{task_title}'")
        except Exception as error:
            print(f"Lỗi khi thêm công việc cá nhân: {error}")

    def add_group_task_to_db(self, date_obj, task_title, assignee_id=None, note_text=""):
        """
        Thêm một công việc nhóm mới vào cơ sở dữ liệu.
        
        Args:
            date_obj (datetime): Ngày hết hạn của công việc.
            task_title (str): Tiêu đề công việc.
            assignee_id (int, optional): ID người được giao.
            note_text (str): Ghi chú cho công việc.
        """
        if not self.current_group_id:
            QMessageBox.warning(self, "Lỗi", "Không có nhóm nào được chọn để thêm công việc.")
            return
            
        try:
            due_date_str = date_obj.strftime('%Y-%m-%d %H:%M:%S')
            self.db_manager.add_group_task(
                group_id=self.current_group_id,
                creator_id=self.current_user_id,
                title=task_title,
                note=note_text,
                due_at=due_date_str,
                assignee_id=assignee_id
            )
            self.populate_calendar_grid()
            print(f"Đã thêm công việc nhóm: '{task_title}'")
        except Exception as error:
            print(f"Lỗi khi thêm công việc nhóm: {error}")

    def delete_task(self, task_id, is_group):
        """
        Xóa một công việc (cá nhân hoặc nhóm) khỏi cơ sở dữ liệu.
        
        Args:
            task_id (int): ID của công việc cần xóa.
            is_group (bool): True nếu là công việc nhóm, False nếu là công việc cá nhân.
        """
        try:
            if is_group:
                self.db_manager.delete_group_task(task_id)
            else:
                self.db_manager.delete_task(task_id)
            self.populate_calendar_grid()
            print(f"Đã xóa công việc ID={task_id}, Nhóm={is_group}")
        except Exception as error:
            print(f"Lỗi khi xóa công việc: {error}")
            
    def update_task_status(self, task_id, is_done, is_group):
        """
        Cập nhật trạng thái hoàn thành của một công việc.
        
        Args:
            task_id (int): ID của công việc.
            is_done (int): Trạng thái mới (1 là hoàn thành, 0 là chưa).
            is_group (bool): True nếu là công việc nhóm.
        """
        try:
            if is_group:
                self.db_manager.update_group_task_status(task_id, is_done)
            else:
                self.db_manager.update_task_status(task_id, is_done)
            print(f"Đã cập nhật trạng thái cho công việc ID={task_id}")
            return True
        except Exception as error:
            print(f"Lỗi khi cập nhật trạng thái: {error}")
            return False

    def can_toggle_task(self, task_id, is_group):
        """
        Kiểm tra xem người dùng hiện tại có quyền thay đổi trạng thái của công việc không.
        
        Args:
            task_id (int): ID của công việc.
            is_group (bool): True nếu là công việc nhóm.
            
        Returns:
            tuple: (bool, str) -> (có được phép hay không, thông báo lỗi).
        """
        try:
            if is_group:
                task_details = self.db_manager.get_group_task_by_id(task_id)
                if not task_details:
                    return False, "Không tìm thấy công việc nhóm."
                
                assignee_id = task_details[2] # Cột assignee_id
                
                # Trưởng nhóm có thể thay đổi mọi công việc.
                # Thành viên chỉ có thể thay đổi công việc được giao cho chính họ.
                if self.current_user_id == self.current_group_leader_id or self.current_user_id == assignee_id:
                    return True, ""
                else:
                    return False, "Bạn không có quyền thay đổi công việc của người khác."
            else:
                # Công việc cá nhân thì chỉ chủ sở hữu mới được thay đổi.
                task_details = self.db_manager.get_task_by_id(task_id)
                if not task_details:
                    return False, "Không tìm thấy công việc."
                    
                owner_id = task_details[1] # Cột user_id
                if owner_id == self.current_user_id:
                    return True, ""
                else:
                    return False, "Đây là công việc cá nhân của người khác."
        except Exception as error:
            print(f"Lỗi khi kiểm tra quyền: {error}")
            return False, "Lỗi hệ thống khi kiểm tra quyền."