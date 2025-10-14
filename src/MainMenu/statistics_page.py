from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea
from PyQt5.QtCore import Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class StatItemWidget(QFrame):
    def __init__(self, stat_data, parent=None):
        super().__init__(parent)
        self.setObjectName("StatItemWidget")
        self.setFrameShape(QFrame.StyledPanel)
        
        main_layout = QHBoxLayout(self)
        
        info_layout = QVBoxLayout()
        name_label = QLabel(stat_data.get('name', 'N/A'))
        name_label.setObjectName("StatNameLabel")
        
        # Lấy dữ liệu từ 3 key mới
        completed = stat_data.get('completed', 0)
        overdue = stat_data.get('overdue', 0)
        upcoming = stat_data.get('upcoming', 0)
        
        # 'in_progress' cũ bây giờ được chia thành 'overdue' và 'upcoming'
        total = completed + overdue + upcoming
        percent = (completed / total * 100) if total > 0 else 0
        
        # Cập nhật lại chuỗi hiển thị thông tin
        stats_text = (
            f"Tổng số Task: {total}\n"
            f"Hoàn thành: {completed} ({percent:.1f}%)\n"
            f"Quá hạn: {overdue}\n"
            f"Chưa tới hạn: {upcoming}"
        )
        stats_label = QLabel(stats_text)
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(stats_label)
        info_layout.addStretch()

        figure = Figure(figsize=(5, 5)) 
        canvas = FigureCanvas(figure)
        
        self._draw_pie_chart(figure, canvas, stat_data)

        main_layout.addLayout(info_layout, 1)
        main_layout.addWidget(canvas, 2) 

    def _draw_pie_chart(self, figure, canvas, stats_data):
        figure.clear()
        ax = figure.add_subplot(111)
        
        # Cập nhật labels, sizes, và colors cho 3 thành phần
        labels = ['Hoàn thành', 'Quá hạn', 'Chưa tới hạn']
        sizes = [
            stats_data.get('completed', 0), 
            stats_data.get('overdue', 0), 
            stats_data.get('upcoming', 0)
        ]
        # Xanh lá (hoàn thành), Đỏ (quá hạn), Vàng (sắp tới)
        colors = ['#2ecc71', '#e74c3c', '#f1c40f']
        
        if sum(sizes) > 0:
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90,
                   textprops={'fontsize': 11})
        else:
            ax.text(0.5, 0.5, 'Không có công việc', ha='center', va='center', color='gray')
            ax.axis('off')
            
        ax.axis('equal')
        
        figure.tight_layout()
        canvas.draw()

class StatisticsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("StatisticsPage")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        
        title = QLabel("Tổng quan tiến độ công việc")
        title.setObjectName("PageTitleLabel")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # [SỬA] Gán scroll_area vào self để có thể truy cập từ các hàm khác
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True) 
        main_layout.addWidget(self.scroll_area)
        
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        # [SỬA] Đặt khoảng cách giữa các biểu đồ là 0 để chúng liền kề nhau
        self.scroll_layout.setSpacing(0)
        self.scroll_area.setWidget(scroll_content)

    # [THÊM] Ghi đè sự kiện resizeEvent
    def resizeEvent(self, event):
        """Được gọi mỗi khi kích thước của StatisticsPage thay đổi."""
        super().resizeEvent(event)
        # Gọi hàm cập nhật chiều cao của các widget con
        self._update_children_height()

    # [THÊM] Hàm cập nhật chiều cao cho các widget con
    def _update_children_height(self):
        """
        Tính toán chiều cao của khu vực hiển thị và áp dụng cho mỗi StatItemWidget.
        """
        # Lấy chiều cao của khu vực có thể nhìn thấy bên trong QScrollArea
        # Trừ đi một chút để tránh thanh cuộn ngang không cần thiết
        visible_height = self.scroll_area.viewport().height() - 2
        
        if visible_height < 100: # Ngăn không cho widget quá nhỏ
            return

        # Lặp qua tất cả các widget trong layout và đặt chiều cao cố định cho chúng
        for i in range(self.scroll_layout.count()):
            widget = self.scroll_layout.itemAt(i).widget()
            if isinstance(widget, StatItemWidget):
                widget.setFixedHeight(visible_height)

    def update_all_stats(self, personal_stats, group_stats_list):
        # Xóa các widget cũ
        for i in reversed(range(self.scroll_layout.count())): 
            widget_to_remove = self.scroll_layout.itemAt(i).widget()
            if widget_to_remove:
                widget_to_remove.setParent(None)

        # Thêm widget cá nhân
        personal_stats['name'] = "Cá nhân"
        personal_widget = StatItemWidget(personal_stats)
        self.scroll_layout.addWidget(personal_widget)
        
        # Thêm các widget của nhóm
        if not group_stats_list:
            no_group_label = QLabel("Bạn chưa tham gia nhóm nào có công việc.")
            no_group_label.setAlignment(Qt.AlignCenter)
            self.scroll_layout.addWidget(no_group_label)
        else:
            for group_data in group_stats_list:
                group_data['name'] = group_data.pop('group_name')
                group_widget = StatItemWidget(group_data)
                self.scroll_layout.addWidget(group_widget)

        # [THÊM] Cập nhật chiều cao của các widget ngay sau khi thêm chúng vào
        # Dùng singleShot để đảm bảo giao diện đã được cập nhật trước khi lấy kích thước
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, self._update_children_height)