# --- Nhập các thư viện và module cần thiết ---
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QLabel, QMessageBox, QStackedWidget, QDialog)
from PyQt5.QtCore import Qt

# --- Nhập các module và widget tùy chỉnh của dự án ---
from MainMenu.side_panel import SidePanel
from MainMenu.calendar_widget import CalendarWidget
from MainMenu.home_page import DoNowView
from MainMenu.group_dialogs import GroupSelectionDialog, MemberListDialog, AddMemberDialog
from Managers.database_manager import Database

# ==============================================================================
# STYLESHEET (QSS) - Dùng để định dạng giao diện cho toàn bộ cửa sổ
# ==============================================================================
STYLESHEET = """
    /* --- Kiểu chung --- */
    #MainWindow { background-color: #f0f0f0; }
    #SidePanel { background-color: #e9e9e9; border-right: 1px solid #d0d0d0; }
    #InfoValueLabel { font-weight: bold; font-size: 14px; }
    
    /* --- Kiểu nút bấm trong thanh bên --- */
    #SidePanel QPushButton { 
        background-color: #ffffff; 
        border: 1px solid #c0c0c0; 
        border-radius: 15px; 
        padding: 10px; 
        font-weight: bold; 
    }
    #SidePanel QPushButton:hover { background-color: #f5f5f5; }
    
    /* Nút bị vô hiệu hóa (cho biết tab đang được chọn) */
    #SidePanel QPushButton:disabled {
        background-color: #e0e0e0;
        color: #888888;
        border-color: #b0b0b0;
    }

    /* Kiểu riêng cho nút Đăng xuất */
    #ExitButton { background-color: #ffe0e0; border-color: #ffaaaa; }
    #ExitButton:hover { background-color: #ffcccc; }
    
    /* --- Các kiểu khác cho widget con --- */
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
    Cửa sổ chính của ứng dụng, chứa thanh điều hướng bên trái (SidePanel)
    và khu vực hiển thị nội dung chính (Trang chủ hoặc Lịch).
    Đây là "trung tâm điều khiển" của ứng dụng sau khi người dùng đăng nhập.
    """

    def __init__(self, user_id, user_name, default_role='Cá nhân', parent=None):
        super().__init__(parent)
        
        # --- Các biến trạng thái (state) của cửa sổ ---
        self.current_user_id = user_id
        self.current_user_name = user_name
        self.default_role_name = default_role
        
        self.current_view_mode = 'personal'  # 'personal' hoặc 'group'
        self.current_content_view = 'home'  # 'home' hoặc 'calendar'
        
        self.current_group_id = None
        self.current_group_name = None
        self.is_current_user_leader = False
        
        self._is_logging_out = False  # Cờ để xử lý sự kiện đóng cửa sổ khi đăng xuất

        # Tạo một đối tượng quản lý CSDL duy nhất để chia sẻ cho các widget con
        self.db_manager = Database()

        # Cài đặt thuộc tính cơ bản cho cửa sổ
        self.setWindowTitle("Todo List Pro")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(STYLESHEET)
        self.setObjectName("MainWindow")

        self.initialize_ui()  # Bắt đầu xây dựng giao diện người dùng
        
        # Cập nhật thông tin ban đầu cho SidePanel
        self.side_panel.set_user_info(self.current_user_name, self.default_role_name)
        self.side_panel.update_view_mode(self.current_view_mode, is_leader=False)

        # Lấy thông tin hình học của màn hình chính
        screen_geometry = QApplication.primaryScreen().geometry()
        
        # Lấy thông tin hình học của cửa sổ ứng dụng (bao gồm cả viền)
        window_geometry = self.frameGeometry()
        
        # Di chuyển tâm của hình chữ nhật cửa sổ đến tâm của màn hình
        window_geometry.moveCenter(screen_geometry.center())
        
        # Di chuyển vị trí top-left của cửa sổ đến vị trí mới đã tính toán
        self.move(window_geometry.topLeft())

    def initialize_ui(self):
        """
        Thiết lập và sắp xếp tất cả các widget con trong cửa sổ chính.
        """
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Layout chính, chia cửa sổ thành 2 phần: thanh bên và nội dung
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Thanh điều hướng bên trái ---
        self.side_panel = SidePanel()
        self.main_layout.addWidget(self.side_panel)
        
        # --- Khu vực nội dung bên phải ---
        right_panel_layout = QVBoxLayout()
        right_panel_layout.setContentsMargins(10, 10, 10, 10)
        right_panel_layout.setSpacing(10)

        # Nhãn hiển thị tên nhóm (mặc định sẽ bị ẩn)
        self.group_title_label = QLabel("Tên Nhóm")
        self.group_title_label.setObjectName("GroupTitleLabel")
        self.group_title_label.setAlignment(Qt.AlignCenter)
        self.group_title_label.hide() # Ẩn đi lúc đầu
        right_panel_layout.addWidget(self.group_title_label)

        # QStackedWidget: một widget cho phép chứa nhiều widget khác và chỉ hiển thị một cái tại một thời điểm
        # Rất lý tưởng để chuyển đổi giữa các màn hình
        self.content_stack = QStackedWidget()
        right_panel_layout.addWidget(self.content_stack)
        self.main_layout.addLayout(right_panel_layout, 1) # 1: cho phép khu vực này co giãn

        # --- Khởi tạo các màn hình con và thêm vào StackedWidget ---
        # Màn hình Trang chủ (My Tasks)
        self.home_widget = DoNowView(self.current_user_id, db_manager=self.db_manager)
        self.content_stack.addWidget(self.home_widget)

        # Màn hình Lịch
        self.calendar_widget = CalendarWidget(self.current_user_id, db_manager=self.db_manager)
        self.content_stack.addWidget(self.calendar_widget)

        self.content_stack.setCurrentWidget(self.home_widget) # Đặt màn hình Trang chủ làm mặc định

        # --- Kết nối tín hiệu (signals) từ SidePanel đến các hàm xử lý (slots) ---
        self.side_panel.personal_area_requested.connect(self._handle_personal_view_request)
        self.side_panel.group_area_requested.connect(self._handle_group_view_request)
        self.side_panel.home_requested.connect(self._handle_home_view_request)
        self.side_panel.calendar_requested.connect(self._handle_calendar_view_request)
        self.side_panel.exit_requested.connect(self._handle_logout_request)
        self.side_panel.member_list_requested.connect(self._show_member_list)
        self.side_panel.add_member_requested.connect(self._show_add_member_dialog)

    # --- Các hàm xử lý sự kiện chính (Event Handlers / Slots) ---

    def _handle_personal_view_request(self):
        """Chuyển ứng dụng về chế độ xem công việc cá nhân."""
        print("Chuyển sang khu vực cá nhân...")
        self.current_view_mode = 'personal'
        self.current_group_id = None
        self.is_current_user_leader = False
        
        self.group_title_label.hide() # Ẩn tiêu đề nhóm
        self.side_panel.set_user_info(self.current_user_name, self.default_role_name)
        self.side_panel.update_view_mode(self.current_view_mode, is_leader=False)
        
        # Yêu cầu các widget con tự cập nhật lại dữ liệu cho chế độ cá nhân
        self.home_widget.load_data_from_db()
        self.calendar_widget.switch_view_mode(mode='personal')

    def _handle_group_view_request(self):
        """Mở cửa sổ chọn nhóm và chuyển sang chế độ xem công việc nhóm."""
        print("Yêu cầu chuyển sang khu vực nhóm...")
        dialog = GroupSelectionDialog(self.current_user_id, self)
        
        # Nếu người dùng chọn một nhóm và nhấn OK
        if dialog.exec_() == QDialog.Accepted and dialog.selected_group:
            group_id, group_name = dialog.selected_group
            self._load_group_context(group_id, group_name)
        else:
            # Nếu người dùng hủy, đảm bảo các nút trên side_panel quay về trạng thái cũ
            self.side_panel.update_view_mode(self.current_view_mode, self.is_current_user_leader)

    def _handle_home_view_request(self):
        """Chuyển màn hình hiển thị sang Trang chủ (My Tasks)."""
        print("Chuyển sang màn hình Trang chủ...")
        self.current_content_view = 'home'
        self.content_stack.setCurrentWidget(self.home_widget)
        # Tải lại dữ liệu cho trang chủ
        self.home_widget.load_data_from_db()

    def _handle_calendar_view_request(self):
        """Chuyển màn hình hiển thị sang Lịch."""
        print("Chuyển sang màn hình Lịch...")
        self.current_content_view = 'calendar'
        self.content_stack.setCurrentWidget(self.calendar_widget)
        # Yêu cầu Lịch tự cập nhật lại dữ liệu theo chế độ hiện tại (cá nhân hoặc nhóm)
        self.calendar_widget.switch_view_mode(self.current_view_mode, self.current_group_id)

    def _load_group_context(self, group_id, group_name):
        """
        Tải thông tin của một nhóm và cập nhật trạng thái của toàn bộ ứng dụng.
        """
        self.current_view_mode = 'group'
        self.current_group_id = group_id
        self.current_group_name = group_name
        self.group_title_label.setText(f"Nhóm: {self.current_group_name}")
        self.group_title_label.show()
        
        try:
            # Kiểm tra xem người dùng có phải là trưởng nhóm không
            leader_id = self.db_manager.get_group_leader(self.current_group_id)
            self.is_current_user_leader = (self.current_user_id == leader_id)
            
            # Cập nhật vai trò trên SidePanel
            role = "Quản trị viên" if self.is_current_user_leader else "Thành viên"
            self.side_panel.set_user_info(self.current_user_name, role)
            self.side_panel.update_view_mode(self.current_view_mode, self.is_current_user_leader)

            # Ra lệnh cho các widget con chuyển sang chế độ nhóm
            # (Home page sẽ tự lọc công việc cá nhân, không cần thay đổi)
            self.calendar_widget.switch_view_mode(mode='group', group_id=self.current_group_id)

        except Exception as error:
            QMessageBox.critical(self, "Lỗi CSDL", f"Không thể tải thông tin nhóm: {error}")
    
    # --- Các hàm xử lý cho nhóm ---

    def _show_member_list(self):
        """Hiển thị cửa sổ danh sách thành viên của nhóm hiện tại."""
        if self.current_group_id:
            dialog = MemberListDialog(self.current_group_id, self)
            dialog.exec_()
    
    def _show_add_member_dialog(self):
        """Hiển thị cửa sổ thêm thành viên (chỉ dành cho trưởng nhóm)."""
        if self.current_group_id and self.is_current_user_leader:
            dialog = AddMemberDialog(self.current_group_id, self)
            dialog.exec_()

    # --- Xử lý Đăng xuất và Đóng cửa sổ ---

    def _handle_logout_request(self):
        """Xử lý khi người dùng nhấn nút 'Sign Out'."""
        from login import LoginRegisterApp # Import tại đây để tránh lỗi import vòng tròn
        
        reply = QMessageBox.question(self, "Xác nhận Đăng xuất", 
                                     "Bạn có chắc chắn muốn đăng xuất không?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self._is_logging_out = True # Đặt cờ để bỏ qua xác nhận ở closeEvent
            self.close() # Đóng cửa sổ hiện tại
            
            # Mở lại cửa sổ đăng nhập
            self.login_window = LoginRegisterApp()
            self.login_window.show()

    def closeEvent(self, event):
        """
        Ghi đè sự kiện đóng cửa sổ (khi nhấn nút X).
        Hỏi người dùng xác nhận trước khi thoát hoàn toàn ứng dụng.
        """
        # Nếu đang trong quá trình đăng xuất, cho phép đóng ngay lập tức
        if self._is_logging_out:
            event.accept()
            return

        # Ngược lại, hỏi người dùng để xác nhận thoát ứng dụng
        reply = QMessageBox.question(self, "Xác nhận Thoát",
                                     "Bạn có chắc chắn muốn thoát khỏi ứng dụng không?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept() # Chấp nhận sự kiện đóng
        else:
            event.ignore() # Hủy bỏ sự kiện đóng