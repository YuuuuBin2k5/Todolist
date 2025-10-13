"""
    Thanh điều hướng bên trái
    - Chứa thông tin người dùng
    - Các nút chuyển đổi giữa khu vực cá nhân và khu vực nhóm
    - Các nút điều hướng nội dung: Trang chủ và Lịch
    - Nút thoát trở về màn hình đăng nhập
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QPainter, QBrush, QColor, QPixmap
from config import COLOR_GRAY
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

    member_list_requested = pyqtSignal()
    add_member_requested = pyqtSignal()

    # Tín hiệu phát ra khi yêu cầu xem thống kê
    statistics_requested = pyqtSignal()


    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedWidth(300)
        self.setObjectName("SidePanel")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(15)

        self.avatar = QLabel()
        self.avatar.setFixedSize(120, 120)
        # self.layout.addWidget(self.avatar, alignment=Qt.AlignCenter)
        # self._create_circular_avatar()
        
        # # --- Thông tin người dùng ---
        # self.user_name_label = QLabel("Tên người dùng")
        # self.user_name_label.setObjectName("InfoValueLabel")
        # self.user_name_label.setAlignment(Qt.AlignCenter)
        # self.layout.addWidget(self.user_name_label)
        
        # self.role_label = QLabel("Vai trò")
        # self.role_label.setObjectName("InfoValueLabel")
        # self.role_label.setAlignment(Qt.AlignCenter)
        # self.layout.addWidget(self.role_label)

        # # --- Nút chuyển đổi khu vực ---
        # self.personal_btn = QPushButton("Khu vực Cá nhân")
        # self.personal_btn.setObjectName("PersonalButton")
        self.avatar.setAlignment(Qt.AlignCenter)
        self.create_circular_avatar()
        self.layout.addWidget(self.avatar, 0, Qt.AlignCenter)
        self.layout.addSpacing(15)

        name_title_label = QLabel("TÊN")
        self.name_value_label = QLabel("Đang tải...")
        role_title_label = QLabel("VAI TRÒ")
        self.role_value_label = QLabel("Đang tải...")
        self.name_value_label.setObjectName("InfoValueLabel")
        self.role_value_label.setObjectName("InfoValueLabel")
        self.layout.addWidget(name_title_label)
        self.layout.addWidget(self.name_value_label)
        self.layout.addSpacing(10)
        self.layout.addWidget(role_title_label)
        self.layout.addWidget(self.role_value_label)
        self.layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.personal_btn = QPushButton("KHU VỰC CÁ NHÂN")
        self.group_btn = QPushButton("KHU VỰC NHÓM")

        self.layout.addWidget(self.personal_btn)

        # self.group_btn = QPushButton("Khu vực Nhóm")
        # self.group_btn.setObjectName("GroupButton")
        self.layout.addWidget(self.group_btn)

        self.member_list_btn = QPushButton("Danh sách thành viên")
        self.add_member_btn = QPushButton("Thêm thành viên")
        self.layout.addWidget(self.member_list_btn)
        self.layout.addWidget(self.add_member_btn)
        
        
        self.member_list_btn.hide()
        self.add_member_btn.hide()
        
        self.layout.addStretch(1)
        

        # Thêm một khoảng phân cách
        self.layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # --- Nút điều hướng nội dung ---
        self.home_button = QPushButton("Trang chủ")
        self.home_button.setObjectName("HomeButton")
        self.layout.addWidget(self.home_button)
        
        self.calendar_button = QPushButton("Lịch")
        self.calendar_button.setObjectName("CalendarButton")
        self.layout.addWidget(self.calendar_button)

        #Vi
        self.statistics_button = QPushButton("Thống kê")
        self.statistics_button.setObjectName("StatisticsButton") # Đặt tên để có thể style bằng CSS
        self.layout.addWidget(self.statistics_button)

        # --- Khoảng trống giãn nở để đẩy nút Exit xuống dưới ---
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(spacer)

        # --- Nút Exit ---
        self.exit_button = QPushButton("Sign Out")
        self.exit_button.setObjectName("ExitButton")
        self.layout.addWidget(self.exit_button)

        # --- Kết nối tín hiệu ---
        self.personal_btn.clicked.connect(self.personal_area_requested.emit)
        self.group_btn.clicked.connect(self.group_area_requested.emit)
        self.home_button.clicked.connect(self.home_requested.emit)
        self.calendar_button.clicked.connect(self.calendar_requested.emit)
        self.exit_button.clicked.connect(self.exit_requested.emit)
        self.member_list_btn.clicked.connect(self.member_list_requested.emit)
        self.add_member_btn.clicked.connect(self.add_member_requested.emit)
        self.statistics_button.clicked.connect(self.statistics_requested.emit)
        
        self.update_view('personal')

        

        # self.exit_btn = QPushButton("EXIT")
        # self.exit_btn.setObjectName("ExitButton")
        # self.layout.addWidget(self.exit_btn)
        
    def set_user_info(self, user_name, role):
        """
            Thiết lập thông tin tên và vai trò của người dùng.
        """
        self.name_value_label.setText(user_name)
        self.role_value_label.setText(role)
        
    def _create_circular_avatar(self):
        """
            Vẽ một hình tròn rỗng để làm avatar.
        """
        pixmap = QPixmap(self.avatar.size())
        pixmap.fill(Qt.transparent)
        

    def update_view(self, view_mode, is_leader=False):
        """Chỉ cần enable/disable các nút, CSS sẽ tự xử lý giao diện."""
        if view_mode == 'personal':
            self.personal_btn.setEnabled(False)
            self.group_btn.setEnabled(True)
            self.member_list_btn.hide()
            self.add_member_btn.hide()
        elif view_mode == 'group':
            self.personal_btn.setEnabled(True)
            self.group_btn.setEnabled(False)
            self.member_list_btn.show()
            self.add_member_btn.setVisible(is_leader)

    def create_circular_avatar(self):
        pixmap = QPixmap(self.avatar.size())
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(COLOR_GRAY)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, self.avatar.width(), self.avatar.height())
        painter.end()
        self.avatar.setPixmap(pixmap)
        
  