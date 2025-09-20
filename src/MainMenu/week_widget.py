"""
    Chứa WeekWidget chính và logic của nó
"""
import sys
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QApplication, QScrollArea
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
# Giả sử TaskWidget nằm trong thư mục components
from MainMenu.components import TaskWidget 

VIETNAMESE_DAYS = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]

class WeekDayCell(QWidget):
    """Một ô nhỏ hiển thị Thứ và Ngày trong tuần."""
    def __init__(self, day_name, date_num, is_today=False, parent=None):
        super().__init__(parent)
        self.setObjectName("WeekDayCell")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.day_label = QLabel(day_name)
        self.day_label.setAlignment(Qt.AlignCenter)
        self.day_label.setObjectName("WeekDayLabel")

        self.date_label = QLabel(str(date_num))
        self.date_label.setAlignment(Qt.AlignCenter)
        font = self.date_label.font()
        font.setPointSize(16)
        font.setBold(True)
        self.date_label.setFont(font)

        layout.addWidget(self.day_label)
        layout.addWidget(self.date_label)
        
        if is_today:
            self.setStyleSheet("#WeekDayCell { border: 2px solid #0078D7; border-radius: 5px; background-color: #E0EFFF; }")

class WeekWidget(QWidget):
    """
        Widget này chứa giao diện và logic của lịch theo tuần.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_date = datetime.now()
        self.initUI()
        self.populate_week()

    def initUI(self):
        self.main_layout = QVBoxLayout(self)
        
        # --- 1. Thanh điều hướng tuần ---
        nav_layout = QHBoxLayout()
        self.prev_week_btn = QPushButton("< Tuần trước")
        self.prev_week_btn.clicked.connect(self.prev_week)
        
        self.week_label = QLabel()
        self.week_label.setAlignment(Qt.AlignCenter)
        title_font = self.week_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.week_label.setFont(title_font)
        
        self.next_week_btn = QPushButton("Tuần sau >")
        self.next_week_btn.clicked.connect(self.next_week)
        
        nav_layout.addWidget(self.prev_week_btn)
        nav_layout.addWidget(self.week_label, 1)
        nav_layout.addWidget(self.next_week_btn)
        self.main_layout.addLayout(nav_layout)
        
        # --- 2. Lưới hiển thị 7 ngày trong tuần ---
        self.days_layout = QHBoxLayout()
        self.days_layout.setSpacing(10)
        self.main_layout.addLayout(self.days_layout)

        # --- 3. Khu vực hiển thị danh sách công việc ---
        task_area_label = QLabel("Công việc trong tuần")
        task_area_label.setObjectName("TaskAreaLabel")
        font = task_area_label.font()
        font.setPointSize(14)
        task_area_label.setFont(font)
        self.main_layout.addWidget(task_area_label)

        # ScrollArea để chứa danh sách task
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("TaskScrollArea")
        
        scroll_content = QWidget()
        self.task_list_layout = QVBoxLayout(scroll_content)
        self.task_list_layout.setAlignment(Qt.AlignTop)
        
        scroll_area.setWidget(scroll_content)
        self.main_layout.addWidget(scroll_area, 1) # Cho phép co giãn

    def clear_week_view(self):
        """Xóa các widget cũ trước khi vẽ tuần mới."""
        for i in reversed(range(self.days_layout.count())):
            self.days_layout.itemAt(i).widget().deleteLater()
        for i in reversed(range(self.task_list_layout.count())):
            item = self.task_list_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Xóa layout con nếu có
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()


    def populate_week(self):
        """Vẽ lại toàn bộ giao diện cho tuần hiện tại."""
        self.clear_week_view()
        
        today = datetime.now().date()
        # Tính ngày bắt đầu của tuần (Chủ Nhật)
        # weekday() trả về Thứ 2 = 0, ..., Chủ Nhật = 6
        start_of_week = self.current_date.date() - timedelta(days=((self.current_date.weekday() + 1) % 7))
        
        # Cập nhật nhãn điều hướng
        end_of_week = start_of_week + timedelta(days=6)
        self.week_label.setText(f"Tuần từ {start_of_week.strftime('%d/%m')} đến {end_of_week.strftime('%d/%m/%Y')}")

        # Vẽ 7 ô ngày
        for i in range(7):
            current_day = start_of_week + timedelta(days=i)
            day_name = VIETNAMESE_DAYS[current_day.weekday()] # Lấy tên tiếng Việt
            date_num = current_day.day
            is_today = (current_day == today)
            
            day_cell = WeekDayCell(day_name, date_num, is_today)
            self.days_layout.addWidget(day_cell)

        # Tải và hiển thị công việc cho tuần này
        self.load_tasks_for_week(start_of_week, end_of_week)

    def load_tasks_for_week(self, start_date, end_date):
        """Tải và hiển thị các task trong khoảng thời gian của tuần."""
        # --- DỮ LIỆU MẪU ---
        # Trong ứng dụng thực tế, bạn sẽ truy vấn database ở đây
        # Key là ngày trong tháng, value là danh sách các task
        tasks_of_month = {
            18: [("Làm báo cáo tuần", False, "Nộp cho sếp trước 5h chiều")],
            20: [
                ("Họp team", False, "Họp online qua Google Meet"),
                ("Thanh toán tiền điện", True, "Đã thanh toán qua app")
            ],
            21: [("Đi siêu thị", False, "Mua rau và thịt")]
        }
        
        # Duyệt qua các ngày trong tuần
        for i in range(7):
            current_day = start_date + timedelta(days=i)
            day_key = current_day.day
            
            # Kiểm tra xem ngày này có công việc không
            if day_key in tasks_of_month and current_day.month == self.current_date.month:
                # Tạo một tiêu đề cho ngày đó
                day_header_label = QLabel(f"{VIETNAMESE_DAYS[current_day.weekday()]}, {current_day.strftime('%d/%m')}")
                day_header_label.setObjectName("TaskDayHeader")
                self.task_list_layout.addWidget(day_header_label)

                # Thêm các task của ngày đó
                for task_text, is_done, note_text in tasks_of_month[day_key]:
                    task_widget = TaskWidget(task_text, is_done, note=note_text)
                    self.task_list_layout.addWidget(task_widget)

    def prev_week(self):
        """Chuyển sang tuần trước."""
        self.current_date -= timedelta(days=7)
        self.populate_week()

    def next_week(self):
        """Chuyển sang tuần sau."""
        self.current_date += timedelta(days=7)
        self.populate_week()

# --- Đoạn mã để chạy thử widget này độc lập ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Thêm một chút style để dễ nhìn hơn
    app.setStyleSheet("""
        #WeekDayCell { 
            background-color: #f0f0f0; 
            border-radius: 5px;
        }
        #WeekDayLabel {
            color: #666;
        }
        #TaskDayHeader {
            font-size: 14px;
            font-weight: bold;
            margin-top: 10px;
            padding-bottom: 5px;
            border-bottom: 1px solid #ddd;
        }
        #TaskScrollArea {
            border: 1px solid #ccc;
        }
    """)
    
    main_window = WeekWidget()
    main_window.setWindowTitle("Week View Widget")
    main_window.resize(800, 600)
    main_window.show()
    sys.exit(app.exec_())