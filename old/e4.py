import sys
import os
import platform
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QSlider, QLabel, 
                               QFileDialog, QFrame, QMessageBox)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QPixmap
os.environ["PATH"] = os.path.dirname(__file__) + os.pathsep + os.environ["PATH"]
import mpv
import locale


class MPVPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.mpv_player = None
        self.video_file = None
        self.duration = 0
        self.current_position = 0
        self.is_playing = False
        self.volume = 50
        
        # Timer para actualizar la posición
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_position)
        self.timer.start(100)  # Actualizar cada 100ms para mejor precisión
        
        self.init_ui()
        self.init_mpv()
        
    def init_ui(self):
        self.setWindowTitle("Reproductor MPV - PySide6")
        self.setGeometry(100, 100, 800, 600)
        
        # Layout principal
        main_layout = QVBoxLayout()
        
        # Área de video (frame negro)
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
        self.video_frame.setMinimumHeight(400)
        main_layout.addWidget(self.video_frame)
        
        # Controles
        controls_layout = self.create_controls()
        main_layout.addLayout(controls_layout)
        
        self.setLayout(main_layout)
        
    def init_mpv(self):
        """Inicializar el reproductor MPV"""
        try:
            # Configuración específica por sistema operativo
            if platform.system() == 'Linux':
                # Linux: mejor compatibilidad con X11/Wayland
                mpv_config = {
                    'wid': str(int(self.video_frame.winId())),
                    'vo': 'gpu',  # o 'xv' como fallback
                    'hwdec': 'auto-safe',  # más conservador en Linux
                    'gpu_context': 'auto',
                    'screenshot_directory': os.path.expanduser('~/Pictures'),
                    'x11_name': 'mpv-player'  # nombre para el gestor de ventanas
                }
            else:  # Windows
                # Windows: configuración optimizada para Windows
                mpv_config = {
                    'wid': str(int(self.video_frame.winId())),
                    'vo': 'gpu',  # o 'direct3d' como alternativa
                    'hwdec': 'auto',  # menos restrictivo en Windows
                    'gpu_api': 'auto',  # detectar automáticamente (D3D11, Vulkan, etc.)
                    'screenshot_directory': os.path.expanduser('~/Pictures'),
                    'ontop': False  # evitar problemas de ventana en Windows
                }
            
            # Configuración común para ambos sistemas
            common_config = {
                'keep_open': True,
                'idle': True,
                'osd_level': 0,
                'cursor_autohide': False,
                'input_default_bindings': False,
                'input_vo_keyboard': False,
                'input_cursor': False,
                'screenshot_format': 'png',
                'screenshot_png_compression': 8,
                'pause': True  # comenzar pausado
            }
            
            # Combinar configuraciones
            final_config = {**mpv_config, **common_config}
            
            # Crear el reproductor MPV
            self.mpv_player = mpv.MPV(**final_config)
            
            # Callbacks para eventos
            @self.mpv_player.property_observer('time-pos')
            def time_observer(_name, value):
                if value is not None:
                    self.current_position = value
                    
            @self.mpv_player.property_observer('duration')
            def duration_observer(_name, value):
                if value is not None:
                    self.duration = value
                    
            @self.mpv_player.property_observer('pause')
            def pause_observer(_name, value):
                if value is not None:
                    self.is_playing = not value
                    
            @self.mpv_player.property_observer('volume')
            def volume_observer(_name, value):
                if value is not None:
                    self.volume = int(value)
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo inicializar MPV: {str(e)}")
            sys.exit(1)
        
    def create_controls(self):
        # Layout principal de controles
        main_controls = QVBoxLayout()
        
        # Botón para abrir archivo
        open_button = QPushButton("Abrir Video")
        open_button.clicked.connect(self.open_file)
        main_controls.addWidget(open_button)
        
        # Slider de tiempo
        time_layout = QHBoxLayout()
        self.time_label = QLabel("00:00 / 00:00")
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setMinimum(0)
        self.time_slider.setMaximum(1000)  # Usar 1000 para mejor precisión
        self.time_slider.valueChanged.connect(self.seek_video)
        self.time_slider.sliderPressed.connect(self.on_slider_pressed)
        self.time_slider.sliderReleased.connect(self.on_slider_released)
        self.slider_pressed = False
        
        time_layout.addWidget(self.time_label)
        time_layout.addWidget(self.time_slider)
        main_controls.addLayout(time_layout)
        
        # Controles de reproducción
        playback_layout = QHBoxLayout()
        
        # Botones principales
        self.play_button = QPushButton("▶ Play")
        self.play_button.clicked.connect(self.toggle_play_pause)
        
        self.pause_button = QPushButton("⏸ Pause")
        self.pause_button.clicked.connect(self.pause_video)
        
        self.stop_button = QPushButton("⏹ Stop")
        self.stop_button.clicked.connect(self.stop_video)
        
        playback_layout.addWidget(self.play_button)
        playback_layout.addWidget(self.pause_button)
        playback_layout.addWidget(self.stop_button)
        
        # Controles de frame
        self.prev_frame_button = QPushButton("◀◀ Frame Ant")
        self.prev_frame_button.clicked.connect(self.previous_frame)
        
        self.next_frame_button = QPushButton("▶▶ Frame Sig")
        self.next_frame_button.clicked.connect(self.next_frame)
        
        playback_layout.addWidget(self.prev_frame_button)
        playback_layout.addWidget(self.next_frame_button)
        
        # Controles de navegación
        self.rewind_button = QPushButton("⏪ -10s")
        self.rewind_button.clicked.connect(self.rewind)
        
        self.forward_button = QPushButton("⏩ +10s")
        self.forward_button.clicked.connect(self.forward)
        
        playback_layout.addWidget(self.rewind_button)
        playback_layout.addWidget(self.forward_button)
        
        # Botón de captura
        self.screenshot_button = QPushButton("📷 Captura")
        self.screenshot_button.clicked.connect(self.take_screenshot)
        playback_layout.addWidget(self.screenshot_button)
        
        main_controls.addLayout(playback_layout)
        
        # Control de volumen
        volume_layout = QHBoxLayout()
        volume_label = QLabel("🔊 Volumen:")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.change_volume)
        self.volume_value_label = QLabel("50%")
        
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_value_label)
        main_controls.addLayout(volume_layout)
        
        # Información adicional
        info_layout = QHBoxLayout()
        self.info_label = QLabel("Listo para reproducir")
        info_layout.addWidget(self.info_label)
        main_controls.addLayout(info_layout)
        
        return main_controls
        
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Seleccionar archivo de video",
            "",
            "Videos (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v *.3gp);;Todos los archivos (*)"
        )
        
        if file_path:
            self.video_file = file_path
            self.load_video()
            
    def load_video(self):
        if not self.video_file:
            return
            
        try:
            # Cargar el archivo de video
            self.mpv_player.loadfile(self.video_file)
            self.mpv_player.pause = True  # Comenzar pausado
            self.info_label.setText(f"Cargado: {os.path.basename(self.video_file)}")
            
            # Resetear controles
            self.current_position = 0
            self.time_slider.setValue(0)
            self.is_playing = False
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo cargar el video: {str(e)}")
            
    def on_slider_pressed(self):
        self.slider_pressed = True
        
    def on_slider_released(self):
        self.slider_pressed = False
        
    def toggle_play_pause(self):
        if self.mpv_player and self.video_file:
            if self.is_playing:
                self.pause_video()
            else:
                self.play_video()
                
    def play_video(self):
        if self.mpv_player and self.video_file:
            self.mpv_player.pause = False
            self.is_playing = True
            self.info_label.setText("Reproduciendo...")
            
    def pause_video(self):
        if self.mpv_player:
            self.mpv_player.pause = True
            self.is_playing = False
            self.info_label.setText("Pausado")
            
    def stop_video(self):
        if self.mpv_player:
            self.mpv_player.stop()
            self.is_playing = False
            self.current_position = 0
            self.time_slider.setValue(0)
            self.info_label.setText("Detenido")
            self.update_time_label()
            
    def seek_video(self, position):
        if self.mpv_player and self.video_file and self.duration > 0:
            if self.slider_pressed:  # Solo buscar cuando el usuario esté arrastrando
                time_position = (position / 1000) * self.duration
                self.mpv_player.seek(time_position, reference='absolute')
                
    def previous_frame(self):
        if self.mpv_player and self.video_file:
            self.mpv_player.frame_back_step()
            
    def next_frame(self):
        if self.mpv_player and self.video_file:
            self.mpv_player.frame_step()
            
    def rewind(self):
        if self.mpv_player and self.video_file:
            self.mpv_player.seek(-10, reference='relative')
            
    def forward(self):
        if self.mpv_player and self.video_file:
            self.mpv_player.seek(10, reference='relative')
            
    def change_volume(self, value):
        if self.mpv_player:
            self.mpv_player.volume = value
            self.volume_value_label.setText(f"{value}%")
            
    def take_screenshot(self):
        if self.mpv_player and self.video_file:
            try:
                # Tomar captura de pantalla
                self.mpv_player.screenshot()
                
                # Obtener información del archivo
                video_name = os.path.splitext(os.path.basename(self.video_file))[0]
                screenshot_dir = self.mpv_player.screenshot_directory
                
                QMessageBox.information(
                    self, 
                    "Captura realizada", 
                    f"Captura guardada en:\n{screenshot_dir}\n\n"
                    f"Busca archivos que empiecen con: {video_name}"
                )
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo tomar la captura: {str(e)}")
                
    def update_position(self):
        if self.mpv_player and self.video_file and not self.slider_pressed:
            try:
                # Actualizar slider de tiempo
                if self.duration > 0 and self.current_position is not None:
                    progress = (self.current_position / self.duration) * 1000
                    self.time_slider.setValue(int(progress))
                    
                # Actualizar etiqueta de tiempo
                self.update_time_label()
                
                # Actualizar slider de volumen si es necesario
                if self.volume_slider.value() != self.volume:
                    self.volume_slider.setValue(self.volume)
                    self.volume_value_label.setText(f"{self.volume}%")
                    
            except Exception as e:
                pass  # Ignorar errores menores de actualización
                
    def update_time_label(self):
        current_time = self.format_time(self.current_position if self.current_position else 0)
        total_time = self.format_time(self.duration if self.duration else 0)
        self.time_label.setText(f"{current_time} / {total_time}")
        
    def format_time(self, seconds):
        if seconds is None:
            seconds = 0
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
        
    def closeEvent(self, event):
        if self.mpv_player:
            try:
                self.mpv_player.terminate()
            except:
                pass
        event.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reproductor MPV - Python")
        self.setGeometry(100, 100, 900, 700)
        
        # Widget central
        self.player = MPVPlayer()
        self.setCentralWidget(self.player)


def main():
    app = QApplication(sys.argv)
    
    # Verificar si la librería mpv está disponible
    try:
        import mpv
    except ImportError:
        QMessageBox.critical(None, "Error", 
                           "La librería python-mpv no está instalada.\n\n"
                           "Instalación:\n"
                           "pip install python-mpv\n\n"
                           "También necesitas tener MPV instalado en tu sistema:\n"
                           "Windows: Descargar desde https://mpv.io/\n"
                           "Linux: sudo apt install mpv libmpv-dev (Ubuntu/Debian)\n"
                           "       sudo pacman -S mpv (Arch Linux)")
        sys.exit(1)
    
    try:
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Error al iniciar la aplicación: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()