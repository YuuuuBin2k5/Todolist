"""
    Chứa các widget hỗ trợ cho Calendar bao gồm: 
    - Widget cho một công việc + logic (kéo thả)    ---> TaskWidget
    - Widget cho một ngày + logic (nhận TaskWidget) ---> DayWidget
"""

import locale
from datetime import datetime
from PyQt5.QtWidgets import (QDialog, QFrame, QHBoxLayout, QCheckBox, QLabel, QVBoxLayout, 
                             QApplication, QMenu, QInputDialog, QStyle, QPushButton, 
                             QScrollArea, QWidget)
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDrag, QCursor, QFont

# Thiết lập ngôn ngữ Tiếng Việt để hiển thị đúng Thứ trong tuần
try:
    locale.setlocale(locale.LC_TIME, 'vi_VN.UTF-8')
except locale.Error:
    print("Locale vi_VN not supported, skipping.")

VIETNAMESE_DAYS = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
VIETNAMESE_MONTHS = [
    "Tháng Một", "Tháng Hai", "Tháng Ba", "Tháng Tư", "Tháng Năm", "Tháng Sáu",
    "Tháng Bảy", "Tháng Tám", "Tháng Chín", "Tháng Mười", "Tháng Mười Một", "Tháng Mười Hai"
]

# [MỚI] Widget để hiển thị một công việc trong cửa sổ chi tiết
class TaskDetailItemWidget(QFrame):
    def __init__(self, task_text, is_done, note_text, parent=None):
        super().__init__(parent)
        self.setObjectName("TaskDetailItem")
        self.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(self)

        # Tên công việc
        name_label = QLabel(task_text)
        name_label.setFont(QFont("Arial", 11, QFont.Bold))
        name_label.setWordWrap(True)
        layout.addWidget(name_label)

        # Trạng thái
        status_text = "✅ Đã hoàn thành" if is_done else "❌ Chưa hoàn thành"
        status_label = QLabel(f"<b>Trạng thái:</b> {status_text}")
        layout.addWidget(status_label)

        # Ghi chú (chỉ hiển thị nếu có)
        if note_text:
            note_label = QLabel(f"<b>Ghi chú:</b> {note_text}")
            note_label.setWordWrap(True) # Tự động xuống dòng nếu ghi chú dài
            note_label.setObjectName("NoteLabelInDialog")
            layout.addWidget(note_label)

# [MỚI] Cửa sổ chi tiết công việc của một ngày
class DayDetailDialog(QDialog):
    def __init__(self, full_date, tasks_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chi Tiết Công Việc Trong Ngày")
        self.setMinimumSize(450, 400)
        self.setObjectName("DayDetailDialog")
        
        main_layout = QVBoxLayout(self)

        # Hiển thị ngày tháng năm đầy đủ
        # Ví dụ: "Thứ Bảy, ngày 20 tháng 09 năm 2025"
        day_name = VIETNAMESE_DAYS[full_date.weekday()]
        month_name = VIETNAMESE_MONTHS[full_date.month - 1]
        date_str = f"{day_name}, ngày {full_date.day} {month_name} năm {full_date.year}"

        date_label = QLabel(date_str)
        date_label.setObjectName("DateHeaderLabel")
        date_label.setAlignment(Qt.AlignCenter)

        header_font = QApplication.instance().font()
        header_font.setPointSize(16)
        header_font.setBold(True)
        date_label.setFont(header_font)
        
        main_layout.addWidget(date_label)

        # Khu vực cuộn để chứa danh sách công việc
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        tasks_layout = QVBoxLayout(scroll_content)
        tasks_layout.setAlignment(Qt.AlignTop)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # Thêm từng công việc vào danh sách
        if tasks_list:
            for task in tasks_list:
                detail_item = TaskDetailItemWidget(
                    task.label.text(),
                    task.checkbox.isChecked(),
                    task.note
                )
                tasks_layout.addWidget(detail_item)
        else:
            tasks_layout.addWidget(QLabel("Không có công việc nào trong ngày này."))

        # Nút Đóng
        close_button = QPushButton("Đóng")
        close_button.clicked.connect(self.accept)
        main_layout.addWidget(close_button, 0, Qt.AlignRight)

class TaskWidget(QFrame):
    """
        Widget đại diện cho một công việc (task).
        Nó có thể được kéo (drag) và thả (drop) vào một DayWidget khác.
    """
    def __init__(self, text, is_done=False, note="", parent=None):
        # Gọi hàm khởi tạo của lớp cha (QFrame)
        super().__init__(parent)
        # Đặt tên object để có thể áp dụng CSS sau này
        self.setObjectName("TaskWidget")
        # Đặt kiểu khung viền
        self.setFrameShape(QFrame.StyledPanel)
        # Đổi con trỏ chuột thành hình bàn tay khi di vào để báo hiệu có thể tương tác
        self.setCursor(QCursor(Qt.PointingHandCursor))

        # Lưu lại nội dung ghi chú
        self.note = note

        # --- Giao diện của Widget ---
        # Tạo layout ngang để chứa checkbox và nhãn tên công việc
        self.layout = QHBoxLayout(self)
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(is_done)  # Đặt trạng thái (đã hoàn thành hay chưa)
        self.label = QLabel(text)          # Hiển thị tên công việc
        
        # Tạo một label để hiển thị icon ghi chú
        self.note_icon_label = QLabel()
        # Lấy icon tài liệu chuẩn từ style của hệ điều hành
        note_icon = self.style().standardIcon(QStyle.SP_FileIcon)
        self.note_icon_label.setPixmap(note_icon.pixmap(16, 16)) # Đặt kích thước icon
        
        # Thêm checkbox và label vào layout
        self.layout.addWidget(self.checkbox)
        self.layout.addWidget(self.label)
        self.layout.addStretch() # Thêm bộ đệm để đẩy icon sang phải
        self.layout.addWidget(self.note_icon_label)

        # Cập nhật hiển thị (ẩn/hiện icon) dựa trên việc có ghi chú hay không
        self._update_note_icon()
    
    def _update_note_icon(self):
        """Ẩn hoặc hiện icon ghi chú tùy thuộc vào nội dung của self.note."""
        # Nếu self.note có nội dung (không phải chuỗi rỗng) thì hiện icon, và ngược lại
        self.note_icon_label.setVisible(bool(self.note))

    # Xử lý sự kiện nháy đúp chuột
    def mouseDoubleClickEvent(self, event):
        """Mở hộp thoại để người dùng xem/sửa ghi chú khi nháy đúp chuột."""
        # Mở hộp thoại nhập văn bản nhiều dòng (getMultiLineText)
        new_note, ok = QInputDialog.getMultiLineText(self, "Sửa Ghi Chú", "Nội dung ghi chú:", self.note)
        
        if ok:
            # Nếu người dùng nhấn OK, cập nhật lại ghi chú
            self.note = new_note
            # Cập nhật lại trạng thái hiển thị của icon
            self._update_note_icon()
   
    def mousePressEvent(self, event):
        """
            Sự kiện này được gọi khi người dùng nhấn chuột vào widget. 
            Lưu lại vị trí bắt đầu kéo.
        """
        # Chỉ xử lý khi nhấn chuột trái
        if event.button() == Qt.LeftButton:
            # Lưu lại vị trí bắt đầu nhấn chuột để xác định khi nào bắt đầu kéo
            self.drag_start_position = event.pos()

    def mouseMoveEvent(self, event):
        """
            Sự kiện này được gọi khi người dùng di chuyển chuột
            Kéo thả tạo bản Copy
        """
        # Nếu không phải đang nhấn chuột trái thì bỏ qua
        if not (event.buttons() & Qt.LeftButton):
            return
        # Nếu khoảng cách di chuyển chưa đủ lớn (theo thiết lập của hệ thống), thì chưa bắt đầu kéo
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return

        # --- Bắt đầu quá trình kéo (Drag) ---
        drag = QDrag(self)
        # Tạo dữ liệu MIME để mang thông tin trong lúc kéo
        mime_data = QMimeData()

        # Truyền text của label để nơi nhận có thể tạo bản sao
        mime_data.setProperty("task_widget_ref", self)
        drag.setMimeData(mime_data)
        
        # Tạo một ảnh xem trước (preview) của widget khi đang kéo
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        # Đặt điểm nóng của con trỏ (vị trí con trỏ so với ảnh preview)
        drag.setHotSpot(event.pos())

        # Chỉ thực hiện hành động CopyAction
        drag.exec_(Qt.CopyAction)
    
    
    def contextMenuEvent(self, event):
        """
            Tạo menu ngữ cảnh khi chuột phải vào một công việc.
        """
        context_menu = QMenu(self)
        
        # Tạo một hành động (action) "Xóa"
        delete_action = context_menu.addAction("Xóa công việc này")
        
        # Thực hiện hành động khi người dùng chọn một mục trong menu
        # event.pos() là vị trí chuột tương đối với widget
        # self.mapToGlobal(event.pos()) chuyển đổi nó thành tọa độ toàn màn hình
        action = context_menu.exec_(self.mapToGlobal(event.pos()))
        
        # Nếu hành động được chọn là "Xóa"
        if action == delete_action:
            # Tự xóa widget này
            self.deleteLater()

class DayWidget(QFrame):
    """
        Widget đại diện cho một ô ngày trong lịch.
        Nó có thể nhận (drop) các TaskWidget.
    """
    def __init__(self, date_text, year, month, parent=None):
        super().__init__(parent)
        self.setObjectName("DayWidget")
        self.setFrameShape(QFrame.StyledPanel)
        # Quan trọng: Bật tính năng chấp nhận thả (drop) cho widget này
        self.setAcceptDrops(True)

        # Lưu lại thông tin ngày tháng năm
        self.day = int(date_text)
        self.year = year
        self.month = month

        # Layout chính của ô ngày, theo chiều dọc
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignTop) # Căn các mục con lên trên cùng

        # Nhãn để hiển thị số ngày (ví dụ: 1, 2, 3...)
        self.date_label = QLabel(date_text)
        self.date_label.setObjectName("DateLabel")
        self.date_label.setAlignment(Qt.AlignRight) # Căn lề phải cho đẹp
        self.main_layout.addWidget(self.date_label)

        # Layout dọc con để chứa danh sách các công việc
        self.tasks_layout = QVBoxLayout()
        self.main_layout.addLayout(self.tasks_layout)

    # Thêm sự kiện nháy đúp chuột
    def mouseDoubleClickEvent(self, event):
        # Kiểm tra xem có bấm vào một TaskWidget con hay không
        child_widget = self.childAt(event.pos())
        # Nếu không bấm vào widget con nào (bấm vào vùng trống)
        if child_widget is None or child_widget == self:
            tasks_list = []
            # Lấy tất cả các TaskWidget con
            for i in range(self.tasks_layout.count()):
                widget = self.tasks_layout.itemAt(i).widget()
                if isinstance(widget, TaskWidget):
                    tasks_list.append(widget)
            
            # Tạo ngày đầy đủ từ thông tin đã lưu
            full_date = datetime(self.year, self.month, self.day)
            
            # Tạo và hiển thị dialog
            dialog = DayDetailDialog(full_date, tasks_list, self)
            dialog.exec_()
        else:
            # Nếu bấm vào một TaskWidget, chuyển sự kiện cho nó xử lý
            super().mouseDoubleClickEvent(event)

    def add_task(self, task_widget):
        """
            Hàm để thêm một TaskWidget vào danh sách công việc của ngày này.
        """
        self.tasks_layout.addWidget(task_widget)

    def dragEnterEvent(self, event):
        """
            Sự kiện này được gọi khi một đối tượng kéo (drag) đi vào không gian của widget này.
        """
        # Kiểm tra xem dữ liệu được kéo có phải là "task_widget" mà ta đã định nghĩa không.
        # Nếu đúng, chấp nhận hành động thả.
        if event.mimeData().property("task_widget_ref"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        """
            Sự kiện này được gọi khi người dùng thả đối tượng vào widget này.
            Luôn tạo một công việc mới (Bản sao)
        """
        # Dữ liệu tham chiếu tạo bản sao
        source_widget = event.mimeData().property("task_widget_ref")

        # Nếu có tham chiếu đến widget gốc
        if source_widget:
            # Lấy thông tin trực tiếp từ các thuộc tính của widget gốc
            task_text = source_widget.label.text()
            note_text = source_widget.note
            
            # Tạo TaskWidget mới (bản sao) với thông tin đã lấy
            new_task = TaskWidget(task_text, note=note_text)
            self.add_task(new_task)
            event.setDropAction(Qt.CopyAction)
            event.accept()

    def contextMenuEvent(self, event):
        context_menu = QMenu(self)
        add_task_action = context_menu.addAction("Thêm công việc mới")
        action = context_menu.exec_(self.mapToGlobal(event.pos()))
        if action == add_task_action:
            self._prompt_for_new_task()

    def _prompt_for_new_task(self):
        task_text, ok = QInputDialog.getText(self, "Công việc mới", "Nhập tên công việc:")
        if ok and task_text:
            # Khi thêm mới, ghi chú mặc định là rỗng
            new_task = TaskWidget(task_text, note="")
            self.add_task(new_task)