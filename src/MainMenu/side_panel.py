# --- Nhập các thư viện và module cần thiết ---
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QPainter, QBrush, QColor, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal

# ==============================================================================
# LỚP 1: SidePanel - Thanh điều hướng bên trái
# ==============================================================================
class SidePanel(QFrame):
    """
    Thanh điều hướng bên trái của ứng dụng.
    Chứa thông tin người dùng và các nút điều hướng chính.
    Nó giao tiếp với MainWindow thông qua cơ chế signals-slots.
    """
    # --- Định nghĩa các tín hiệu (signals) ---
    # Các tín hiệu này sẽ được "phát ra" khi người dùng nhấn nút tương ứng.
    # MainWindow sẽ "lắng nghe" các tín hiệu này để thực hiện hành động.
    
    # Tín hiệu chuyển đổi khu vực làm việc
    personal_area_requested = pyqtSignal()
    group_area_requested = pyqtSignal()
    
    # Tín hiệu chuyển đổi màn hình nội dung
    home_requested = pyqtSignal()
    calendar_requested = pyqtSignal()
    
    # Tín hiệu cho các chức năng của nhóm
    member_list_requested = pyqtSignal()
    add_member_requested = pyqtSignal()
    
    # Tín hiệu đăng xuất
    exit_requested = pyqtSignal()

    def __init__(self, parent=None):
        """
        Khởi tạo và xây dựng giao diện cho SidePanel.
        """
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedWidth(300)  # Cố định chiều rộng của thanh bên
        self.setObjectName("SidePanel")  # Đặt tên để áp dụng CSS

        # Layout chính, sắp xếp các widget theo chiều dọc
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)

        # --- Khu vực thông tin người dùng ---
        self._setup_user_info_widgets()

        # Thêm một khoảng trống để tách biệt khu vực thông tin và các nút
        self.main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # --- Khu vực các nút bấm ---
        self._setup_buttons()
        
        # --- Kết nối tín hiệu của các nút ---
        self._connect_button_signals()

        # Cài đặt trạng thái ban đầu cho các nút
        self.update_view_mode('personal', is_leader=False)

    def _setup_user_info_widgets(self):
        """Tạo các widget hiển thị thông tin người dùng (avatar, tên, vai trò)."""
        # Widget hiển thị avatar (hình tròn màu xám)
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(120, 120)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self._create_circular_avatar()
        self.main_layout.addWidget(self.avatar_label, 0, Qt.AlignCenter)
        self.main_layout.addSpacing(15)

        # Các nhãn hiển thị tên và vai trò
        name_title_label = QLabel("TÊN")
        self.name_value_label = QLabel("Đang tải...")
        self.name_value_label.setObjectName("InfoValueLabel") # Đặt tên để CSS in đậm
        
        role_title_label = QLabel("VAI TRÒ")
        self.role_value_label = QLabel("Đang tải...")
        self.role_value_label.setObjectName("InfoValueLabel")

        self.main_layout.addWidget(name_title_label)
        self.main_layout.addWidget(self.name_value_label)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(role_title_label)
        self.main_layout.addWidget(self.role_value_label)

    def _setup_buttons(self):
        """Tạo tất cả các nút bấm cho thanh bên."""
        # Nút chuyển đổi khu vực
        self.personal_area_button = QPushButton("KHU VỰC CÁ NHÂN")
        self.group_area_button = QPushButton("KHU VỰC NHÓM")
        self.main_layout.addWidget(self.personal_area_button)
        self.main_layout.addWidget(self.group_area_button)

        # Các nút chức năng dành riêng cho nhóm (ban đầu bị ẩn)
        self.member_list_button = QPushButton("Danh sách thành viên")
        self.add_member_button = QPushButton("Thêm thành viên")
        self.main_layout.addWidget(self.member_list_button)
        self.main_layout.addWidget(self.add_member_button)
        self.member_list_button.hide()
        self.add_member_button.hide()

        # Thêm một khoảng trống co giãn để đẩy các nút điều hướng xuống dưới
        self.main_layout.addStretch(1)

        # Nút điều hướng nội dung
        self.home_button = QPushButton("Trang chủ")
        self.calendar_button = QPushButton("Lịch")
        self.main_layout.addWidget(self.home_button)
        self.main_layout.addWidget(self.calendar_button)

        # Thêm một khoảng trống co giãn lớn để đẩy nút "Sign Out" xuống đáy
        self.main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Nút đăng xuất
        self.exit_button = QPushButton("Sign Out")
        self.exit_button.setObjectName("ExitButton") # Đặt tên để CSS có màu đỏ
        self.main_layout.addWidget(self.exit_button)

    def _connect_button_signals(self):
        """Kết nối sự kiện `clicked` của các nút tới việc phát ra tín hiệu tương ứng."""
        self.personal_area_button.clicked.connect(self.personal_area_requested.emit)
        self.group_area_button.clicked.connect(self.group_area_requested.emit)
        self.home_button.clicked.connect(self.home_requested.emit)
        self.calendar_button.clicked.connect(self.calendar_requested.emit)
        self.member_list_button.clicked.connect(self.member_list_requested.emit)
        self.add_member_button.clicked.connect(self.add_member_requested.emit)
        self.exit_button.clicked.connect(self.exit_requested.emit)

    def set_user_info(self, name, role_name):
        """
        Cập nhật thông tin tên và vai trò của người dùng trên giao diện.
        Hàm này được gọi từ MainWindow.
        """
        self.name_value_label.setText(name)
        self.role_value_label.setText(role_name)
        
    def _create_circular_avatar(self):
        """
        Sử dụng QPainter để vẽ một hình tròn màu xám và đặt nó làm avatar.
        """
        # Tạo một pixmap (bề mặt vẽ) trong suốt với kích thước của avatar
        pixmap = QPixmap(self.avatar_label.size())
        pixmap.fill(Qt.transparent)
        
        # Tạo một đối tượng QPainter để vẽ lên pixmap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing) # Bật chế độ khử răng cưa cho hình tròn mịn hơn
        painter.setBrush(QBrush(QColor("#cccccc"))) # Đặt màu tô là màu xám
        painter.setPen(Qt.NoPen) # Không vẽ viền
        
        # Vẽ hình elip (vì chiều rộng và cao bằng nhau nên sẽ là hình tròn)
        painter.drawEllipse(0, 0, self.avatar_label.width(), self.avatar_label.height())
        painter.end() # Kết thúc quá trình vẽ
        
        # Đặt pixmap đã vẽ làm hình ảnh cho avatar_label
        self.avatar_label.setPixmap(pixmap)

    def update_view_mode(self, view_mode, is_leader=False):
        """
        Cập nhật trạng thái của các nút bấm dựa trên chế độ xem hiện tại (cá nhân/nhóm).
        
        Args:
            view_mode (str): 'personal' hoặc 'group'.
            is_leader (bool): True nếu người dùng là trưởng nhóm của nhóm đang xem.
        """
        if view_mode == 'personal':
            # Vô hiệu hóa nút "Cá nhân" để cho biết nó đang được chọn
            self.personal_area_button.setEnabled(False) 
            self.group_area_button.setEnabled(True)
            # Ẩn các nút chỉ dành cho nhóm
            self.member_list_button.hide()
            self.add_member_button.hide()
        elif view_mode == 'group':
            self.personal_area_button.setEnabled(True)
            # Vô hiệu hóa nút "Nhóm" để cho biết nó đang được chọn
            self.group_area_button.setEnabled(False) 
            # Hiển thị các nút của nhóm
            self.member_list_button.show()
            # Nút "Thêm thành viên" chỉ hiển thị nếu người dùng là trưởng nhóm
            self.add_member_button.setVisible(is_leader)