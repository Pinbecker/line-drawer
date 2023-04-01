import sys
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QComboBox, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QPushButton, QGraphicsLineItem, QGraphicsEllipseItem
from PyQt5.QtCore import Qt, QPointF, QRectF, QLineF, QEvent, QTimer
from PyQt5.QtGui import QPen, QPainter, QColor, QBrush, QPainterPathStroker


class CustomGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super(CustomGraphicsView, self).__init__(parent)
        SCALE_FACTOR = 1
        self.scale(SCALE_FACTOR, SCALE_FACTOR)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        scene_width = 2000
        scene_height = 2000
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, scene_width, scene_height)

        # Set the scene for the QGraphicsView
        self.setScene(self.scene)


    def wheelEvent(self, event):
        zoom_in_factor = 1.1
        zoom_out_factor = 1 / zoom_in_factor

        # Calculate the mouse position in the scene
        old_pos = self.mapToScene(event.pos())

        # Determine the zoom direction
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        # Apply the zoom
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setResizeAnchor(QGraphicsView.NoAnchor)
        self.scale(zoom_factor, zoom_factor)



        # Calculate the new position after zooming
        new_pos = self.mapToScene(event.pos())

        # Calculate the difference between the old and new positions
        delta = new_pos - old_pos

        # Move the view to maintain the mouse position on the same point
        self.translate(delta.x(), delta.y())





    def keyPressEvent(self, event):
        self.parent().on_key_press(event)    


class LineDrawer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):

        


        self.lines = []
        self.selected_line = None

        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('Line Drawer')
        self.setWindowTitle('Line Drawer')

        self.view = CustomGraphicsView(self)
        self.setCentralWidget(self.view)

        self.scene = QGraphicsScene(self)

        # Set the canvas size
        canvas_width = 100000
        canvas_height = 100000
        self.scene.setSceneRect(0, 0, canvas_width, canvas_height)

        self.view.setScene(self.scene)

        self.show()

        main_layout = QVBoxLayout()
        export_btn = QPushButton('Export to Excel', self)
        export_btn.clicked.connect(self.export_to_excel)
        main_layout.addWidget(export_btn)
        top_layout = QHBoxLayout()

        self.materials = QComboBox()
        self.materials.addItems(['Twin Bar', 'Roll Form'])
        top_layout.addWidget(self.materials)

        self.heights = QComboBox()
        self.heights.addItems(['1.2m', '2m', '2.4m', '3m', '3.6m', '4m', '4.5m', '5m', '6m'])
        top_layout.addWidget(self.heights)

        self.color_key = QLabel()
        self.color_key.setFixedWidth(200)
        top_layout.addWidget(self.color_key)

        # Create a toolbar
        toolbar = self.addToolBar("Toolbar")

        # Create button for switching between line and circle drawing
        switch_button = QPushButton("Switch to Circle Drawing")
        switch_button.clicked.connect(lambda: self.switch_drawing_mode("circle" if self.drawing_mode == "line" else "line"))
        toolbar.addWidget(switch_button)

        # Create a dropdown menu for selecting the circle type
        circle_type_dropdown = QComboBox()
        circle_type_dropdown.addItem("End")
        circle_type_dropdown.addItem("Corner")
        circle_type_dropdown.addItem("Two Way")
        circle_type_dropdown.currentTextChanged.connect(lambda text: setattr(self, 'circle_type', text))
        toolbar.addWidget(circle_type_dropdown)



        self.view = CustomGraphicsView()
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setFocusPolicy(Qt.StrongFocus)


        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.scene.setSceneRect(0, 0, 1000, 1000)  # Add this line

        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.view)

        self.pen = QPen(Qt.black, 1, Qt.SolidLine)

        # Connect the view's event handling functions
        self.view.setMouseTracking(True)
        self.view.viewport().installEventFilter(self)

        self.view.mouseMoveEvent = self.on_mouse_move
        self.view.mouseReleaseEvent = self.on_mouse_release
        self.view.keyPressEvent = self.on_key_press



        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(['Material', 'Height', 'Line Length (m)', 'Anchor Points'])
        main_layout.addWidget(self.table)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.view.setMouseTracking(True)
        self.view.mousePressEvent = self.on_mouse_press
        self.view.mouseMoveEvent = self.on_mouse_move
        self.view.mouseReleaseEvent = self.on_mouse_release

        self.start_point = None
        self.end_point = None
        self.temp_line = None
        self.drawing_line = False
        self.drawing_mode = "line"  # Add this line
        self.circle_type = None  # Add this line

        self.material_data = [
            {"name": "Twin Bar", "heights": ['1.2m', '2m', '2.4m', '3m', '3.6m', '4m', '4.5m', '5m', '6m'],
             "colors": [QColor(255, 0, 0), QColor(0, 255, 0), QColor(0, 0, 255), QColor(255, 255, 0), QColor(0, 255, 255), QColor(255, 0, 255), QColor(128, 0, 128), QColor(128, 128, 128), QColor(255, 165, 0)]},
            {"name": "Roll Form", "heights": ['1.2m', '2m', '2.4m', '3m', '3.6m', '4m', '4.5m', '5m', '6m'],
             "colors": [QColor(255, 99, 71), QColor(0, 128, 128), QColor(75, 0, 130), QColor(255, 192, 203), QColor(
            0, 100, 0), QColor(139, 0, 0), QColor(0, 0, 139), QColor(255, 140, 0), QColor(47, 79, 79)]},
        ]

        self.material_index = 0
        self.height_index = 0
        self.pen = QPen(self.material_data[self.material_index]["colors"][self.height_index], 5)
        self.materials.currentIndexChanged.connect(self.change_material)
        self.heights.currentIndexChanged.connect(self.change_height)

        self.length_text = None
        self.update_color_key()

    def switch_drawing_mode(self, mode):
        self.drawing_mode = mode

    def update_color_key(self):
        current_material = self.material_data[self.material_index]
        current_color = current_material["colors"][self.height_index]
        self.color_key.setText(f"{current_material['name']} {current_material['heights'][self.height_index]}")
        self.color_key.setStyleSheet(f"background-color: {current_color.name()}; color: {'black' if current_color.lightness() > 127 else 'white'}")

    def change_material(self, index):
        self.material_index = index
        self.pen.setColor(self.material_data[self.material_index]["colors"][self.height_index])
        self.update_color_key()

    def change_height(self, index):
        self.height_index = index
        self.pen.setColor(self.material_data[self.material_index]["colors"][self.height_index])
        self.update_color_key()

    def snap_to_angle(self, angle_degrees):
        angle_radians = np.deg2rad(angle_degrees)
        dx = self.end_point.x() - self.start_point.x()
        dy = self.end_point.y() - self.start_point.y()

        distance = np.sqrt(dx ** 2 + dy ** 2)
        snapped_distance = round(distance / 10) * 10
        snapped_x = distance * np.cos(angle_radians)
        snapped_y = distance * np.sin(angle_radians)

        return QPointF(self.start_point.x() + snapped_x, self.start_point.y() + snapped_y)

    def export_to_excel(self):
        headers = []
        data = []

        # Extract table headers
        for i in range(self.table.columnCount()):
            headers.append(self.table.horizontalHeaderItem(i).text())

        # Extract table data
        for i in range(self.table.rowCount()):
            row_data = []
            for j in range(self.table.columnCount()):
                item = self.table.item(i, j)
                if item is not None:
                    row_data.append(item.text())
                else:
                    row_data.append('')
            data.append(row_data)

        # Create a Pandas DataFrame
        df = pd.DataFrame(data, columns=headers)

        # Open a file dialog to choose the export file path and name
        file_path, _ = QFileDialog.getSaveFileName(self, 'Save File', '', 'Excel files (*.xlsx)')

        # Export the DataFrame to an Excel file
        if file_path:
            df.to_excel(file_path, index=False)


    def eventFilter(self, watched, event):
        if watched == self.view.viewport():
            if event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.RightButton:
                    print("Right-click detected")
                    pos = self.view.mapToScene(event.pos())
                    print(f"Right-click position: {pos}")
                    items_at_pos = self.scene.items(pos, Qt.IntersectsItemShape, Qt.AscendingOrder, self.view.transform())
                    print(f"Items at click position: {items_at_pos}")
                    for item in items_at_pos:
                        if isinstance(item, QGraphicsLineItem):
                            print(f"Line found: {item}")
                            if self.selected_line is not None:
                                self.deselect_line(self.selected_line)

                            line = next((line for line in self.lines if line['item'] == item), None)
                            if line is not None:
                                self.selected_line = line
                                self.select_line(line)
                            break
                    return True
                elif event.button() == Qt.LeftButton:
                    self.on_mouse_press(event)
                return True
            elif event.type() == QEvent.MouseMove:
                self.on_mouse_move(event)
                return True
            elif event.type() == QEvent.MouseButtonRelease:
                if event.button() == Qt.LeftButton:
                    self.on_mouse_release(event)
                return True
            elif event.type() == QEvent.KeyPress:
                self.on_key_press(event)
                return True
        return super().eventFilter(watched, event)



    def on_mouse_press(self, event):
        pos = self.view.mapToScene(event.pos())
        print(f"Click position: {pos}")

        if self.drawing_mode == "circle":
            if event.button() == Qt.LeftButton:
                # Create and add the circle based on the selected type and position
                circle_radius = 10
                circle_rect = QRectF(pos.x() - circle_radius, pos.y() - circle_radius, 2 * circle_radius, 2 * circle_radius)
                circle_pen = QPen(Qt.black, 1)
                circle_brush = QBrush(Qt.black)
                circle = self.scene.addEllipse(circle_rect, circle_pen, circle_brush)
                # Add any additional customization based on self.circle_type here
        else:

            item = self.view.itemAt(event.pos())

            # Deselect the line if any other item or empty space is clicked
            if self.selected_line is not None and (item is None or item != self.selected_line['item']):
                self.deselect_line(self.selected_line)
                self.selected_line = None

            if not self.drawing_line:
                if event.button() == Qt.LeftButton:
                    anchor_radius = 10
                    snap_to_existing = False
                    for i in range(self.table.rowCount()):
                        start_anchor = self.table.item(i, 0).data(Qt.UserRole)
                        end_anchor = self.table.item(i, 1).data(Qt.UserRole)
                        for anchor in [start_anchor, end_anchor]:
                            if anchor is not None:
                                anchor_rect = QRectF(anchor.x() - anchor_radius, anchor.y() - anchor_radius, 2 * anchor_radius, 2 * anchor_radius)
                                if anchor_rect.contains(pos):
                                    pos = anchor
                                    snap_to_existing = True
                                    break
                        if snap_to_existing:
                            break

                    if not snap_to_existing:
                        self.start_point = pos
                        anchor_rect = QRectF(self.start_point.x() - anchor_radius, self.start_point.y() - anchor_radius, 2 * anchor_radius, 2 * anchor_radius)
                        anchor_pen = QPen(Qt.black, 1)
                        anchor_brush = QBrush(Qt.black)
                        anchor = self.scene.addEllipse(anchor_rect, anchor_pen, anchor_brush)

                    else:
                        self.start_point = pos

                    self.drawing_line = True

            else:
                self.on_mouse_release(event)


    def remove_anchor_point(self, point):
        items_at_point = self.scene.items(point)
        for item in items_at_point:
            if isinstance(item, QGraphicsEllipseItem):
                self.scene.removeItem(item)
                break

    def on_key_press(self, event):
        if event.key() == Qt.Key_Delete:
            # Check if a line is selected, and delete it if it is
            for line in self.lines:
                if line['item'].pen().color() == Qt.black:
                    self.delete_line(line)
                    self.remove_anchor_point(line['start_anchor'])
                    self.remove_anchor_point(line['end_anchor'])
                    break
        





    def on_mouse_move(self, event):
        if self.drawing_line:
            if self.start_point is not None:
                if self.temp_line:
                    self.scene.removeItem(self.temp_line)
                if self.length_text:
                    self.scene.removeItem(self.length_text)

                self.end_point = self.view.mapToScene(event.pos())

                anchor_radius = 10
                for i in range(self.table.rowCount()):

                    start_anchor = self.table.item(i, 0).data(Qt.UserRole)
                    end_anchor = self.table.item(i, 1).data(Qt.UserRole)
                    for anchor in [start_anchor, end_anchor]:
                        if anchor is not None:
                            anchor_rect = QRectF(anchor.x() - anchor_radius, anchor.y() - anchor_radius, 2 * anchor_radius, 2 * anchor_radius)
                            if anchor_rect.contains(self.end_point):
                                self.end_point = anchor
                                print("Hovering over anchor at:", self.end_point)
                                break


                # Snap to 90 and 45-degree angles
                angles_to_snap = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130, 135, 140, 145, 150, 155, 160, 165, 170, 175, 180, 185, 190, 195, 200, 205, 210, 215, 220, 225, 230, 235, 240, 245, 250, 255, 260, 265, 270, 275, 280, 285, 290, 295, 300, 305, 310, 315, 320, 325, 330, 335, 340, 345, 350, 355]
                min_angle_diff = float('inf')
                snapped_point = self.end_point
                for angle in angles_to_snap:
                    temp_point = self.snap_to_angle(angle)
                    angle_diff = np.arctan2(self.end_point.y() - self.start_point.y(), self.end_point.x() - self.start_point.x()) - np.arctan2(temp_point.y() - self.start_point.y(), temp_point.x() - self.start_point.x())
                    angle_diff = np.abs(np.rad2deg(angle_diff))
                    if angle_diff < 15 and angle_diff < min_angle_diff:
                        min_angle_diff = angle_diff
                        snapped_point = temp_point
                self.end_point = snapped_point

                self.temp_line = self.scene.addLine(self.start_point.x(), self.start_point.y(), self.end_point.x(), self.end_point.y(), self.pen)

                line_length = round(np.sqrt((self.start_point.x() - self.end_point.x())**2 + (self.start_point.y() - self.end_point.y())**2) / 1) / 20
                self.length_text = self.scene.addText("{:.1f}m".format(line_length))
                mid_point = QPointF((self.start_point.x() + self.end_point.x()) / 2, (self.start_point.y() + self.end_point.y()) / 2)
                text_width = self.length_text.boundingRect().width()
                self.length_text.setPos(mid_point.x() - text_width / 2, mid_point.y())





    def on_mouse_release(self, event):
        if self.start_point is not None and self.end_point is not None and self.drawing_line:
            if event.button() == Qt.LeftButton:
                self.scene.removeItem(self.temp_line)
                line = self.scene.addLine(self.start_point.x(), self.start_point.y(), self.end_point.x(), self.end_point.y(), self.pen)
                self.scene.removeItem(self.length_text)

                line_length = round(np.sqrt((self.start_point.x() - self.end_point.x())**2 + (self.start_point.y() - self.end_point.y())**2) / 1) / 20

                # Create a new QGraphicsTextItem with the length text
                final_length_text = self.scene.addText("{:.1f}m".format(line_length))
                
                # Set the position of the new QGraphicsTextItem to the midpoint of the line
                mid_point = QPointF((self.start_point.x() + self.end_point.x()) / 2, (self.start_point.y() + self.end_point.y()) / 2)
                text_width = final_length_text.boundingRect().width()
                final_length_text.setPos(mid_point.x() - text_width / 2, mid_point.y())

                anchor_radius = 10
                self.found_anchor = False

                for i in range(self.table.rowCount()):
                    anchor = self.table.item(i, 1).data(Qt.UserRole)
                    if anchor is not None:
                        anchor_rect = QRectF(anchor.x() - anchor_radius, anchor.y() - anchor_radius, 2 * anchor_radius, 2 * anchor_radius)
                        if anchor_rect.contains(self.end_point):
                            self.found_anchor = True
                            i = i
                            break

                if not self.found_anchor:
                    # Create an anchor point at the start of the line
                    start_anchor_rect = QRectF(self.start_point.x() - anchor_radius, self.start_point.y() - anchor_radius, 2 * anchor_radius, 2 * anchor_radius)
                    anchor_pen = QPen(Qt.black, 1)
                    anchor_brush = QBrush(Qt.black)
                    start_anchor_item = self.scene.addEllipse(start_anchor_rect, anchor_pen, anchor_brush)

                    # Create an anchor point at the end of the line
                    end_anchor_rect = QRectF(self.end_point.x() - anchor_radius, self.end_point.y() - anchor_radius, 2 * anchor_radius, 2 * anchor_radius)
                    end_anchor_item = self.scene.addEllipse(end_anchor_rect, anchor_pen, anchor_brush)
                else:
                    start_anchor_item = self.table.item(i, 0).data(Qt.UserRole)
                    end_anchor_item = self.table.item(i, 1).data(Qt.UserRole)


                self.add_line_to_table(line, line_length, self.start_point, self.end_point, start_anchor_item, end_anchor_item, final_length_text)


                self.total_anchor_points = self.table.rowCount() * 2
                print("Total number of anchor points:", self.total_anchor_points)

                #self.lines.append({'item': line, 'start_anchor': self.start_point, 'end_anchor': self.end_point})
                print(f"Added line: {line}, Total lines: {len(self.lines)}")


                self.start_point = None
                self.end_point = None
                self.temp_line = None
                self.length_text = None
                self.drawing_line = False  # Add this line


    def select_line(self, line):
        # Highlight the selected line by changing its pen color and width
        pen = line['item'].pen()
        pen.setColor(Qt.black)
        pen.setWidth(3)
        line['item'].setPen(pen)

    def deselect_line(self, line):
        # Restore the original pen color and width of the deselected line
        pen = line['item'].pen()
        pen.setColor(line['original_color'])
        pen.setWidth(line['original_width'])
        line['item'].setPen(pen)

    def delete_line(self, line):
        # Remove the line from the scene and from the list
        self.scene.removeItem(line['item'])
        self.lines.remove(line)

        # Remove the start and end anchor items if they are not being used by other lines
        if not self.is_anchor_used(line['start_anchor']) and isinstance(line['start_anchor_item'], QGraphicsEllipseItem):
            self.scene.removeItem(line['start_anchor_item'])

        if not self.is_anchor_used(line['end_anchor']) and isinstance(line['end_anchor_item'], QGraphicsEllipseItem):
            self.scene.removeItem(line['end_anchor_item'])

        # Remove the length text
        self.scene.removeItem(line['length_text'])

        # Remove the QTableWidgetItem objects with the anchor points
        for row in range(self.table.rowCount()):
            start_anchor = self.table.item(row, 0).data(Qt.UserRole)
            end_anchor = self.table.item(row, 1).data(Qt.UserRole)

            if start_anchor == line['start_anchor'] or end_anchor == line['end_anchor']:
                self.table.removeRow(row)
                break






    def is_anchor_used(self, anchor):
        usage_count = 0
        for line in self.lines:
            if line['start_anchor'] == anchor or line['end_anchor'] == anchor:
                usage_count += 1
        return usage_count > 1




    def add_line_to_table(self, line, length, start_anchor, end_anchor, start_anchor_item, end_anchor_item, length_text_item):
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)

        material_item = QTableWidgetItem(f"{self.material_data[self.material_index]['name']}")
        material_item.setData(Qt.UserRole, start_anchor)
        self.table.setItem(row_count, 0, material_item)

        height_item = QTableWidgetItem(f"{self.material_data[self.material_index]['heights'][self.height_index]}")
        height_item.setData(Qt.UserRole, end_anchor)
        self.table.setItem(row_count, 1, height_item)

        length_item = QTableWidgetItem(f"{length:.1f}m")
        self.table.setItem(row_count, 2, length_item)

        if row_count == 0:
            anchor_points = QTableWidgetItem("1")  # The first line has 1 anchor point
        elif not self.found_anchor:
            anchor_points = QTableWidgetItem("1")  # Only add 1 anchor point when it's created
        else:
            anchor_points = QTableWidgetItem("0")  # No anchor points are created if the end point connects to an existing anchor
        self.table.setItem(row_count, 3, anchor_points)


        # Add the line item to the list with its length and anchors
        self.lines.append({ 
            'item': line,
            'original_color': line.pen().color(),
            'original_width': line.pen().width(),
            'length': length, 
            'start_anchor': start_anchor, 
            'end_anchor': end_anchor,
            'start_anchor_item': start_anchor_item,
            'end_anchor_item': end_anchor_item,
            'length_text': length_text_item
        })
        print(f"Added line, Total lines: {len(self.lines)}")



if __name__ == '__main__':
    app = QApplication(sys.argv)
    line_drawer = LineDrawer()
    line_drawer.show()
    sys.exit(app.exec_())
