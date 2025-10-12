# --- Nhập các thư viện và module cần thiết ---
import os
from datetime import datetime, timedelta
import time

# Nhập các lớp widget và công cụ từ PyQt5
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QScrollArea, QFrame,
                             QGridLayout, QGroupBox, QComboBox, QMessageBox,
                             QDateTimeEdit, QGraphicsDropShadowEffect, QMenu, QAction)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QDateTime
from PyQt5.QtGui import QIcon, QColor

# Nhập các module và cấu hình tùy chỉnh của dự án
from Managers.database_manager import Database
from config import (ICON_DIR, COLOR_BACKGROUND, COLOR_PRIMARY, COLOR_SUCCESS, 
                    COLOR_DANGER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, 
                    COLOR_BORDER, COLOR_HOVER, PRIORITY_COLORS, COLOR_WHITE)


# ==============================================================================
# LỚP 1: TaskItemWidget - Widget hiển thị một công việc trong danh sách
# ==============================================================================
class TaskItemWidget(QFrame):
    """
    Widget đại diện cho một mục công việc trong danh sách.
    Hiển thị tiêu đề, ghi chú, thông tin chi tiết và các nút hành động.
    """
    # Định nghĩa các tín hiệu (signals) để giao tiếp với widget cha (DoNowView)
    task_toggled = pyqtSignal(str)  # Phát ra khi trạng thái hoàn thành thay đổi
    task_deleted = pyqtSignal(str)  # Phát ra khi người dùng nhấn nút xóa
    task_started = pyqtSignal(str)  # Phát ra khi người dùng nhấn nút bắt đầu

    def __init__(self, task_details, timer_metadata, parent=None):
        """
        Khởi tạo widget.
        
        Args:
            task_details (dict): Dictionary chứa thông tin của công việc.
            timer_metadata (dict): Dictionary chứa thông tin về thời gian (vd: thời gian bắt đầu).
            parent (QWidget): Widget cha.
        """
        super().__init__(parent)
        self.task_id = task_details['id']  # Lưu ID của công việc
        self.task_details = task_details
        self.timer_metadata = timer_metadata
        self.initialize_ui()  # Cài đặt giao diện
        self.apply_shadow_effect()  # Áp dụng hiệu ứng đổ bóng

    def initialize_ui(self):
        """Xây dựng giao diện cho một mục công việc."""
        self.setObjectName("TaskItemWidget")
        is_done = self.task_details['is_done']
        
        # Thiết lập CSS cho widget, có thay đổi style nếu công việc đã hoàn thành
        self.setStyleSheet(f"""
            #TaskItemWidget {{
                background-color: {COLOR_WHITE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px; padding: 12px; margin: 4px 8px;
            }}
            #TaskItemWidget[done="true"] {{ background-color: #F8F9FA; }}
            QLabel {{ background-color: transparent; border: none; }}
        """)
        self.setProperty("done", is_done)  # Đặt thuộc tính "done" để CSS có thể áp dụng

        main_layout = QHBoxLayout(self)  # Layout chính, sắp xếp theo chiều ngang

        # Layout chứa nội dung chữ (tiêu đề, ghi chú, chi tiết)
        content_layout = QVBoxLayout()
        title_label = QLabel(self.task_details['title'])
        # Thay đổi style của tiêu đề nếu công việc đã xong (gạch ngang, màu xám)
        if is_done:
            title_label.setStyleSheet(f"font-size: 15px; text-decoration: line-through; color: {COLOR_TEXT_SECONDARY};")
        else:
            title_label.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        content_layout.addWidget(title_label)

        # Hiển thị ghi chú nếu có
        note_text = self.task_details.get('note', '')
        if note_text:
            note_label = QLabel(note_text)
            note_label.setStyleSheet(f"font-size:12px; color: {COLOR_TEXT_SECONDARY}; padding-top:4px;")
            content_layout.addWidget(note_label)
        
        # Xây dựng chuỗi thông tin chi tiết (độ ưu tiên, hạn chót, thời gian ước tính)
        details_parts = []
        priority = self.task_details.get('priority', 4)
        if priority < 4:
            priority_color = PRIORITY_COLORS.get(priority, COLOR_TEXT_SECONDARY)
            details_parts.append(f"<b style='color:{priority_color};'>Ưu tiên {priority}</b>")

        if self.task_details['due_at']:
            try:
                due_date = datetime.fromisoformat(self.task_details['due_at'])
                details_parts.append(f"📅 {due_date.strftime('%d/%m %H:%M')}")
            except (ValueError, TypeError):
                details_parts.append(f"📅 {self.task_details['due_at']}")
        
        if self.task_details['estimated_minutes']:
            details_parts.append(f"⏱️ {self.task_details['estimated_minutes']} phút")

        # Hiển thị chuỗi thông tin chi tiết nếu có
        if details_parts:
            details_label = QLabel("  •  ".join(details_parts))
            details_label.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_SECONDARY}; padding-top: 4px;")
            content_layout.addWidget(details_label)

        # Layout cho các nút hành động (hoàn thành, xóa, ...)
        action_layout = QHBoxLayout()
        action_layout.setSpacing(5)
        action_layout.setAlignment(Qt.AlignRight)

        # Hiển thị các nút tùy thuộc vào trạng thái công việc
        if not is_done:
            start_button = self._create_icon_button(os.path.join(ICON_DIR, 'play.svg'), "Bắt đầu tính giờ")
            start_button.clicked.connect(lambda: self.task_started.emit(self.task_id))
            
            complete_button = self._create_icon_button(os.path.join(ICON_DIR, 'check-circle.svg'), "Đánh dấu hoàn thành")
            complete_button.clicked.connect(lambda: self.task_toggled.emit(self.task_id))
            
            action_layout.addWidget(start_button)
            action_layout.addWidget(complete_button)
        else:
            undo_button = self._create_icon_button(os.path.join(ICON_DIR, 'rotate-ccw.svg'), "Đánh dấu chưa hoàn thành")
            undo_button.clicked.connect(lambda: self.task_toggled.emit(self.task_id))
            action_layout.addWidget(undo_button)
            
        delete_button = self._create_icon_button(os.path.join(ICON_DIR, 'x-circle.svg'), "Xóa công việc")
        delete_button.clicked.connect(lambda: self.task_deleted.emit(self.task_id))
        action_layout.addWidget(delete_button)

        # Gắn các layout con vào layout chính
        main_layout.addLayout(content_layout)
        main_layout.addStretch()  # Đẩy các nút hành động về phía bên phải
        main_layout.addLayout(action_layout)

    def _create_icon_button(self, icon_path, tooltip):
        """Hàm trợ giúp để tạo một QPushButton chỉ có icon."""
        button = QPushButton()
        if os.path.exists(icon_path):
            button.setIcon(QIcon(icon_path))
        button.setFixedSize(28, 28)
        button.setToolTip(tooltip)
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet("QPushButton { border-radius: 14px; background-color: transparent; } QPushButton:hover { background-color: #e0e0e0; }")
        return button
        
    def apply_shadow_effect(self):
        """Áp dụng hiệu ứng đổ bóng nhẹ cho widget."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(0, 0, 0, 25))
        self.setGraphicsEffect(shadow)


# ==============================================================================
# LỚP 2: DoNowView - Widget chính của trang "My Tasks"
# ==============================================================================
class DoNowView(QWidget):
    """
    Widget chính chứa toàn bộ giao diện của trang "My Tasks", bao gồm form thêm
    việc, thanh lọc, danh sách công việc và điều khiển phân trang.
    """
    def __init__(self, user_id=None, db_manager=None, parent=None):
        super().__init__(parent)
        self.current_user_id = user_id
        self.db_manager = db_manager if db_manager else Database()
        
        # Các biến trạng thái để quản lý dữ liệu và giao diện
        self.all_tasks = []  # Lưu tất cả công việc lấy từ CSDL
        self.timer_metadata = {}  # Lưu thông tin timer cho mỗi công việc
        self.task_history = {} # Lưu lịch sử tương tác (chưa dùng tới)
        self.search_query = ""
        self.filter_status = "all"  # 'all', 'pending', 'done'
        self.current_page = 1
        self.items_per_page = 10
        self.current_priority_selection = 2  # Mặc định là ưu tiên trung bình

        self.setup_ui()  # Bắt đầu xây dựng giao diện
        self.load_data_from_db()  # Tải dữ liệu từ CSDL

        # Timer để kiểm tra các công việc sắp hết hạn
        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self._check_upcoming_deadlines)
        self.notification_timer.start(60 * 1000)  # Chạy mỗi phút

    def setup_ui(self):
        """Xây dựng toàn bộ giao diện của trang."""
        self.setObjectName("DoNowView")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(20)

        # Tiêu đề chính của trang
        header_label = QLabel("Công việc của tôi")
        header_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        main_layout.addWidget(header_label)

        # Thêm các nhóm widget con vào layout chính
        main_layout.addWidget(self._create_add_task_form())
        main_layout.addWidget(self._create_filter_bar())
        main_layout.addWidget(self._create_task_list_area(), 1) # Chiếm phần lớn không gian
        main_layout.addLayout(self._create_pagination_controls())

    def _create_add_task_form(self):
        """Tạo form để người dùng nhập công việc mới."""
        form_group = QGroupBox("✨ Thêm công việc mới")
        layout = QGridLayout(form_group)
        
        # Các ô nhập liệu
        self.title_input = QLineEdit(placeholderText="VD: Hoàn thành báo cáo dự án")
        self.due_date_input = QDateTimeEdit(calendarPopup=True)
        self.due_date_input.setDateTime(QDateTime.currentDateTime())
        self.estimated_time_input = QLineEdit(placeholderText="Thời gian (phút)")
        self.note_input = QLineEdit(placeholderText="Ghi chú (tùy chọn)")
        
        # Nút chọn độ ưu tiên
        self.priority_button = QPushButton()
        self.priority_button.setToolTip("Chọn độ ưu tiên")
        self._update_priority_button_icon(self.current_priority_selection) # Đặt icon mặc định
        self.priority_button.clicked.connect(self._show_priority_menu)

        # Nút "Thêm"
        add_task_button = QPushButton("Thêm công việc")
        add_task_button.setObjectName("MainCTA") # Đặt tên để áp dụng CSS
        add_task_button.clicked.connect(self._handle_add_task)

        # Sắp xếp các widget vào lưới
        layout.addWidget(self.title_input, 0, 0, 1, 2)
        layout.addWidget(self.due_date_input, 1, 0)
        layout.addWidget(self.estimated_time_input, 1, 1)
        layout.addWidget(self.priority_button, 1, 2)
        layout.addWidget(add_task_button, 0, 2, 1, 1)
        layout.addWidget(self.note_input, 2, 0, 1, 3)
        
        # Cho phép nhấn Enter để thêm việc
        self.title_input.returnPressed.connect(self._handle_add_task)
        return form_group

    def _show_priority_menu(self):
        """Hiển thị menu ngữ cảnh để chọn độ ưu tiên."""
        menu = QMenu(self)
        priority_map = {1: "Cao", 2: "Trung bình", 3: "Thấp"}
        icon_map = {1: 'flag-red.svg', 2: 'flag-green.svg', 3: 'flag-blue.svg'}
        
        for priority_value, priority_name in priority_map.items():
            icon_path = os.path.join(ICON_DIR, icon_map[priority_value])
            action = QAction(QIcon(icon_path), f"Ưu tiên: {priority_name}", self)
            action.triggered.connect(lambda _, p=priority_value: self._update_priority_button_icon(p))
            menu.addAction(action)
            
        menu.exec_(self.priority_button.mapToGlobal(self.priority_button.rect().bottomLeft()))

    def _update_priority_button_icon(self, priority):
        """Cập nhật icon và trạng thái độ ưu tiên được chọn."""
        self.current_priority_selection = priority
        icon_map = {1: 'flag-red.svg', 2: 'flag-green.svg', 3: 'flag-blue.svg'}
        icon_path = os.path.join(ICON_DIR, icon_map.get(priority))
        if os.path.exists(icon_path):
            self.priority_button.setIcon(QIcon(icon_path))

    def _create_filter_bar(self):
        """Tạo thanh chứa ô tìm kiếm và bộ lọc trạng thái."""
        filter_container = QFrame()
        layout = QHBoxLayout(filter_container)
        layout.setContentsMargins(0,0,0,0)
        
        self.search_input = QLineEdit(placeholderText="Tìm kiếm công việc...")
        self.search_input.textChanged.connect(self._handle_search_change)
        
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(["Tất cả trạng thái", "Đang chờ", "Hoàn thành"])
        self.status_filter_combo.currentIndexChanged.connect(self._handle_filter_change)
        
        layout.addWidget(self.search_input, 1)
        layout.addWidget(self.status_filter_combo)
        return filter_container

    def _create_task_list_area(self):
        """Tạo khu vực có thể cuộn để chứa danh sách các công việc."""
        list_group = QGroupBox("📌 Danh sách công việc")
        layout = QVBoxLayout(list_group)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        self.tasks_container_widget = QWidget() # Widget chứa các TaskItemWidget
        self.tasks_container_widget.setObjectName("TasksContainer")
        self.tasks_list_layout = QVBoxLayout(self.tasks_container_widget)
        self.tasks_list_layout.setAlignment(Qt.AlignTop)
        
        scroll_area.setWidget(self.tasks_container_widget)
        layout.addWidget(scroll_area)
        return list_group

    def _create_pagination_controls(self):
        """Tạo các nút "Trước", "Sau" và nhãn hiển thị trang."""
        pagination_layout = QHBoxLayout()
        self.prev_page_button = QPushButton("Trước")
        self.next_page_button = QPushButton("Sau")
        self.prev_page_button.setObjectName("PaginationButton")
        self.next_page_button.setObjectName("PaginationButton")
        self.page_label = QLabel(f"Trang {self.current_page}")
        
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.prev_page_button)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_page_button)
        pagination_layout.addStretch()
        
        self.prev_page_button.clicked.connect(lambda: self._handle_page_change(-1))
        self.next_page_button.clicked.connect(lambda: self._handle_page_change(1))
        return pagination_layout

    def load_data_from_db(self):
        """Tải danh sách công việc từ CSDL và lưu vào `self.all_tasks`."""
        try:
            # Lấy tất cả công việc của người dùng
            task_rows = self.db_manager.get_tasks_for_user(self.current_user_id)
            self.all_tasks = []
            for row in task_rows:
                # Chuyển đổi mỗi hàng từ tuple sang dictionary để dễ làm việc
                self.all_tasks.append({
                    "id": str(row[0]), "title": row[1], "is_done": bool(row[2]),
                    "due_at": row[3], "estimated_minutes": row[4],
                    "priority": row[5], "note": row[6]
                })
        except Exception as error:
            print(f"Lỗi khi tải danh sách công việc: {error}")
        self.render_tasks_on_ui() # Sau khi tải xong, vẽ lại giao diện

    def get_visible_tasks(self):
        """
        Thực hiện lọc, sắp xếp và phân trang danh sách công việc.
        Đây là hàm logic cốt lõi của trang.
        
        Returns:
            tuple: (danh sách tất cả công việc đã lọc, danh sách công việc cho trang hiện tại)
        """
        # 1. Hàm sắp xếp: Ưu tiên công việc chưa xong, sau đó đến độ ưu tiên, rồi đến hạn chót
        def sort_key(task):
            # (False, 1, ...) sẽ đứng trước (True, 2, ...)
            return (task['is_done'], task.get('priority', 4))

        sorted_tasks = sorted(self.all_tasks, key=sort_key)
        
        # 2. Hàm lọc: Lọc theo trạng thái và từ khóa tìm kiếm
        def filter_function(task):
            match_status = (self.filter_status == "all" or
                            (self.filter_status == "pending" and not task['is_done']) or
                            (self.filter_status == "done" and task['is_done']))
            
            match_search = self.search_query.lower() in task['title'].lower()
            return match_status and match_search
            
        filtered_tasks = list(filter(filter_function, sorted_tasks))
        
        # 3. Phân trang: Lấy ra lát cắt dữ liệu cho trang hiện tại
        start_index = (self.current_page - 1) * self.items_per_page
        end_index = start_index + self.items_per_page
        paginated_tasks = filtered_tasks[start_index:end_index]
        
        return filtered_tasks, paginated_tasks

    def render_tasks_on_ui(self):
        """Vẽ lại danh sách công việc trên giao diện dựa trên trạng thái hiện tại."""
        # Xóa tất cả widget công việc cũ
        while self.tasks_list_layout.count():
            child = self.tasks_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        all_filtered, visible_tasks = self.get_visible_tasks()
        
        if not visible_tasks:
            # Hiển thị thông báo nếu không có công việc nào
            no_tasks_label = QLabel("🎉 Tuyệt vời! Bạn không có công việc nào cần làm.")
            no_tasks_label.setAlignment(Qt.AlignCenter)
            self.tasks_list_layout.addWidget(no_tasks_label)
        else:
            # Tạo và thêm widget cho từng công việc
            for task_details in visible_tasks:
                task_widget = TaskItemWidget(task_details, self.timer_metadata.get(task_details['id'], {}))
                # Kết nối các tín hiệu từ widget con đến các hàm xử lý của widget cha
                task_widget.task_toggled.connect(self._handle_toggle_task)
                task_widget.task_deleted.connect(self._handle_delete_task)
                task_widget.task_started.connect(self._handle_start_task)
                self.tasks_list_layout.addWidget(task_widget)
        
        self.tasks_list_layout.addStretch() # Đẩy các mục lên trên
        
        # Cập nhật lại trạng thái của các nút phân trang
        self.page_label.setText(f"Trang {self.current_page}")
        self.prev_page_button.setEnabled(self.current_page > 1)
        self.next_page_button.setEnabled(len(all_filtered) > self.current_page * self.items_per_page)

    # --- Các hàm xử lý sự kiện ---

    def _handle_add_task(self):
        """Xử lý khi người dùng nhấn nút 'Thêm công việc'."""
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập tiêu đề công việc.")
            return

        due_at = self.due_date_input.dateTime().toPyDateTime().strftime('%Y-%m-%d %H:%M:%S')
        estimated_str = self.estimated_time_input.text().strip()
        estimated_minutes = int(estimated_str) if estimated_str.isdigit() else None
        note = self.note_input.text().strip()
        
        try:
            self.db_manager.add_task_with_meta(
                user_id=self.current_user_id, title=title, note=note, 
                due_at=due_at, estimated_minutes=estimated_minutes, 
                priority=self.current_priority_selection
            )
            # Xóa nội dung trong form và tải lại dữ liệu
            self.title_input.clear()
            self.estimated_time_input.clear()
            self.note_input.clear()
            self.load_data_from_db()
        except Exception as error:
            QMessageBox.critical(self, "Lỗi CSDL", f"Không thể thêm công việc: {error}")
    
    def _handle_toggle_task(self, task_id):
        """Xử lý khi trạng thái hoàn thành của một công việc thay đổi."""
        try:
            # Tìm công việc trong danh sách và cập nhật trạng thái
            task = next(t for t in self.all_tasks if t['id'] == task_id)
            new_status = not task['is_done']
            self.db_manager.update_task_status(int(task_id), int(new_status))
            task['is_done'] = new_status  # Cập nhật trạng thái trong danh sách local
            self.render_tasks_on_ui()  # Vẽ lại giao diện
        except (StopIteration, Exception) as error:
            print(f"Lỗi khi cập nhật trạng thái công việc: {error}")

    def _handle_delete_task(self, task_id):
        """Xử lý khi người dùng xóa một công việc."""
        try:
            self.db_manager.delete_task(int(task_id))
            # Xóa công việc khỏi danh sách local và vẽ lại giao diện
            self.all_tasks = [t for t in self.all_tasks if t['id'] != task_id]
            self.render_tasks_on_ui()
        except Exception as error:
            print(f"Lỗi khi xóa công việc: {error}")

    def _handle_start_task(self, task_id):
        """Xử lý khi người dùng bắt đầu tính giờ cho một công việc."""
        self.timer_metadata.setdefault(task_id, {})['start'] = time.time()
        QMessageBox.information(self, "Bắt đầu", "Đã bắt đầu tính giờ cho công việc.")

    def _handle_search_change(self, text):
        """Xử lý khi người dùng thay đổi từ khóa tìm kiếm."""
        self.search_query = text
        self.current_page = 1  # Quay về trang đầu tiên khi có tìm kiếm mới
        self.render_tasks_on_ui()

    def _handle_filter_change(self, index):
        """Xử lý khi người dùng thay đổi bộ lọc trạng thái."""
        filter_map = {0: "all", 1: "pending", 2: "done"}
        self.filter_status = filter_map.get(index)
        self.current_page = 1  # Quay về trang đầu tiên
        self.render_tasks_on_ui()
        
    def _handle_page_change(self, delta):
        """Xử lý khi người dùng nhấn nút 'Trước' hoặc 'Sau'."""
        self.current_page = max(1, self.current_page + delta)
        self.render_tasks_on_ui()
        
    def _check_upcoming_deadlines(self):
        """Kiểm tra và thông báo cho các công việc sắp hết hạn."""
        now = datetime.now()
        for task in self.all_tasks:
            if not task['is_done'] and task['due_at']:
                try:
                    due_date = datetime.fromisoformat(task['due_at'])
                    time_left = due_date - now
                    # Nếu thời gian còn lại từ 0 đến 15 phút
                    if timedelta(minutes=0) < time_left <= timedelta(minutes=15):
                        QMessageBox.warning(self, "Nhắc nhở", f"Công việc '{task['title']}' sắp đến hạn!\n"
                                                              f"Còn khoảng {time_left.seconds // 60} phút.")
                except (ValueError, TypeError):
                    continue