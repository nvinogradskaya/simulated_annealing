import sys
from PyQt6.QtWidgets import QApplication, QGraphicsSimpleTextItem, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QGridLayout, QMessageBox, QGraphicsScene, QGraphicsView
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QFont
from PyQt6.QtCore import Qt
import math
import random

class GraphWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.view)

        self.points = {}
        self.edges = []

    def set_graph(self, adjacency_matrix, num_points, path):
        self.points = {}
        self.edges = []

        self.num_points = num_points
        self.path = path


        center_x = self.view.width() / 2
        center_y = self.view.height() / 2
        radius = min(center_x, center_y) * 0.8

        angle = 360 / self.num_points
        for i in range(self.num_points):
            x = center_x + radius * math.cos(math.radians(angle * i))
            y = center_y + radius * math.sin(math.radians(angle * i))
            self.points[i] = (x, y)


        for i in range(self.num_points):
            for j in range(self.num_points):
                if adjacency_matrix[i][j] != 0:
                    self.edges.append((i, j))

        self.draw_graph()

    def draw_graph(self):
        self.scene.clear()


        pen = QPen(QColor("black"), 1)
        for start, end in self.edges:
            start_x, start_y = self.points[start]
            end_x, end_y = self.points[end]
            self.scene.addLine(start_x, start_y, end_x, end_y, pen)


        point_radius = 8
        brush = QBrush(QColor("black"), Qt.BrushStyle.SolidPattern)
        for i, (x, y) in self.points.items():
            self.scene.addEllipse(x - point_radius, y - point_radius, 2 * point_radius, 2 * point_radius, pen, brush)


        label_font = QFont("Arial", 18)
        for i, (x, y) in self.points.items():
            label = QGraphicsSimpleTextItem(chr(ord('A') + i))
            label.setFont(label_font)
            label.setPos(x + point_radius, y + point_radius)
            label.setZValue(-1)
            self.scene.addItem(label)


        if self.path:
            path_pen = QPen(QColor("red"), 2)
            for i in range(len(self.path) - 1):
                start_x, start_y = self.points[self.path[i]]
                end_x, end_y = self.points[self.path[i + 1]]
                self.scene.addLine(start_x, start_y, end_x, end_y, path_pen)


            start_x, start_y = self.points[self.path[-1]]
            end_x, end_y = self.points[self.path[0]]
            self.scene.addLine(start_x, start_y, end_x, end_y, path_pen)

        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)


class TSP(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Решение задачи коммивояжера")
        self.setGeometry(700, 700, 1100, 900)

        self.size_label = QLabel("Количество вершин графа:")
        self.size_input = QLineEdit()
        self.generate_button = QPushButton("Ввод матрицы")
        self.generate_button.clicked.connect(self.generate_matrix)

        self.matrix_layout = QGridLayout()
        self.solve_button = QPushButton("Старт")
        self.solve_button.clicked.connect(self.start)

        self.result_label = QLabel()

        self.graph_widget = GraphWidget()

        layout = QVBoxLayout()
        layout.addWidget(self.size_label)
        layout.addWidget(self.size_input)
        layout.addWidget(self.generate_button)
        layout.addLayout(self.matrix_layout)
        layout.addWidget(self.solve_button)
        layout.addWidget(self.result_label)
        layout.addWidget(self.graph_widget)

        self.setLayout(layout)

    def generate_matrix(self):
        self.clear_matrix()
        num_points = int(self.size_input.text())

        for row in range(num_points):
            for col in range(num_points):
                cell_label = QLabel(f"Из пункта {chr(row + 65)} в пункт {chr(col + 65)}:")
                cell_input = QLineEdit()
                self.matrix_layout.addWidget(cell_label, row, col * 2)
                self.matrix_layout.addWidget(cell_input, row, col * 2 + 1)

    def clear_matrix(self):
        for i in reversed(range(self.matrix_layout.count())):
            item = self.matrix_layout.itemAt(i)
            if item:
                item.widget().setParent(None)

    def start(self):
        num_points = int(self.size_input.text())
        adjacency_matrix = self.get_adj_matrix(num_points)
        try:
            graph = self.parse_adj_matrix(adjacency_matrix, num_points)
            path, length = self.simulated_annealing(graph)
            if path:
                result_text = "Длина кратчайшего гамильтонова цикла: " + str(length)
                result_text += "\nКратчайший гамильтонов цикл: "
                for i in range(len(path)):
                    point_name = chr(ord('A') + path[i])
                    result_text += point_name
                    if i < len(path) - 1:
                        result_text += " -> "
                result_text += " --> " + chr(ord('A') + path[0])
            else:
                result_text = "Гамильтонова цикла не существует"

        except ValueError:
            result_text = "Ошибка при вводе матрицы смежности"
            path = []

        self.result_label.setText(result_text)
        self.graph_widget.set_graph(graph, num_points, path)

    def get_adj_matrix(self, num_points):
        adj_matrix = ""
        for row in range(num_points):
            for col in range(num_points):
                cell_input = self.matrix_layout.itemAtPosition(row, col * 2 + 1).widget()
                adj_matrix += cell_input.text().strip() + " "
            adj_matrix += "\n"
        return adj_matrix.strip()

    def parse_adj_matrix(self, matrix_string, num_points):
        rows = matrix_string.split("\n")
        graph = []
        for row in rows:
            graph.append([int(cell.strip()) for cell in row.strip().split()][:num_points])
        return graph

    def simulated_annealing(self, graph):
        num_points = len(graph)
        min_length = float('inf')
        min_path = None

        for start in range(num_points):
            temp = 1000.0
            cool_rate = 0.003

            current_path = list(range(start, num_points)) + list(range(0, start))
            random.shuffle(current_path)

            while temp > 1:
                new_path = current_path[:]
                p1 = random.randint(0, num_points - 1)
                p2 = random.randint(0, num_points - 1)
                new_path[p1], new_path[p2] = new_path[p2], new_path[p1]

                current_length = self.calculate_path_length(graph, current_path)
                new_length = self.calculate_path_length(graph, new_path)

                if new_length < current_length or math.exp((current_length - new_length) / temp) > random.random():
                    current_path = new_path

                temp *= 1 - cool_rate

            current_length = self.calculate_path_length(graph, current_path)
            if current_length < min_length:
                min_length = current_length
                min_path = current_path

        return min_path, min_length

    def calculate_path_length(self, graph, path):
        length = 0
        num_points = len(graph)
        for i in range(num_points):
            length += graph[path[i]][path[(i + 1) % num_points]]
        return length


if __name__ == "__main__":
    app = QApplication([])
    solver = TSP()
    solver.show()
    sys.exit(app.exec())
