"""
    Cột bên trái
    - Chứa thông tin người dùng
    - Các nút thao tác 
        + Chuyển đổi giữa Todo Cá nhân và Nhóm
        + Nút Exit thoát trở về Login
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QPainter, QBrush, QColor, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal

class SidePanel(QFrame):
    """
        Thanh điều hướng bên trái, chứa thông tin người dùng và các nút chức năng chính.
    """
    personal_area_requested = pyqtSignal()
    group_area_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # Đặt kiểu khung để có viền
        self.setFrameShape(QFrame.StyledPanel)
        # Cố định chiều rộng của thanh bên
        self.setFixedWidth(300)
        self.setObjectName("SidePanel")

        # Layout chính của thanh bên, theo chiều dọc
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15) # Đặt lề
        self.layout.setSpacing(15) # Đặt khoảng cách giữa các widget con

        # --- Avatar (Ảnh đại diện) ---
        self.avatar = QLabel()
        self.avatar.setFixedSize(120, 120) # Kích thước cố định
        self.avatar.setAlignment(Qt.AlignCenter)
        self.create_circular_avatar() # Gọi hàm vẽ avatar hình tròn
        # Thêm avatar vào layout, căn giữa theo chiều ngang
        self.layout.addWidget(self.avatar, 0, Qt.AlignCenter)
        self.layout.addSpacing(15)

        # --- Thông tin Tên và Vai trò ---
        name_title_label = QLabel("TÊN")
        self.name_value_label = QLabel("Đang tải...")
        
        role_title_label = QLabel("VAI TRÒ")
        self.role_value_label = QLabel("Đang tải...")


        # Đặt tên object cho các label giá trị để style bằng CSS
        self.name_value_label.setObjectName("InfoValueLabel")
        self.role_value_label.setObjectName("InfoValueLabel")
        
        # Thêm các label vào layout
        self.layout.addWidget(name_title_label)
        self.layout.addWidget(self.name_value_label)
        self.layout.addSpacing(10)
        self.layout.addWidget(role_title_label)
        self.layout.addWidget(self.role_value_label)
        
        # Thêm một khoảng trống co giãn để đẩy các nút chức năng xuống dưới
        self.layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # --- Các nút điều hướng chức năng ---
        self.personal_btn = QPushButton("KHU VỰC CÁ NHÂN")
        self.group_btn = QPushButton("KHU VỰC NHÓM")

        self.personal_btn.clicked.connect(self.personal_area_requested.emit)
        self.group_btn.clicked.connect(self.group_area_requested.emit)
        
        self.layout.addWidget(self.personal_btn)
        self.layout.addWidget(self.group_btn)
        
        # Thêm một bộ đệm co giãn, nó sẽ chiếm hết không gian thừa
        # và đẩy nút Exit xuống dưới cùng.
        self.layout.addStretch(1)

        # --- Nút Exit ---
        self.exit_btn = QPushButton("EXIT")
        self.exit_btn.setObjectName("ExitButton") # Đặt tên riêng để style khác biệt
        self.layout.addWidget(self.exit_btn)

    def set_user_info(self, user_name, user_role):
        self.name_value_label.setText(user_name)
        self.role_value_label.setText(user_role)

    def create_circular_avatar(self):
        """
            Tạo một ảnh QPixmap hình tròn để làm avatar placeholder.
        """
        # Tạo một pixmap trống với kích thước bằng kích thước của label avatar
        pixmap = QPixmap(self.avatar.size())
        pixmap.fill(Qt.transparent) # Làm cho nền trong suốt
        
        # Sử dụng QPainter để vẽ lên pixmap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing) # Bật khử răng cưa cho hình tròn mịn
        
        # Vẽ hình tròn
        painter.setBrush(QBrush(QColor("#cccccc"))) # Đặt màu nền cho hình tròn
        painter.setPen(Qt.NoPen) # Không vẽ viền
        painter.drawEllipse(0, 0, self.avatar.width(), self.avatar.height())
        painter.end() # Kết thúc vẽ
        
        # Đặt pixmap đã vẽ xong làm nội dung cho label avatar
        self.avatar.setPixmap(pixmap)
    #Làm mờ nút
    def update_view_buttons(self, active_view):
        """
            Cập nhật giao diện của các nút điều hướng để làm nổi bật khu vực đang hoạt động.
            active_view: 'personal' hoặc 'group'
        """
        # Định nghĩa kiểu CSS cho trạng thái bình thường và trạng thái "mờ" (đang hoạt động)
        normal_style = """
            background-color: #ffffff; 
            border: 1px solid #c0c0c0; 
            border-radius: 15px; 
            padding: 10px; 
            font-weight: bold;
        """
        
        active_style = """
            background-color: #e0e0e0; /* Màu nền xám hơn */
            color: #888888; /* Màu chữ xám hơn */
            border: 1px solid #b0b0b0; 
            border-radius: 15px; 
            padding: 10px; 
            font-weight: bold;
        """
        
        if active_view == 'personal':
            self.personal_btn.setStyleSheet(active_style)
            self.group_btn.setStyleSheet(normal_style)
        elif active_view == 'group':
            self.personal_btn.setStyleSheet(normal_style)
            self.group_btn.setStyleSheet(active_style)