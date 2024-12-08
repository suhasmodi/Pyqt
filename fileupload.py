from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QListWidget,
    QListWidgetItem,
    QCheckBox,
    QPushButton,
    QFileDialog,
    QHBoxLayout,
)
from PyQt5.QtGui import QColor
from qgis.core import QgsRasterLayer, QgsVectorLayer, QgsProject
from qgis.gui import QgsMapCanvas
import sys


class MapViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Integrated QGIS Viewer")
        self.setGeometry(100, 100, 1000, 600)

        # Create the main layout
        main_layout = QHBoxLayout()

        # Map Canvas
        self.canvas = QgsMapCanvas()
        self.canvas.setCanvasColor(QColor("white"))
        self.canvas.enableAntiAliasing(True)

        # Layers Panel
        self.layers_panel = QListWidget()
        self.layers_panel.setFixedWidth(150)
        

        # Buttons for adding, removing, and managing layers
        add_layer_btn = QPushButton("Add Layer")
        add_layer_btn.clicked.connect(self.add_layer)
        

        remove_layer_btn = QPushButton("Remove Layer")
        remove_layer_btn.clicked.connect(self.remove_layer)

        zoom_layer_btn = QPushButton("Zoom to Layer")
        zoom_layer_btn.clicked.connect(self.zoom_to_layer)
        for button in (add_layer_btn, remove_layer_btn, zoom_layer_btn):
            button.setFixedWidth(150)

        # Left Panel Layout
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.layers_panel)
        left_layout.addWidget(add_layer_btn)
        left_layout.addWidget(remove_layer_btn)
        left_layout.addWidget(zoom_layer_btn)
        

        left_panel = QWidget()
        left_panel.setLayout(left_layout)

        # Add widgets to the main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(self.canvas)

        # Set the central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        main_layout.addWidget(left_panel, stretch=0)  # Left panel retains its fixed width
        main_layout.addWidget(self.canvas, stretch=1)  # Map canvas takes the rest of the space

        # Store added layers
        self.layer_references = {}

    def add_layer(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "Supported Files (*.tif *.tiff *.png *.jpg *.shp *.geojson);;Raster Files (*.tif *.tiff *.png *.jpg);;Vector Files (*.shp *.geojson)"
        )
        if not file_path:
            return

        layer_name = file_path.split("/")[-1]

        if file_path.endswith((".tif", ".tiff", ".png", ".jpg")):
            layer = QgsRasterLayer(file_path, layer_name)
        elif file_path.endswith((".shp", ".geojson")):
            layer = QgsVectorLayer(file_path, layer_name, "ogr")
        else:
            print("Unsupported layer type.")
            return

        if not layer.isValid():
            print(f"Layer {layer_name} failed to load!")
            return

        # Add the layer to the QGIS project
        QgsProject.instance().addMapLayer(layer)
        self.layer_references[layer_name] = layer

        # Add a checkbox to the layers panel
        self.add_layer_checkbox(layer_name)

        # Update the canvas layers and zoom to the new layer
        self.update_canvas_layers()
        self.canvas.zoomToFullExtent()

    def add_layer_checkbox(self, layer_name):
        """Add a checkbox to toggle visibility of the layer."""
        item = QListWidgetItem()
        checkbox = QCheckBox(layer_name)
        checkbox.setChecked(True)
        checkbox.stateChanged.connect(
            lambda state, name=layer_name: self.toggle_layer_visibility(name, state)
        )

        # Embed the checkbox into the QListWidget
        self.layers_panel.addItem(item)
        self.layers_panel.setItemWidget(item, checkbox)

    def toggle_layer_visibility(self, layer_name, state):
        """Toggle the visibility of a layer."""
        layer = self.layer_references.get(layer_name)
        if layer:
            tree_layer = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
            if tree_layer:
                tree_layer.setItemVisibilityChecked(state == 2)  # 2 = Qt.Checked

        self.update_canvas_layers()

    def remove_layer(self):
        """Remove the selected layers."""
        selected_items = [
            self.layers_panel.itemWidget(self.layers_panel.item(i))
            for i in range(self.layers_panel.count())
        ]
        for checkbox in selected_items:
            if checkbox and checkbox.isChecked():
                layer_name = checkbox.text()
                layer = self.layer_references.get(layer_name)
                if layer:
                    QgsProject.instance().removeMapLayer(layer.id())
                    del self.layer_references[layer_name]

                # Remove from the layers panel
                for i in range(self.layers_panel.count()):
                    if self.layers_panel.itemWidget(self.layers_panel.item(i)) == checkbox:
                        self.layers_panel.takeItem(i)
                        break

        self.update_canvas_layers()

    def zoom_to_layer(self):
        """Zoom to the extent of the selected layer."""
        selected_items = [
            self.layers_panel.itemWidget(self.layers_panel.item(i))
            for i in range(self.layers_panel.count())
        ]
        for checkbox in selected_items:
            if checkbox and checkbox.isChecked():
                layer_name = checkbox.text()
                layer = self.layer_references.get(layer_name)
                if layer:
                    self.canvas.setExtent(layer.extent())
                    self.canvas.refresh()
                break  # Zoom to the first selected layer

    def update_canvas_layers(self):
        """Update the map canvas with the current visible layers."""
        visible_layers = [
            self.layer_references[name]
            for name in self.layer_references
            if QgsProject.instance().layerTreeRoot().findLayer(self.layer_references[name].id()).isVisible()
        ]
        self.canvas.setLayers(visible_layers)
        self.canvas.refresh()


# Create the viewer instance
app = QApplication(sys.argv)
viewer = MapViewer()
viewer.show()
sys.exit(app.exec_())
