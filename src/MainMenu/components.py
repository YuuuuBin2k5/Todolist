# --- Nhập các thư viện và module cần thiết ---
import locale  # Dùng để thiết lập ngôn ngữ hiển thị (vd: Thứ trong tuần)
from datetime import datetime  # Để làm việc với đối tượng ngày giờ

# Nhập các lớp widget và công cụ từ PyQt5
from PyQt5.QtWidgets import (QDialog, QFrame, QHBoxLayout, QCheckBox, QLabel, QVBoxLayout,
                             QApplication, QMenu, QInputDialog, QStyle, QPushButton,
                             QScrollArea, QWidget, QLineEdit, QDateTimeEdit, QTextEdit, QDialogButtonBox, QMessageBox,
                             QGraphicsDropShadowEffect, QGraphicsOpacityEffect)
from PyQt5.QtCore import Qt, QMimeData, QDate, QDateTime, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QDrag, QCursor, QFont, QColor, QFontMetrics

# Nhập các biến cấu hình màu sắc và đường dẫn
from config import COLOR_WHITE, COLOR_BORDER, TEXT_MUTED, COLOR_PRIMARY, COLOR_TEXT_PRIMARY

# --- Cấu hình Ngôn ngữ ---
try:
    # Cố gắng thiết lập ngôn ngữ sang Tiếng Việt để hiển thị đúng định dạng
    locale.setlocale(locale.LC_TIME, 'vi_VN.UTF-8')
except locale.Error:
    # Bỏ qua nếu hệ thống không hỗ trợ locale này
    print("Locale 'vi_VN.UTF-8' không được hỗ trợ, sẽ sử dụng locale mặc định.")

# --- Các Hằng số ---
VIETNAMESE_DAYS = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
VIETNAMESE_MONTHS = [
    "Tháng Một", "Tháng Hai", "Tháng Ba", "Tháng Tư", "Tháng Năm", "Tháng Sáu",
    "Tháng Bảy", "Tháng Tám", "Tháng Chín", "Tháng Mười", "Tháng Mười Một", "Tháng Mười Hai"
]

# ==============================================================================
# LỚP 1: TaskDetailItemWidget - Widget hiển thị chi tiết một công việc
# ==============================================================================
class TaskDetailItemWidget(QFrame):
    """
    Một widget con, dùng để hiển thị thông tin chi tiết của một công việc
    trong cửa sổ DayDetailDialog.
    """
    def __init__(self, task_details: dict, calendar_ref=None, parent=None):
        """
        Khởi tạo widget.
        
        Args:
            task_details (dict): Dictionary chứa thông tin chi tiết của công việc.
            calendar_ref (CalendarWidget): Tham chiếu đến lịch để thực hiện các hành động (như xóa).
            parent (QWidget): Widget cha.
        """
        super().__init__(parent)  # Gọi hàm khởi tạo của lớp QFrame
        self.setObjectName("TaskDetailItem")  # Đặt tên object để áp dụng CSS
        self.setFrameShape(QFrame.StyledPanel)  # Đặt kiểu khung viền
        self.calendar_ref = calendar_ref  # Lưu tham chiếu đến lịch

        # Trích xuất và chuẩn hóa dữ liệu từ dictionary
        title = task_details.get('title', 'Không có tiêu đề')
        is_done = task_details.get('is_done', False)
        note_text = task_details.get('note', '')
        assignee_name = task_details.get('assignee_name')
        due_at_str = task_details.get('due_at')
        task_id = task_details.get('task_id')
        is_group_task = task_details.get('is_group', False)

        # Áp dụng CSS cho widget
        self.setStyleSheet(f"""
            QFrame#TaskDetailItem {{ 
                background: {COLOR_WHITE}; 
                border: 1px solid {COLOR_BORDER}; 
                border-radius: 10px; 
                padding: 10px; 
            }}
            QLabel#StatusSmall {{ font-size: 12px; color: {TEXT_MUTED}; }}
            QLabel#NoteLabelInDialog {{ color: {COLOR_TEXT_PRIMARY}; }}
        """)

        # Layout chính, sắp xếp theo chiều ngang
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Layout chứa nội dung bên trái (tiêu đề, ghi chú, thông tin)
        content_layout = QVBoxLayout()
        content_layout.setSpacing(6)

        # Nhãn tiêu đề công việc
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 11, QFont.Bold))
        title_label.setWordWrap(True)  # Tự động xuống dòng nếu tiêu đề quá dài
        content_layout.addWidget(title_label)

        # Hàng chứa thông tin phụ (trạng thái, người thực hiện, hạn chót)
        info_row_layout = QHBoxLayout()
        status_label = QLabel("Đã hoàn thành" if is_done else "Chưa hoàn thành")
        status_label.setObjectName('StatusSmall')
        info_row_layout.addWidget(status_label)

        if assignee_name:
            assignee_label = QLabel(f"👤 {assignee_name}")
            assignee_label.setStyleSheet(f'color: {COLOR_PRIMARY}; margin-left:8px;')
            info_row_layout.addWidget(assignee_label)

        if due_at_str:
            due_label = QLabel(f"⏰ {due_at_str}")
            due_label.setStyleSheet(f'color: {TEXT_MUTED}; margin-left:8px;')
            info_row_layout.addWidget(due_label)
        
        info_row_layout.addStretch()  # Đẩy các mục về bên trái
        content_layout.addLayout(info_row_layout)

        # Nhãn hiển thị ghi chú nếu có
        if note_text:
            note_label = QLabel(f"<b>Ghi chú:</b> {note_text}")
            note_label.setWordWrap(True)
            note_label.setObjectName("NoteLabelInDialog")
            content_layout.addWidget(note_label)

        # Hàng chứa các nút hành động (ví dụ: nút Xóa)
        actions_row_layout = QHBoxLayout()
        actions_row_layout.addStretch()  # Đẩy nút xóa về bên phải
        delete_button = QPushButton("Xóa")
        
        # Hàm nội bộ để xử lý sự kiện nhấn nút xóa
        def perform_delete():
            try:
                if self.calendar_ref and task_id is not None:
                    # Gọi hàm xóa từ CalendarWidget
                    self.calendar_ref.delete_task(task_id, is_group=is_group_task)
            except Exception as error:
                print(f"Lỗi khi thực hiện xóa: {error}")
        
        delete_button.clicked.connect(perform_delete)  # Kết nối sự kiện click
        actions_row_layout.addWidget(delete_button)
        content_layout.addLayout(actions_row_layout)

        main_layout.addLayout(content_layout)

# ==============================================================================
# LỚP 2: DayDetailDialog - Cửa sổ hiển thị danh sách công việc trong ngày
# ==============================================================================
class DayDetailDialog(QDialog):
    """
    Cửa sổ (dialog) bật lên để hiển thị chi tiết tất cả công việc của một ngày cụ thể.
    """
    def __init__(self, selected_date: datetime, tasks_list: list, calendar_ref=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chi Tiết Công Việc Trong Ngày")
        self.setMinimumSize(520, 460)
        self.setObjectName("DayDetailDialog")
        self.calendar_ref = calendar_ref

        main_layout = QVBoxLayout(self)

        # Định dạng chuỗi ngày tháng năm theo Tiếng Việt
        day_name = VIETNAMESE_DAYS[selected_date.weekday()]
        month_name = VIETNAMESE_MONTHS[selected_date.month - 1]
        date_string = f"{day_name}, ngày {selected_date.day} {month_name} năm {selected_date.year}"

        # Nhãn hiển thị ngày tháng
        date_label = QLabel(date_string)
        date_label.setObjectName("DateHeaderLabel")
        date_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(date_label)

        # Tạo khu vực có thể cuộn để chứa danh sách công việc
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content_widget = QWidget()
        tasks_layout = QVBoxLayout(scroll_content_widget)
        tasks_layout.setAlignment(Qt.AlignTop) # Các công việc sẽ xếp từ trên xuống
        scroll_area.setWidget(scroll_content_widget)
        main_layout.addWidget(scroll_area)

        # Lặp qua danh sách công việc và tạo widget cho từng cái
        if tasks_list:
            for task_details in tasks_list:
                detail_item_widget = TaskDetailItemWidget(task_details, calendar_ref=self.calendar_ref)
                tasks_layout.addWidget(detail_item_widget)
        else:
            # Hiển thị thông báo nếu không có công việc nào
            tasks_layout.addWidget(QLabel("Không có công việc nào trong ngày này."))

        # Nút đóng cửa sổ
        close_button = QPushButton("Đóng")
        close_button.clicked.connect(self.accept) # self.accept() là cách chuẩn để đóng QDialog
        main_layout.addWidget(close_button, 0, Qt.AlignRight)

# ==============================================================================
# LỚP 3: ElidedLabel - Nhãn có thể tự cắt ngắn văn bản dài
# ==============================================================================
class ElidedLabel(QLabel):
    """
    Một QLabel tùy chỉnh có khả năng tự động cắt ngắn văn bản dài và thêm "..."
    khi không đủ không gian hiển thị.
    """
    def __init__(self, text='', parent=None):
        super().__init__(parent)
        self._full_text = str(text or '') # Lưu trữ văn bản gốc, đầy đủ
        self.setText(self._full_text)

    def setText(self, text):
        """Ghi đè phương thức setText để lưu văn bản gốc trước khi hiển thị."""
        self._full_text = str(text or '')
        super().setText(self._full_text)
        self._update_elided_text() # Cập nhật lại văn bản hiển thị

    def resizeEvent(self, event):
        """Sự kiện được gọi mỗi khi kích thước của label thay đổi."""
        super().resizeEvent(event)
        self._update_elided_text() # Cập nhật lại văn bản cho vừa với kích thước mới

    def _update_elided_text(self):
        """Cắt ngắn văn bản nếu cần và hiển thị."""
        try:
            font_metrics = QFontMetrics(self.font()) # Công cụ đo kích thước văn bản
            # Tính toán chiều rộng có sẵn (trừ đi một chút padding)
            available_width = max(8, self.width() - 24)
            # Cắt ngắn văn bản bằng công cụ của Qt
            elided_text = font_metrics.elidedText(self._full_text, Qt.ElideRight, available_width)
            super().setText(elided_text) # Hiển thị văn bản đã cắt ngắn
            
            # Luôn hiển thị văn bản đầy đủ khi người dùng di chuột vào (tooltip)
            if self._full_text:
                self.setToolTip(self._full_text)
        except Exception as error:
            print(f"Lỗi khi cắt ngắn văn bản: {error}")

# ==============================================================================
# LỚP 4: TaskBadge - Widget hiển thị công việc dạng "huy hiệu" nhỏ gọn
# ==============================================================================
class TaskBadge(QFrame):
    """
    Widget nhỏ gọn để hiển thị một công việc trên ô lịch.
    Bao gồm tiêu đề (tự cắt ngắn), checkbox và các hiệu ứng tương tác.
    """
    def __init__(self, title, color='#66bb6a', note='', assignee_name=None, 
                 task_id=None, is_group=False, calendar_ref=None, parent=None):
        super().__init__(parent)
        self.setObjectName('TaskBadge')
        
        # Lưu trữ các thông tin quan trọng của công việc
        self.task_id = task_id
        self.is_group_task = is_group
        self.calendar_ref = calendar_ref
        self.note_text = note
        self.assignee_name = assignee_name
        self.task_title = title or ''

        # Cấu hình giao diện cơ bản
        self.setFixedHeight(36)
        self.setMaximumWidth(340)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 6, 2)
        layout.setSpacing(8)

        # Biểu tượng bên trái (để phân biệt công việc nhóm)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(20, 20)
        layout.addWidget(self.icon_label, 0, Qt.AlignVCenter)
        if self.is_group_task:
            self.icon_label.setText('👥') # Emoji nhóm
            self.icon_label.setStyleSheet('font-size:11px; color: white; background: rgba(0,0,0,0.12); border-radius:8px;')
        else:
            self.icon_label.setStyleSheet('background: transparent;') # Ẩn đi nếu là việc cá nhân

        # Nhãn tiêu đề (sử dụng ElidedLabel để tự cắt ngắn)
        self.title_label = ElidedLabel(self.task_title)
        self.title_label.setStyleSheet('color: white; font-size: 13px; font-weight:600;')
        layout.addWidget(self.title_label, 1) # Chiếm phần lớn không gian

        # Checkbox (dùng QPushButton có thể check) để tương tác
        self.checkbox = QPushButton('')
        self.checkbox.setCheckable(True)
        self.checkbox.setFixedSize(24, 24)
        self.checkbox.setStyleSheet("""
            QPushButton { background: rgba(255,255,255,0.12); border-radius: 6px; border: none; color: white; font-weight: bold; }
            QPushButton:checked { background: white; color: #2b2b2b; }
        """)
        layout.addWidget(self.checkbox, 0, Qt.AlignRight)

        # Áp dụng màu nền và hiệu ứng đổ bóng
        self.setStyleSheet(f'background: {color}; border-radius: 12px; padding: 4px;')
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

        # Kết nối sự kiện `toggled` của checkbox với hàm xử lý
        self.checkbox.toggled.connect(self._on_checkbox_changed)

    def text(self):
        """Hàm trợ giúp để lấy tiêu đề của badge."""
        return self.task_title

    def mouseDoubleClickEvent(self, event):
        """Mở cửa sổ chi tiết khi người dùng double-click vào badge."""
        if event.button() == Qt.LeftButton and self.calendar_ref:
            try:
                dialog = QDialog(self)
                dialog.setWindowTitle('Chi tiết công việc')
                dialog.setMinimumWidth(420)
                
                # Tạo dữ liệu để truyền vào TaskDetailItemWidget
                task_details = {
                    'title': self.task_title, 'is_done': self.checkbox.isChecked(),
                    'note': self.note_text, 'assignee_name': self.assignee_name,
                    'task_id': self.task_id, 'is_group': self.is_group_task
                }
                
                content_widget = TaskDetailItemWidget(task_details, calendar_ref=self.calendar_ref)
                layout = QVBoxLayout(dialog)
                layout.addWidget(content_widget)
                
                button_box = QDialogButtonBox(QDialogButtonBox.Close)
                button_box.rejected.connect(dialog.reject)
                layout.addWidget(button_box)
                
                dialog.exec_()
            except Exception as error:
                print(f"Lỗi khi mở dialog chi tiết: {error}")

    def contextMenuEvent(self, event):
        """Hiển thị menu ngữ cảnh (chuột phải) để xóa công việc."""
        context_menu = QMenu(self)
        delete_action = context_menu.addAction('Xóa công việc này')
        action = context_menu.exec_(self.mapToGlobal(event.pos()))
        if action == delete_action:
            if self.task_id and self.calendar_ref:
                self.calendar_ref.delete_task(self.task_id, self.is_group_task)

    def _on_checkbox_changed(self, is_checked):
        """
        Hàm được gọi khi trạng thái của checkbox thay đổi.
        Xử lý việc cập nhật trạng thái công việc trong CSDL.
        """
        # Chuyển đổi trạng thái (bool) sang số nguyên (0 hoặc 1)
        new_status = 1 if is_checked else 0

        # 1. Kiểm tra quyền hạn trước khi thực hiện
        allowed, message = self.calendar_ref.can_toggle_task(self.task_id, self.is_group_task)
        if not allowed:
            QMessageBox.warning(self, 'Không có quyền', message)
            # Hoàn tác lại trạng thái checkbox trên giao diện
            self.checkbox.blockSignals(True)
            self.checkbox.setChecked(not is_checked)
            self.checkbox.blockSignals(False)
            return

        # 2. Cập nhật giao diện một cách "lạc quan" (thay đổi ngay lập tức)
        self.checkbox.setText('✓' if is_checked else '')
        if is_checked:
            self.setStyleSheet('background: #bdbdbd; border-radius: 12px; padding: 4px;')
            self.title_label.setStyleSheet('color: #fff; text-decoration: line-through; font-size:11px;')
        else:
            # Lấy lại màu gốc tùy theo là việc nhóm hay cá nhân
            original_color = '#5c6bc0' if self.is_group_task else '#66bb6a'
            self.setStyleSheet(f'background: {original_color}; border-radius: 12px; padding: 4px;')
            self.title_label.setStyleSheet('color: #fff; font-size:11px;')

        # 3. Gọi CSDL để lưu thay đổi
        success = self.calendar_ref.update_task_status(self.task_id, new_status, self.is_group_task)
        
        # 4. Nếu lưu thất bại, hoàn tác lại giao diện
        if not success:
            QMessageBox.warning(self, 'Lỗi', 'Không thể cập nhật trạng thái công việc.')
            self.checkbox.blockSignals(True)
            self.checkbox.setChecked(not is_checked) # Đảo ngược lại
            self.checkbox.blockSignals(False)
            # Bạn có thể thêm code để hoàn tác cả style ở đây nếu cần

# ==============================================================================
# LỚP 5: AddTaskDialog - Cửa sổ thêm công việc mới
# ==============================================================================
class AddTaskDialog(QDialog):
    """Cửa sổ bật lên cho phép người dùng nhập thông tin để tạo công việc mới."""
    def __init__(self, default_date: datetime, parent=None):
        super().__init__(parent)
        self.setWindowTitle("✨ Thêm công việc mới")
        self.setMinimumWidth(420)

        main_layout = QVBoxLayout(self)

        # Các trường nhập liệu
        self.title_input = QLineEdit(placeholderText="Nhập tiêu đề công việc...")
        self.date_edit = QDateTimeEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat('yyyy-MM-dd HH:mm:ss')
        # Đặt ngày giờ mặc định là ngày người dùng đã click vào
        self.date_edit.setDateTime(QDateTime(default_date))
        
        self.note_edit = QTextEdit(placeholderText="Một vài ghi chú ngắn...")
        self.note_edit.setFixedHeight(90)

        main_layout.addWidget(QLabel("Tiêu đề"))
        main_layout.addWidget(self.title_input)
        main_layout.addWidget(QLabel("Ngày giờ hoàn thành"))
        main_layout.addWidget(self.date_edit)
        main_layout.addWidget(QLabel("Ghi chú (tùy chọn)"))
        main_layout.addWidget(self.note_edit)

        # Các nút "Thêm" và "Hủy"
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Thêm")
        button_box.button(QDialogButtonBox.Cancel).setText("Hủy")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    # Các hàm để lấy dữ liệu từ form sau khi người dùng nhấn "Thêm"
    def get_title(self) -> str:
        return self.title_input.text().strip()

    def get_due_datetime(self) -> QDateTime:
        return self.date_edit.dateTime()

    def get_note(self) -> str:
        return self.note_edit.toPlainText().strip()


# ==============================================================================
# LỚP 6: DayWidget - Widget đại diện cho một ô ngày trong lịch
# ==============================================================================
class DayWidget(QFrame):
    """
    Widget đại diện cho một ô ngày trong lưới lịch.
    Chứa nhãn ngày và một layout để thêm các TaskBadge.
    """
    def __init__(self, date_text, year, month, calendar_ref=None, parent=None):
        super().__init__(parent)
        self.setObjectName("DayWidget")
        self.setFrameShape(QFrame.StyledPanel)
        self.setAcceptDrops(True) # Cho phép kéo-thả công việc vào ô này

        # Lưu thông tin ngày, tháng, năm
        self.day_number = int(date_text)
        self.year = year
        self.month = month
        self.calendar_ref = calendar_ref

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)

        # Nhãn hiển thị số ngày
        self.date_label = QLabel(date_text)
        self.date_label.setObjectName("DateLabel")
        self.date_label.setAlignment(Qt.AlignRight)
        main_layout.addWidget(self.date_label)

        # Layout để chứa các TaskBadge
        self.tasks_layout = QVBoxLayout()
        main_layout.addLayout(self.tasks_layout)

    def set_today_highlight(self, is_today):
        """Đánh dấu ô nếu là ngày hôm nay."""
        if is_today:
            self.setStyleSheet("background-color: rgba(255, 0, 0, 60); border-radius: 6px; padding: 4px;")
        else:
            self.setStyleSheet("") # Xóa highlight

    def _prompt_for_new_task(self):
        """Mở dialog để người dùng nhập thông tin công việc mới."""
        default_date = datetime(self.year, self.month, self.day_number)
        dialog = AddTaskDialog(default_date, self)
        
        # Nếu người dùng nhấn "Thêm" và có nhập tiêu đề
        if dialog.exec_() == QDialog.Accepted and dialog.get_title():
            title = dialog.get_title()
            due_qdatetime = dialog.get_due_datetime()
            # Chuyển đổi từ QDateTime của Qt sang datetime của Python
            due_datetime_obj = due_qdatetime.toPyDateTime()
            note = dialog.get_note()

            if self.calendar_ref:
                # Dựa vào chế độ xem hiện tại để quyết định thêm việc cá nhân hay nhóm
                if self.calendar_ref.view_mode == 'group':
                    self.calendar_ref.add_group_task_to_db(due_datetime_obj, title, note_text=note)
                else:
                    self.calendar_ref.add_task_to_db(due_datetime_obj, title, note_text=note)
    
    def mouseDoubleClickEvent(self, event):
        """Mở cửa sổ chi tiết ngày khi double-click vào vùng trống của ô ngày."""
        # Chỉ mở dialog nếu không double-click vào một công việc đã có
        child_widget = self.childAt(event.pos())
        if not isinstance(child_widget, TaskBadge):
            self.calendar_ref.open_day_detail(self.day_number)
        
    def add_task(self, task_badge: TaskBadge):
        """
        Thêm một TaskBadge vào ô ngày.
        Giới hạn số lượng badge hiển thị để tránh vỡ layout.
        """
        # Đếm số lượng badge đã có
        existing_badges = [self.tasks_layout.itemAt(i).widget() 
                           for i in range(self.tasks_layout.count()) 
                           if isinstance(self.tasks_layout.itemAt(i).widget(), TaskBadge)]
        
        # Nếu chưa đủ 3 badge, thêm badge mới vào
        if len(existing_badges) < 3:
            self.tasks_layout.addWidget(task_badge)
        else:
            # Nếu đã đủ, tìm hoặc tạo nhãn "+1", "+2", ...
            overflow_label = self.findChild(QLabel, "OverflowLabel")
            if not overflow_label:
                overflow_label = QLabel()
                overflow_label.setObjectName("OverflowLabel")
                overflow_label.setStyleSheet('background:#ddd; color:#333; padding:4px 8px; border-radius:10px;')
                self.tasks_layout.addWidget(overflow_label)
            
            # Cập nhật số lượng công việc bị ẩn
            current_overflow_count = int(overflow_label.text().replace("+", "")) if overflow_label.text() else 0
            overflow_label.setText(f"+{current_overflow_count + 1}")

    def clear_tasks(self):
        """Xóa tất cả các widget công việc khỏi ô ngày này."""
        while self.tasks_layout.count():
            item_to_remove = self.tasks_layout.takeAt(0)
            widget = item_to_remove.widget()
            if widget is not None:
                widget.deleteLater() # Xóa widget một cách an toàn

    def contextMenuEvent(self, event):
        """Hiển thị menu chuột phải để thêm công việc mới."""
        context_menu = QMenu(self)
        add_task_action = context_menu.addAction("Thêm công việc mới vào ngày này")
        action = context_menu.exec_(self.mapToGlobal(event.pos()))
        if action == add_task_action:
            self._prompt_for_new_task() # Gọi hàm mở dialog