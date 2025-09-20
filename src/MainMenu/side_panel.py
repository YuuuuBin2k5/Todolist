"""
    Thanh điều hướng bên trái
    - Chứa thông tin người dùng
    - Các nút chuyển đổi giữa khu vực cá nhân và khu vực nhóm
    - Các nút điều hướng nội dung: Trang chủ và Lịch
    - Nút thoát trở về màn hình đăng nhập
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QPainter, QBrush, QColor, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal

class SidePanel(QFrame):
    """
        Thanh điều hướng bên trái, chứa thông tin người dùng và các nút chức năng chính.
    """
    # Tín hiệu phát ra khi yêu cầu chuyển đổi khu vực
    personal_area_requested = pyqtSignal()
    group_area_requested = pyqtSignal()
    
    # Tín hiệu phát ra khi yêu cầu chuyển đổi nội dung
    home_requested = pyqtSignal()
    calendar_requested = pyqtSignal()
    
    # Tín hiệu thoát
    exit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedWidth(300)
        self.setObjectName("SidePanel")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(15)

        # --- Avatar (Ảnh đại diện) ---
        self.avatar = QLabel()
        self.avatar.setFixedSize(120, 120)
        self.layout.addWidget(self.avatar, alignment=Qt.AlignCenter)
        self._create_circular_avatar()
        
        # --- Thông tin người dùng ---
        self.user_name_label = QLabel("Tên người dùng")
        self.user_name_label.setObjectName("InfoValueLabel")
        self.user_name_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.user_name_label)
        
        self.role_label = QLabel("Vai trò")
        self.role_label.setObjectName("InfoValueLabel")
        self.role_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.role_label)

        # --- Nút chuyển đổi khu vực ---
        self.personal_btn = QPushButton("Khu vực Cá nhân")
        self.personal_btn.setObjectName("PersonalButton")
        self.layout.addWidget(self.personal_btn)

        self.group_btn = QPushButton("Khu vực Nhóm")
        self.group_btn.setObjectName("GroupButton")
        self.layout.addWidget(self.group_btn)
        
        # Thêm một khoảng phân cách
        self.layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # --- Nút điều hướng nội dung ---
        self.home_button = QPushButton("Trang chủ")
        self.home_button.setObjectName("HomeButton")
        self.layout.addWidget(self.home_button)
        
        self.calendar_button = QPushButton("Lịch")
        self.calendar_button.setObjectName("CalendarButton")
        self.layout.addWidget(self.calendar_button)

        # --- Khoảng trống giãn nở để đẩy nút Exit xuống dưới ---
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(spacer)

        # --- Nút Exit ---
        self.exit_button = QPushButton("Thoát")
        self.exit_button.setObjectName("ExitButton")
        self.layout.addWidget(self.exit_button)

        # --- Kết nối tín hiệu ---
        self.personal_btn.clicked.connect(self.personal_area_requested.emit)
        self.group_btn.clicked.connect(self.group_area_requested.emit)
        self.home_button.clicked.connect(self.home_requested.emit)
        self.calendar_button.clicked.connect(self.calendar_requested.emit)
        self.exit_button.clicked.connect(self.exit_requested.emit)
        
        self.update_view_buttons(area='personal', content='home')
        
    def set_user_info(self, user_name, role):
        """
            Thiết lập thông tin tên và vai trò của người dùng.
        """
        self.user_name_label.setText(user_name)
        self.role_label.setText(role)
        
    def _create_circular_avatar(self):
        """
            Vẽ một hình tròn rỗng để làm avatar.
        """
        pixmap = QPixmap(self.avatar.size())
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor("#cccccc")))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, self.avatar.width(), self.avatar.height())
        painter.end()
        
        self.avatar.setPixmap(pixmap)
        
    def update_view_buttons(self, area, content=None):
        """
            Cập nhật giao diện của các nút điều hướng để làm nổi bật khu vực/nội dung đang hoạt động.
            - area: 'personal' hoặc 'group'
            - content: 'home' hoặc 'calendar'
        """
        normal_style = """
            background-color: #ffffff; 
            border: 1px solid #c0c0c0; 
            border-radius: 15px; 
            padding: 10px; 
            font-weight: bold;
        """
        
        active_style = """
            background-color: #e0e0e0;
            color: #888888;
            border: 1px solid #b0b0b0; 
            border-radius: 15px; 
            padding: 10px; 
            font-weight: bold;
        """
        
        # Cập nhật style cho các nút khu vực
        self.personal_btn.setStyleSheet(active_style if area == 'personal' else normal_style)
        self.group_btn.setStyleSheet(active_style if area == 'group' else normal_style)
        
        # Cập nhật style cho các nút nội dung
        if content:
            self.home_button.setStyleSheet(active_style if content == 'home' else normal_style)
            self.calendar_button.setStyleSheet(active_style if content == 'calendar' else normal_style)
