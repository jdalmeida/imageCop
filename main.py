# main_app.py
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QProgressBar, QTreeWidget, QTreeWidgetItem, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QFont

# Import the function from the previously created module
from image_comparator import find_similar_images

class ScanWorker(QThread):
    """ Worker thread to run the image comparison without freezing the GUI """
    progress = pyqtSignal(int, int, str) # current_step, total_steps, message
    results = pyqtSignal(dict) # Signal to send back the results
    error = pyqtSignal(str) # Signal for errors
    finished = pyqtSignal() # Signal when done

    def __init__(self, folder_path, hash_size=8, similarity_threshold=5):
        super().__init__()
        self.folder_path = folder_path
        self.hash_size = hash_size
        self.similarity_threshold = similarity_threshold
        self._is_running = True

    def run(self):
        try:
            print(f"Worker started for folder: {self.folder_path}")
            similar_groups = find_similar_images(
                self.folder_path,
                hash_size=self.hash_size,
                similarity_threshold=self.similarity_threshold,
                progress_callback=self.report_progress
            )
            if self._is_running: # Check if stopped before emitting results
                if similar_groups is not None:
                    self.results.emit(similar_groups)
                else:
                    # find_similar_images handles folder not found, emit specific error?
                    # For now, assume callback handled it, or emit a generic error.
                    # self.error.emit("Erro ao processar a pasta.") # Example
                    pass # Progress callback should have informed the user
        except Exception as e:
            print(f"Error in worker thread: {e}")
            if self._is_running:
                self.error.emit(f"Ocorreu um erro inesperado: {e}")
        finally:
            if self._is_running:
                self.finished.emit()
            print("Worker finished.")

    def report_progress(self, current, total, message):
        # Only emit if the thread hasn't been told to stop
        if self._is_running:
            self.progress.emit(current, total, message)

    def stop(self):
        print("Stopping worker thread...")
        self._is_running = False

class ImagePreviewLabel(QLabel):
    """Widget customizado para mostrar preview de imagens no hover"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.ToolTip)
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #333;
                background-color: white;
                padding: 5px;
            }
        """)
        self.setMaximumSize(300, 300)
        self.setMinimumSize(100, 100)
        self.setScaledContents(True)
        self.hide()

    def show_image(self, image_path, x, y):
        """Mostra a imagem no preview"""
        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Redimensiona mantendo proporção
                scaled_pixmap = pixmap.scaled(
                    250, 250, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                self.setPixmap(scaled_pixmap)
                self.resize(scaled_pixmap.size())
                
                # Posiciona o preview próximo ao cursor
                self.move(x + 10, y + 10)
                self.show()
            else:
                self.hide()
        except Exception as e:
            print(f"Erro ao carregar preview da imagem {image_path}: {e}")
            self.hide()

    def hide_image(self):
        """Esconde o preview"""
        self.hide()

class CustomTreeWidget(QTreeWidget):
    """QTreeWidget customizado com preview de imagem no hover"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.preview_label = ImagePreviewLabel(self)
        self.hover_timer = QTimer()
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self.show_preview)
        self.current_item = None
        self.mouse_pos = None
        
        # Habilita tracking do mouse
        self.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        """Captura movimento do mouse para mostrar preview"""
        super().mouseMoveEvent(event)
        
        item = self.itemAt(event.pos())
        self.mouse_pos = event.globalPosition().toPoint()
        
        if item != self.current_item:
            self.current_item = item
            self.hover_timer.stop()
            self.preview_label.hide_image()
            
            if item:
                item_data = item.data(0, Qt.ItemDataRole.UserRole)
                if item_data and not item_data.get("is_group", False):
                    # Só mostra preview para imagens, não para grupos
                    self.hover_timer.start(500)  # Delay de 500ms

    def leaveEvent(self, event):
        """Esconde preview quando o mouse sai da árvore"""
        super().leaveEvent(event)
        self.hover_timer.stop()
        self.preview_label.hide_image()
        self.current_item = None

    def show_preview(self):
        """Mostra o preview da imagem"""
        if self.current_item and self.mouse_pos:
            item_data = self.current_item.data(0, Qt.ItemDataRole.UserRole)
            if item_data and not item_data.get("is_group", False):
                image_path = item_data.get("path")
                if image_path and os.path.exists(image_path):
                    self.preview_label.show_image(
                        image_path, 
                        self.mouse_pos.x(), 
                        self.mouse_pos.y()
                    )

class DuplicateImageFinderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Localizador de Imagens Duplicadas/Similares")
        self.setGeometry(100, 100, 800, 600) # x, y, width, height
        self.selected_folder = ""
        self.scan_thread = None

        # --- Layouts --- 
        self.main_layout = QVBoxLayout(self)

        # Top section: Folder selection
        self.folder_layout = QHBoxLayout()
        self.folder_label = QLabel("Pasta selecionada:")
        self.folder_path_label = QLabel("Nenhuma pasta selecionada")
        self.folder_path_label.setStyleSheet("font-style: italic; color: grey;")
        self.browse_button = QPushButton("Selecionar Pasta")
        self.browse_button.clicked.connect(self.browse_folder)

        self.folder_layout.addWidget(self.folder_label)
        self.folder_layout.addWidget(self.folder_path_label, 1) # Stretch label
        self.folder_layout.addWidget(self.browse_button)
        self.main_layout.addLayout(self.folder_layout)

        # Middle section: Controls and Progress
        self.controls_layout = QHBoxLayout()
        self.scan_button = QPushButton("Iniciar Verificação")
        self.scan_button.setEnabled(False) # Disabled until folder is selected
        self.scan_button.clicked.connect(self.start_scan)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False) # Hide initially
        self.status_label = QLabel("") # For messages like 'Scanning...' or 'Done.'
        self.status_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.controls_layout.addWidget(self.scan_button)
        self.controls_layout.addWidget(self.progress_bar, 1)
        self.controls_layout.addWidget(self.status_label, 2)
        self.main_layout.addLayout(self.controls_layout)

        # Bottom section: Results Tree
        self.results_tree = CustomTreeWidget()  # Usar a árvore customizada
        self.results_tree.setColumnCount(2)
        self.results_tree.setHeaderLabels(["Grupo / Imagem", "Caminho Completo"])
        self.results_tree.setColumnWidth(0, 350) # Adjust width as needed
        self.results_tree.itemDoubleClicked.connect(self.open_image_location) # Open folder on double click
        self.main_layout.addWidget(self.results_tree)

        # --- Styling (Optional) ---
        self.setStyleSheet("""
            QWidget { font-size: 11pt; }
            QPushButton { padding: 5px 10px; }
            QLabel#folder_path_label { border: 1px solid lightgrey; padding: 3px; background-color: #f0f0f0; }
            QTreeWidget { border: 1px solid lightgrey; }
            QHeaderView::section { background-color: #e0e0e0; padding: 4px; border: 1px solid grey; font-weight: bold; }
        """)
        self.folder_path_label.setObjectName("folder_path_label") # For specific styling

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta de Imagens")
        if folder:
            self.selected_folder = folder
            self.folder_path_label.setText(folder)
            self.folder_path_label.setStyleSheet("font-style: normal; color: black;") # Reset style
            self.scan_button.setEnabled(True)
            self.results_tree.clear() # Clear previous results
            self.status_label.setText("Pasta selecionada. Clique em 'Iniciar Verificação'.")
            self.progress_bar.setVisible(False)

    def start_scan(self):
        if not self.selected_folder:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione uma pasta primeiro.")
            return

        if self.scan_thread and self.scan_thread.isRunning():
            # Option to stop the current scan
            reply = QMessageBox.question(self, "Verificação em Andamento",
                                         "Uma verificação já está em andamento. Deseja pará-la?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.scan_thread.stop()
                # Wait briefly for thread to acknowledge stop? Or handle in finished signal.
                self.scan_button.setText("Iniciar Verificação")
                self.progress_bar.setVisible(False)
                self.status_label.setText("Verificação cancelada.")
            return # Don't start a new scan yet

        self.results_tree.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Iniciando verificação...")
        self.scan_button.setText("Parar Verificação") # Change button text
        self.browse_button.setEnabled(False) # Disable browse during scan

        # Create and start the worker thread
        self.scan_thread = ScanWorker(self.selected_folder)
        self.scan_thread.progress.connect(self.update_progress)
        self.scan_thread.results.connect(self.display_results)
        self.scan_thread.error.connect(self.show_error)
        self.scan_thread.finished.connect(self.scan_finished)
        self.scan_thread.start()

    def update_progress(self, current_step, total_steps, message):
        if total_steps > 0:
            percentage = int((current_step / total_steps) * 100)
            self.progress_bar.setValue(percentage)
        self.status_label.setText(message)

    def display_results(self, similar_groups):
        self.results_tree.clear()
        if not similar_groups:
            self.status_label.setText("Nenhum grupo de imagens similares encontrado.")
            QMessageBox.information(self, "Concluído", "Nenhum grupo de imagens similares foi encontrado na pasta selecionada.")
            return

        self.status_label.setText(f"Encontrados {len(similar_groups)} grupos de imagens similares.")

        group_count = 1
        for representative_path, group_paths in similar_groups.items():
            # Parent item for the group
            group_item = QTreeWidgetItem(self.results_tree, [f"Grupo {group_count} ({len(group_paths)} imagens)", os.path.dirname(representative_path)])
            group_item.setToolTip(0, f"Representante: {os.path.basename(representative_path)}\nCaminho: {os.path.dirname(representative_path)}")
            group_item.setFlags(group_item.flags() & ~Qt.ItemFlag.ItemIsSelectable) # Make group header non-selectable itself
            group_item.setData(0, Qt.ItemDataRole.UserRole, {"is_group": True, "path": os.path.dirname(representative_path)}) # Store path for opening

            # Child items for each image in the group
            for img_path in group_paths:
                file_name = os.path.basename(img_path)
                child_item = QTreeWidgetItem(group_item, [file_name, img_path])
                child_item.setToolTip(0, f"Clique duplo para abrir a pasta.\nCaminho: {img_path}")
                child_item.setToolTip(1, img_path)
                # Add checkbox for future deletion feature
                child_item.setFlags(child_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                child_item.setCheckState(0, Qt.CheckState.Unchecked)
                child_item.setData(0, Qt.ItemDataRole.UserRole, {"is_group": False, "path": img_path}) # Store path

                # Optional: Add a small thumbnail?
                # try:
                #     pixmap = QPixmap(img_path)
                #     if not pixmap.isNull():
                #         icon = QIcon(pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                #         child_item.setIcon(0, icon)
                # except Exception as e:
                #     print(f"Could not load thumbnail for {img_path}: {e}")

            group_count += 1

        self.results_tree.expandAll() # Expand all groups initially
        QMessageBox.information(self, "Concluído", f"Verificação concluída. {len(similar_groups)} grupos de imagens similares encontrados.")

    def show_error(self, error_message):
        self.status_label.setText(f"Erro: {error_message}")
        QMessageBox.critical(self, "Erro", error_message)
        self.scan_finished() # Ensure UI resets even on error

    def scan_finished(self):
        self.scan_button.setText("Iniciar Verificação")
        self.browse_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        # Keep the status message unless it was an error message
        if "Erro:" not in self.status_label.text():
             # If results were displayed, keep that message, otherwise set to idle
             if not self.results_tree.topLevelItemCount() > 0 and "Nenhum grupo" not in self.status_label.text():
                 self.status_label.setText("Pronto. Selecione uma pasta ou inicie a verificação.")

        self.scan_thread = None # Clear the thread reference

    def open_image_location(self, item, column):
        """ Opens the containing folder of the double-clicked item. """
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data:
            return

        path_to_open = item_data.get("path")
        if not path_to_open:
            return

        # If it's an image file, open its directory. If it's a group header, open that directory.
        if not item_data.get("is_group", False):
            folder_path = os.path.dirname(path_to_open)
        else:
            folder_path = path_to_open

        try:
            # Platform specific way to open folder
            if sys.platform == 'win32':
                os.startfile(folder_path)
            elif sys.platform == 'darwin': # macOS
                os.system(f'open "{folder_path}"')
            else: # Linux and other Unix-like
                os.system(f'xdg-open "{folder_path}"')
            print(f"Attempted to open folder: {folder_path}")
        except Exception as e:
            print(f"Could not open folder {folder_path}: {e}")
            QMessageBox.warning(self, "Erro", f"Não foi possível abrir a pasta: {folder_path}\nErro: {e}")

    def closeEvent(self, event):
        """ Ensure worker thread is stopped before closing """
        if self.scan_thread and self.scan_thread.isRunning():
            print("Attempting to stop worker thread on close...")
            self.scan_thread.stop()
            # Give the thread a moment to stop - adjust timeout as needed
            if not self.scan_thread.wait(1000): # Wait 1 second
                 print("Warning: Worker thread did not stop gracefully.")
                 # Optionally force termination if wait fails, though generally discouraged
                 # self.scan_thread.terminate()
                 # self.scan_thread.wait()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # You might want to set an application icon here
    # app.setWindowIcon(QIcon('path/to/your/icon.png'))
    main_window = DuplicateImageFinderApp()
    main_window.show()
    sys.exit(app.exec())

