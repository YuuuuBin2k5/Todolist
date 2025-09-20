"""
    Chứa Widget chính và logic của nó       ---> CalendarWidget
"""

import calendar
from datetime import datetime, timedelta
from datetime import datetime, timedelta
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
    def __init__(self, parent=None):
        super().__init__(parent)
        # Lưu lại ngày tháng năm hiện tại để biết cần hiển thị lịch của tháng nào
        self.current_date = datetime.now()
        # Gọi hàm thiết lập giao diện
        self.initUI()
        # Gọi hàm để điền dữ liệu (các ngày) vào lịch
        self.populate_calendar()

    def initUI(self):
        # Layout chính của widget này, theo chiều dọc
        self.main_layout = QVBoxLayout(self)
        
        # --- Tạo thanh điều hướng tháng (VD: < Tháng Chín 2025 >) ---
        nav_layout = QHBoxLayout()
        self.prev_month_btn = QPushButton("< Trước")
        self.prev_month_btn.clicked.connect(self.prev_month) # Kết nối nút với hàm lùi về tháng trước
        
        self.month_label = QLabel() # Nhãn hiển thị tên tháng và năm
        self.month_label.setAlignment(Qt.AlignCenter)
        
        title_font = QApplication.instance().font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.month_label.setFont(title_font)
        
        self.next_month_btn = QPushButton("Sau >")
        self.next_month_btn.clicked.connect(self.next_month) # Kết nối nút với hàm tiến tới tháng sau
        
        # Thêm các nút và nhãn vào layout điều hướng
        nav_layout.addWidget(self.prev_month_btn)
        nav_layout.addWidget(self.month_label, 1) # Tham số 1 để label co giãn, chiếm không gian thừa
        nav_layout.addWidget(self.next_month_btn)
        self.main_layout.addLayout(nav_layout)
        
        # --- Tạo lưới (grid) để chứa các ngày trong tháng ---
        self.grid_layout = QGridLayout()
        self.main_layout.addLayout(self.grid_layout)
        # Tạo các tiêu đề cho thứ trong tuần (Chủ Nhật, Thứ Hai, ...)
        self.setup_week_headers()

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
        
        # Cập nhật nhãn tháng/năm
        month_name = VIETNAMESE_MONTHS[self.current_date.month - 1]
        self.month_label.setText(f"{month_name} {self.current_date.year}")
        
        # Lấy dữ liệu lịch của tháng từ thư viện calendar
        # Nó trả về một list các tuần, mỗi tuần là một list các ngày (số 0 là ngày trống)
        month_calendar = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        
        # Duyệt qua từng tuần và từng ngày để tạo DayWidget
        today = datetime.now()
        for week_num, week_data in enumerate(month_calendar):
            for day_num, day_data in enumerate(week_data):
                # Chỉ tạo widget cho những ngày khác 0
                if day_data != 0:
                    day_widget = DayWidget(
                        str(day_data), 
                        self.current_date.year, 
                        self.current_date.month
                    )
                    # Nếu là ngày hiện tại, gọi highlight trên DayWidget
                    if(self.current_date.year == today.year and
                       self.current_date.month == today.month and
                       day_data == today.day):
                        day_widget.set_today_highlight(True)
                        

                    # Thêm widget ngày vào lưới tại đúng vị trí hàng (tuần) và cột (thứ)
                    self.grid_layout.addWidget(day_widget, week_num + 1, day_num) # +1 vì hàng 0 là tiêu đề
        
        # Thêm dữ liệu thực từ database hoặc dữ liệu mẫu
        if tasks_by_day:
            self.add_tasks_from_data(tasks_by_day)
        else:
            self.add_sample_data()

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
                        # Unpack cả 3 giá trị từ database: (title, is_done, note)
                        for title, is_done, note_text in tasks_by_day[day]:
                            # Khởi tạo TaskWidget với dữ liệu từ database
                            day_widget.add_task(TaskWidget(title, is_done, note=note_text))

    def add_sample_data(self):
        """
            Thêm một vài task mẫu vào lịch để minh họa.
        """
        # Mỗi tuple giờ có 3 phần tử: (tên, trạng thái, ghi chú)
        # 4, 6, 10  là ngày của task
        tasks = { 
            4: [("Clean New House", False, "")], 
            6: [("Pay Electricity", True, "Thanh toán qua app ngân hàng.")],
            10: [("Team Meeting", False, "Chuẩn bị slide báo cáo tuần.")]
        }
        # Duyệt qua các ô trong lưới để tìm DayWidget tương ứng và thêm task
        for row in range(1, self.grid_layout.rowCount()):
            for col in range(self.grid_layout.columnCount()):
                item = self.grid_layout.itemAtPosition(row, col)
                if item and isinstance(item.widget(), DayWidget):
                    day_widget = item.widget()
                    day = int(day_widget.date_label.text()) # Lấy số ngày từ label
                    if day in tasks:
                        # Unpack cả 3 giá trị
                        for task_text, is_done, note_text in tasks[day]:
                            # Khởi tạo TaskWidget với ghi chú
                            day_widget.add_task(TaskWidget(task_text, is_done, note=note_text))
    
    def prev_month(self):
        """
            Chuyển lịch sang tháng trước đó.
        """
        # Lấy ngày đầu của tháng hiện tại trừ đi một ngày sẽ ra ngày cuối của tháng trước
        self.current_date = self.current_date.replace(day=1) - timedelta(days=1)
        self.populate_calendar() # Vẽ lại lịch

    def next_month(self):
        """
            Chuyển lịch sang tháng kế tiếp.
        """
        # Lấy ngày cuối của tháng hiện tại cộng thêm một ngày sẽ ra ngày đầu của tháng sau
        days_in_month = calendar.monthrange(self.current_date.year, self.current_date.month)[1]
        self.current_date = self.current_date.replace(day=days_in_month) + timedelta(days=1)
        self.populate_calendar() # Vẽ lại lịch