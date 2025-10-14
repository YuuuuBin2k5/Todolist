"""
    Thanh điều hướng bên trái
    - Chứa thông tin người dùng
    - Các nút chuyển đổi giữa khu vực cá nhân và khu vực nhóm
    - Các nút điều hướng nội dung: Trang chủ và Lịch
    - Nút thoát trở về màn hình đăng nhập
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy, QFileDialog, QHBoxLayout
from PyQt5.QtGui import QPainter, QBrush, QColor, QPixmap, QPainterPath, QPen
from config import COLOR_GRAY, COLOR_PRIMARY_BLUE, COLOR_SECONDARY_BLUE, COLOR_BORDER, COLOR_HOVER, COLOR_WHITE
from PyQt5.QtCore import Qt, QRectF, pyqtSignal

class ClickableLabel(QLabel):
    """QLabel có thể bấm được, phát tín hiệu `clicked` khi nhấn chuột."""
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked.emit()

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
    # Tín hiệu để thông báo cho parent rằng đường dẫn avatar đã thay đổi (persistence được xử lý bởi parent)
    avatar_changed = pyqtSignal(str)


    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedWidth(300)
        self.setObjectName("SidePanel")

        # Áp dụng chủ đề xanh bóng cho thanh bên
        self.setStyleSheet(f"""
            QFrame#SidePanel {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {COLOR_PRIMARY_BLUE}, stop:1 {COLOR_SECONDARY_BLUE});
                border-right: 1px solid {COLOR_BORDER};
            }}

            QLabel {{
                color: {COLOR_WHITE};
            }}

            QLabel#InfoValueLabel {{
                color: {COLOR_WHITE};
                font-weight: 800;
                font-size: 15px;
                letter-spacing: 0.2px;
                margin-top: 4px;
            }}

            QLabel#InfoTitleLabel {{
                color: rgba(255,255,255,0.85);
                font-weight: 600;
                font-size: 11px;
                margin-bottom: 2px;
                text-transform: uppercase;
                letter-spacing: 0.8px;
            }}

            QLabel#RolePill {{
                background: rgba(255,255,255,0.12);
                color: {COLOR_WHITE};
                border-radius: 12px;
                padding: 6px 12px;
                font-weight: 700;
                min-width: 80px;
                qproperty-alignment: 'AlignCenter';
            }}

            QPushButton {{
                background: rgba(255,255,255,0.08);
                color: {COLOR_WHITE};
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 10px;
                padding: 10px 12px;
                text-align: center;
                font-weight: 600;
            }}

            QPushButton:hover {{
                background: rgba(255,255,255,0.12);
                border: 1px solid rgba(255,255,255,0.18);
            }}

            QPushButton:disabled {{
                background: rgba(0,0,0,0.12);
                color: rgba(255,255,255,0.6);
            }}

            QPushButton#ExitButton {{
                background: {COLOR_WHITE};
                color: {COLOR_PRIMARY_BLUE};
                border-radius: 12px;
                border: 2px solid rgba(0,0,0,0.06);
            }}

            QPushButton#ExitButton:hover {{
                background: {COLOR_HOVER};
                color: {COLOR_WHITE};
            }}

            QPushButton#HomeButton, QPushButton#CalendarButton, QPushButton#StatisticsButton {{
                background: rgba(255,255,255,0.06);
                border-radius: 8px;
                padding-left: 18px;
            }}

            /* Avatar circle styling (kept as pixmap but with nicer border) */
            QLabel {{
                border-radius: 60px;
            }}
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(15)

        # Avatar (có thể click)
        self.avatar = ClickableLabel()
        self.avatar.setFixedSize(120, 120)
        self.avatar.setAlignment(Qt.AlignCenter)
        self.create_circular_avatar()
        self.layout.addWidget(self.avatar, 0, Qt.AlignCenter)
        # kết nối hành vi có thể click
        self.avatar.clicked.connect(self._on_avatar_clicked)
        self.layout.addSpacing(15)

        # Hàng thông tin: tên + vai trò
        name_row = QHBoxLayout()
        name_title_label = QLabel("TÊN")
        name_title_label.setObjectName("InfoTitleLabel")
        self.name_value_label = QLabel("Đang tải...")
        self.name_value_label.setObjectName("InfoValueLabel")
        self.name_value_label.setAlignment(Qt.AlignCenter)
        self.name_value_label.setMinimumWidth(140)
        name_row.addWidget(name_title_label, 0)
        name_row.addWidget(self.name_value_label, 1)
        self.layout.addLayout(name_row)
        self.layout.addSpacing(6)

        role_row = QHBoxLayout()
        role_title_label = QLabel("VAI TRÒ")
        role_title_label.setObjectName("InfoTitleLabel")
        self.role_value_label = QLabel("Đang tải...")
        # đặt tên kiểu pill để làm nổi bật trực quan
        self.role_value_label.setObjectName("RolePill")
        self.role_value_label.setAlignment(Qt.AlignCenter)
        self.role_value_label.setMinimumWidth(140)
        role_row.addWidget(role_title_label, 0)
        role_row.addWidget(self.role_value_label, 1)
        self.layout.addLayout(role_row)
        self.layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Nút chuyển đổi khu vực
        self.personal_btn = QPushButton("KHU VỰC CÁ NHÂN")
        self.group_btn = QPushButton("KHU VỰC NHÓM")

        self.layout.addWidget(self.personal_btn)
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

        # Cải thiện kích thước/sự hiện diện của nút: làm cho nút rộng hơn và nổi bật hơn
        btns = [
            self.personal_btn, self.group_btn,
            self.member_list_btn, self.add_member_btn,
            self.home_button, self.calendar_button,
            self.statistics_button, self.exit_button
        ]
        for b in btns:
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            b.setMinimumHeight(44)
            b.setCursor(Qt.PointingHandCursor)
            # đảm bảo objectName tồn tại để định kiểu mục tiêu nếu thiếu
            if not b.objectName():
                b.setObjectName(b.text().replace(' ', '') + "Btn")

        

        # self.exit_btn = QPushButton("EXIT")
        # self.exit_btn.setObjectName("ExitButton")
        # self.layout.addWidget(self.exit_btn)
        
    def set_user_info(self, user_name, role):
        """
            Thiết lập thông tin tên và vai trò của người dùng.
        """
        self.name_value_label.setText(user_name)
        self.role_value_label.setText(role)

    # Signal to notify parent that avatar path changed (persistence handled by parent)
    from PyQt5.QtCore import pyqtSignal
    avatar_changed = pyqtSignal(str)

    def _on_avatar_clicked(self):
        """Open a file dialog to choose an image and set it as avatar."""
        path, _ = QFileDialog.getOpenFileName(self, "Chọn ảnh đại diện", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            self.set_avatar_from_path(path)
            # phát tín hiệu để parent có thể lưu đường dẫn nếu cần
            try:
                self.avatar_changed.emit(path)
            except Exception:
                pass

    def set_avatar_from_path(self, path: str):
        """Load image from path, mask to circle and set on avatar label."""
        src = QPixmap(path)
        if src.isNull():
            return

        size = self.avatar.size()
        # Tạo pixmap đích với nền trong suốt
        target = QPixmap(size)
        target.fill(Qt.transparent)

        painter = QPainter(target)
        painter.setRenderHint(QPainter.Antialiasing)

        # Cắt theo đường tròn
        rect = QRectF(0.0, 0.0, float(size.width()), float(size.height()))
        path = QPainterPath()
        path.addEllipse(rect)
        painter.setClipPath(path)

        # Vẽ hình ảnh nguồn được scale và căn giữa để phủ kín vòng tròn
        src_scaled = src.scaled(size.width(), size.height(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        # căn giữa pixmap đã scale
        sx = (src_scaled.width() - size.width()) // 2
        sy = (src_scaled.height() - size.height()) // 2
        painter.drawPixmap(-sx, -sy, src_scaled)

        # Tùy chọn: vẽ một viền tinh tế quanh vòng tròn
        pen = QPen(QColor(255, 255, 255, 200))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(rect.adjusted(1.0, 1.0, -1.0, -1.0))

        painter.end()

        self.avatar.setPixmap(target)
        
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
        
  