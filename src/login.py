# -*- coding: utf-8 -*-
import sys
import os
import sqlite3
import random
import smtplib
import ssl
from email.message import EmailMessage
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QStackedWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QDialog)
from PyQt5.QtCore import Qt, QPropertyAnimation, QPoint
# [THAY ĐỔI] Thêm QFont vào đây
from PyQt5.QtGui import QPixmap, QFont 
from config import *
from MainMenu.main_window import MainWindow
from Managers.database_manager import Database

# ==========================================================================================
# LỚP DIALOG MỚI CHO CHỨC NĂNG QUÊN MẬT KHẨU
# ==========================================================================================
class ForgotPasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quên Mật Khẩu")
        self.setFixedSize(400, 300)
        self.setObjectName("ForgotPasswordDialog")
        
        # Biến để lưu trữ thông tin qua các bước
        self.email = ""
        self.verification_code = ""

        self.stacked_widget = QStackedWidget(self)
        
        self.email_page = QWidget()
        self.code_page = QWidget()
        self.reset_page = QWidget()

        self.setup_email_page()
        self.setup_code_page()
        self.setup_reset_page()

        self.stacked_widget.addWidget(self.email_page)
        self.stacked_widget.addWidget(self.code_page)
        self.stacked_widget.addWidget(self.reset_page)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.stacked_widget)
        self.setStyleSheet(f"""
            QDialog#ForgotPasswordDialog {{ background-color: #f9f9f9; }}
            QLabel {{ font-size: 14px; }}
            QLineEdit {{ padding: 8px; border: 1px solid #ccc; border-radius: 4px; }}
            QPushButton {{ 
                padding: 10px; background-color: {BTN_PRIMARY_BG}; color: {COLOR_WHITE}; 
                border: none; border-radius: 4px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {BTN_PRIMARY_BG_HOVER}; }}
        """)

    # --- Bước 1: Trang nhập Email ---
    def setup_email_page(self):
        layout = QVBoxLayout(self.email_page)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel("Nhập email của bạn")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        
        self.email_input = QLineEdit(placeholderText="Email")
        send_code_btn = QPushButton("Gửi mã xác thực")
        send_code_btn.clicked.connect(self.handle_send_code)
        
        layout.addWidget(title)
        layout.addWidget(self.email_input)
        layout.addWidget(send_code_btn)

    # --- Bước 2: Trang nhập mã xác thực ---
    def setup_code_page(self):
        layout = QVBoxLayout(self.code_page)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Nhập mã xác thực")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        
        self.code_input = QLineEdit(placeholderText="Mã 6 chữ số")
        verify_btn = QPushButton("Xác nhận")
        verify_btn.clicked.connect(self.handle_verify_code)
        
        layout.addWidget(title)
        layout.addWidget(self.code_input)
        layout.addWidget(verify_btn)

    # --- Bước 3: Trang đặt lại mật khẩu ---
    def setup_reset_page(self):
        layout = QVBoxLayout(self.reset_page)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Tạo mật khẩu mới")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        
        self.new_password_input = QLineEdit(placeholderText="Mật khẩu mới")
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input = QLineEdit(placeholderText="Xác nhận mật khẩu mới")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        
        reset_btn = QPushButton("Đặt lại mật khẩu")
        reset_btn.clicked.connect(self.handle_reset_password)
        
        layout.addWidget(title)
        layout.addWidget(self.new_password_input)
        layout.addWidget(self.confirm_password_input)
        layout.addWidget(reset_btn)

    # --- Logic xử lý ---
    def handle_send_code(self):
        self.email = self.email_input.text()
        if not self.email:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập email.")
            return
        # Kiểm tra email có tồn tại trong CSDL không (dùng Database helper)
        try:
            db = Database()
            user = db.get_user_by_email(self.email)
            if not user:
                QMessageBox.warning(self, "Lỗi", "Email không tồn tại trong hệ thống.")
                return
        except Exception as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Không thể kiểm tra email: {e}")
            return

        # Tạo mã và gửi email
        self.verification_code = str(random.randint(100000, 999999))
        print(f"Generated code for {self.email}: {self.verification_code}") # In ra để debug
        
        if self.send_verification_email(self.email, self.verification_code):
            QMessageBox.information(self, "Thành công", f"Mã xác thực đã được gửi tới {self.email}.")
            self.stacked_widget.setCurrentIndex(1) # Chuyển sang trang nhập mã

    def handle_verify_code(self):
        entered_code = self.code_input.text()
        if entered_code == self.verification_code:
            self.stacked_widget.setCurrentIndex(2) # Chuyển sang trang đổi mật khẩu
        else:
            QMessageBox.warning(self, "Lỗi", "Mã xác thực không chính xác.")

    def handle_reset_password(self):
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not new_password or not confirm_password:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ mật khẩu.")
            return
        
        if new_password != confirm_password:
            QMessageBox.warning(self, "Lỗi", "Mật khẩu xác nhận không khớp.")
            return
            
        # Cập nhật mật khẩu trong CSDL
        try:
            db = Database()
            db.update_user_password_by_email(new_password, self.email)
            QMessageBox.information(self, "Thành công", "Mật khẩu đã được đặt lại thành công. Vui lòng đăng nhập.")
            self.accept() # Đóng dialog
        except Exception as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Không thể cập nhật mật khẩu: {e}")

    # ======================================================================================
    # HÀM CHỜ: BẠN CẦN ĐIỀN THÔNG TIN GỬI EMAIL CỦA BẠN VÀO ĐÂY
    # ======================================================================================
    def send_verification_email(self, recipient_email, code):
        """
        Đây là nơi bạn sẽ triển khai logic gửi email.
        Sử dụng smtplib và mật khẩu ứng dụng của bạn.
        Trả về True nếu gửi thành công, False nếu thất bại.
        """
        # THAY THẾ CÁC THÔNG TIN NÀY BẰNG THÔNG TIN CỦA BẠN
        email_sender = 'your_email@gmail.com'  # Email của bạn
        email_password = 'your_app_password'     # Mật khẩu ứng dụng 16 ký tự

        if email_sender == 'your_email@gmail.com' or email_password == 'your_app_password':
            print("!!! VUI LÒNG CẤU HÌNH EMAIL VÀ MẬT KHẨU ỨNG DỤNG TRONG HÀM send_verification_email !!!")
            # Giả lập gửi email thành công để test giao diện
            return True 
        
        # --- Logic gửi email thật ---
        email_receiver = recipient_email
        subject = 'Mã xác thực đặt lại mật khẩu của bạn'
        body = f"Mã xác thực của bạn là: {code}"

        em = EmailMessage()
        em['From'] = email_sender
        em['To'] = email_receiver
        em['Subject'] = subject
        em.set_content(body)

        context = ssl.create_default_context()

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                smtp.login(email_sender, email_password)
                smtp.sendmail(email_sender, email_receiver, em.as_string())
            return True
        except Exception as e:
            print(f"Lỗi gửi email: {e}")
            QMessageBox.critical(self, "Lỗi", "Không thể gửi email xác thực.")
            return False

# ==========================================================================================
# CẬP NHẬT LỚP LoginRegisterApp
# ==========================================================================================
class LoginRegisterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self._allow_close = False
        self.setWindowTitle("Đăng Nhập/Đăng Ký")
        self.setGeometry(100, 100, CONTAINER_WIDTH, CONTAINER_HEIGHT)
        self.setFixedSize(CONTAINER_WIDTH, CONTAINER_HEIGHT)
        self.main_container = QWidget()
        self.main_container.setStyleSheet(f"background-color: {COLOR_WHITE}; border-radius: 30px; box-shadow: 0 5px 15px {COLOR_SHADOW};")
        self.setCentralWidget(self.main_container)
        self.base_layout = QHBoxLayout(self.main_container)
        self.base_layout.setSpacing(0)
        self.base_layout.setContentsMargins(0, 0, 0, 0)
        self.stacked_forms = QStackedWidget()
        self.stacked_forms.setFixedSize(FORM_WIDTH, CONTAINER_HEIGHT)
        self.stacked_forms.setStyleSheet("background-color: transparent;")
        self.sign_in_form, self.email_input_signin, self.password_input_signin = self.create_form("Đăng Nhập", "hoặc sử dụng mật khẩu email của bạn")
        self.sign_up_form, self.name_input_signup, self.email_input_signup, self.password_input_signup = self.create_form("Đăng Ký", "hoặc sử dụng email của bạn để đăng ký")
        self.stacked_forms.addWidget(self.sign_in_form)
        self.stacked_forms.addWidget(self.sign_up_form)
        self.base_layout.addWidget(self.stacked_forms)
        self.toggle_panel = QWidget()
        self.toggle_panel.setFixedSize(TOGGLE_PANEL_WIDTH, CONTAINER_HEIGHT)
        self.toggle_panel.setStyleSheet(f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLOR_PRIMARY_BLUE}, stop:1 {COLOR_SECONDARY_BLUE}); color: white; border-top-left-radius: 150px; border-bottom-left-radius: 100px; border-top-right-radius: 10px; border-bottom-right-radius: 10px; z-index: 1000;")
        self.toggle_layout = QStackedWidget(self.toggle_panel)
        self.toggle_layout.setFixedSize(TOGGLE_PANEL_WIDTH, CONTAINER_HEIGHT)
        self.toggle_layout.setStyleSheet("background-color: transparent;")
        self.toggle_left = self.create_toggle_panel("Chào mừng trở lại!", "Hãy nhập thông tin cá nhân của bạn để sử dụng tất cả các tính năng của trang web nhé", "Đăng Nhập")
        self.toggle_layout.addWidget(self.toggle_left)
        self.toggle_right = self.create_toggle_panel("Chào bạn!", "Hãy đăng ký với thông tin cá nhân của bạn để sử dụng tất cả các tính năng của trang web", "Đăng Ký")
        self.toggle_layout.addWidget(self.toggle_right)
        self.base_layout.addWidget(self.toggle_panel)
        self.base_layout.setAlignment(self.toggle_panel, Qt.AlignRight)
        self.stacked_forms.setCurrentWidget(self.sign_in_form)
        self.toggle_layout.setCurrentWidget(self.toggle_right)
        self.toggle_left.findChild(QPushButton).clicked.connect(self.show_sign_in)
        self.toggle_right.findChild(QPushButton).clicked.connect(self.show_sign_up)
        self.animation_form = QPropertyAnimation(self.stacked_forms, b"pos")
        self.animation_form.setDuration(ANIMATION_DURATION_MS)
        self.animation_toggle = QPropertyAnimation(self.toggle_panel, b"pos")
        self.animation_toggle.setDuration(ANIMATION_DURATION_MS)

    def closeEvent(self, event):
        if not self._allow_close:
            reply = QMessageBox.question(self, "Xác nhận Thoát", "Bạn có chắc chắn muốn thoát không?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def create_form(self, title, subtitle):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        layout.setContentsMargins(30, 0, 30, 0)
        layout.setAlignment(Qt.AlignCenter)
        title_label = QLabel(f"<h1>{title}</h1>")
        title_label.setStyleSheet("font-size: 24px; font-weight: 700; color: #333;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        social_layout = QHBoxLayout()
        social_layout.setAlignment(Qt.AlignCenter)
        social_layout.setSpacing(10)
        social_icons = ["assets/images/google_icon.png", "assets/images/facebook_icon.png", "assets/images/instagram_icon.png", "assets/images/github_icon.png"]
        for icon_path in social_icons:
            icon_label = QLabel()
            icon_pixmap = QPixmap(icon_path)
            icon_pixmap_scaled = icon_pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap_scaled)
            icon_label.setFixedSize(40, 40)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet(f"border: 1px solid {COLOR_GRAY}; border-radius: 20px;")
            social_layout.addWidget(icon_label)
        layout.addLayout(social_layout)
        subtitle_label = QLabel(f"<p>{subtitle}</p>")
        subtitle_label.setStyleSheet(f"font-size: 14px; color: {TEXT_MUTED};")
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)
        email_input = QLineEdit(placeholderText="Email")
        email_input.setStyleSheet(f"padding: 10px; height: 40px; border: none; background-color: {INPUT_BG}; border-radius: 8px;")
        layout.addWidget(email_input)
        name_input, password_input = None, None
        if "Đăng Ký" in title:
            name_input = QLineEdit(placeholderText="Name")
            name_input.setStyleSheet(f"padding: 10px; height: 40px; border: none; background-color: {INPUT_BG}; border-radius: 8px;")
            layout.addWidget(name_input)
        password_input = QLineEdit(placeholderText="Password")
        password_input.setStyleSheet(f"padding: 10px; height: 40px; border: none; background-color: {INPUT_BG}; border-radius: 8px;")
        password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(password_input)
        if "Đăng Nhập" in title:
            # [THAY ĐỔI] Biến label thành button có thể nhấn
            forgot_password_btn = QPushButton("Quên mật khẩu?")
            forgot_password_btn.setStyleSheet(f"font-size: 12px; margin-top: 10px; margin-bottom: 20px; border: none; color: {TEXT_MUTED};")
            forgot_password_btn.setCursor(Qt.PointingHandCursor)
            forgot_password_btn.clicked.connect(self.show_forgot_password_dialog)
            layout.addWidget(forgot_password_btn, alignment=Qt.AlignCenter)
        button = QPushButton(title)
        button.setFixedSize(120, 30)
        button.setStyleSheet(f"background-color: {COLOR_SECONDARY_BLUE}; color: {COLOR_WHITE}; border: none; font-weight: 600; text-transform: uppercase; border-radius: 8px;")
        if "Đăng Nhập" in title:
            button.clicked.connect(self.handle_sign_in)
            email_input.returnPressed.connect(button.click)
            password_input.returnPressed.connect(button.click)
        else:
            button.clicked.connect(self.handle_sign_up)
            if name_input: name_input.returnPressed.connect(button.click)
            email_input.returnPressed.connect(button.click)
            password_input.returnPressed.connect(button.click)
        layout.addWidget(button, alignment=Qt.AlignCenter)
        if "Đăng Ký" in title:
            return widget, name_input, email_input, password_input
        else:
            return widget, email_input, password_input

    def create_toggle_panel(self, title, subtitle, button_text):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        title_label = QLabel(f"<h1>{title}</h1>")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: 700;")
        layout.addWidget(title_label)
        subtitle_label = QLabel(f"<p>{subtitle}</p>")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet("font-size: 14px; padding: 0 20px;")
        layout.addWidget(subtitle_label)
        button = QPushButton(button_text)
        button.setFixedSize(120, 30)
        button.setStyleSheet(f"background-color: transparent; border: 1px solid {COLOR_WHITE}; color: {COLOR_WHITE}; font-weight: 600; text-transform: uppercase; border-radius: 8px;")
        layout.addWidget(button, alignment=Qt.AlignCenter)
        return widget

    def show_forgot_password_dialog(self):
        dialog = ForgotPasswordDialog(self)
        dialog.exec_()

    def show_sign_up(self):
        self.stacked_forms.setCurrentWidget(self.sign_up_form)
        self.toggle_layout.setCurrentWidget(self.toggle_left)
        self.toggle_panel.setStyleSheet(f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLOR_PRIMARY_BLUE_PURPLE}, stop:1 {COLOR_SECONDARY_BLUE_PURPLE}); color: white; border-top-right-radius: 150px; border-bottom-right-radius: 100px; border-top-left-radius: 10px; border-bottom-left-radius: 10px; z-index: 1000;")
        self.animate_transition(is_sign_up=True)

    def show_sign_in(self):
        self.stacked_forms.setCurrentWidget(self.sign_in_form)
        self.toggle_layout.setCurrentWidget(self.toggle_right)
        self.toggle_panel.setStyleSheet(f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLOR_PRIMARY_BLUE}, stop:1 {COLOR_SECONDARY_BLUE}); color: white; border-top-left-radius: 150px; border-bottom-left-radius: 100px; border-top-right-radius: 10px; border-bottom-right-radius: 10px; z-index: 1000;")
        self.animate_transition(is_sign_up=False)

    def handle_sign_in(self):
        email = self.email_input_signin.text()
        password = self.password_input_signin.text()
        
        try:
            # Use Database helper for authentication
            db = Database()
            user = db.get_login_user(email, password)
            if user:
                user_id, user_name = user[0], user[1]
                self._allow_close = True
                self.close()
                self.main_window = MainWindow(user_id, user_name)
                self.main_window.show()
            else:
                QMessageBox.warning(self, "Lỗi", "Email hoặc mật khẩu không đúng.")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Lỗi khi kết nối hoặc truy vấn CSDL: {e}")

    def handle_sign_up(self):
        name = self.name_input_signup.text()
        email = self.email_input_signup.text()
        password = self.password_input_signup.text()
        if not name or not email or not password:
            QMessageBox.warning(self, "Lỗi", "Vui lòng điền đầy đủ tất cả các trường.")
            return
        try:
            db = Database()
            created_id = db.create_user(name, password, email)
            # create_user trả về user_id (int) khi thành công, hoặc None khi lỗi
            if created_id is not None:
                QMessageBox.information(self, "Thành công", "Đăng ký thành công! Vui lòng đăng nhập.")
                self.show_sign_in()
            else:
                QMessageBox.warning(self, "Lỗi", "Email này đã tồn tại hoặc không thể tạo tài khoản.")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Lỗi khi kết nối hoặc truy vấn CSDL: {e}")

    def animate_transition(self, is_sign_up):
        start_pos_forms, end_pos_forms = self.stacked_forms.pos(), QPoint(FORM_WIDTH if is_sign_up else 0, 0)
        start_pos_toggle, end_pos_toggle = self.toggle_panel.pos(), QPoint(0 if is_sign_up else FORM_WIDTH, 0)
        self.animation_form.setStartValue(start_pos_forms)
        self.animation_form.setEndValue(end_pos_forms)
        self.animation_toggle.setStartValue(start_pos_toggle)
        self.animation_toggle.setEndValue(end_pos_toggle)
        self.animation_form.start()
        self.animation_toggle.start()