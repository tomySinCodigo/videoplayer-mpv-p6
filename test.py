import sys
import platform
from PySide6.QtWidgets import QApplication
from player_mpv import PlayerMpv


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = PlayerMpv()
    if platform.system() == "Linux":
        v1 = "/run/media/tomy/sis/temp-test/video.mp4"
    elif platform.system() == "Windows":
        v1 = "D:/temp-test/video.mp4"
    else:
        print(platform.system())
        
    player.setVideo(v1)
    player.show()
    sys.exit(app.exec())
