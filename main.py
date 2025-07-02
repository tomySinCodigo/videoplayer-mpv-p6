import sys, os
os.environ["PATH"] = os.path.dirname(__file__) + os.pathsep + os.environ["PATH"]
import mpv
from PySide6.QtWidgets import (QApplication, QWidget)
from PySide6.QtCore import Qt
from skin_player import Ui_SkinPlayer
# from PySide6.QtGui 


class PlayerMpv(QWidget, Ui_SkinPlayer):
    def __init__(self, *args, **kw):
        super(PlayerMpv, self).__init__(*args, **kw)
        self.setupUi(self)
        self.__configPlayerMpv()

    def __configPlayerMpv(self):
        self.player = mpv.MPV(
            wid=0, vo='gpu', keep_open=True,
            idle=True, log_handler=print,
            loglevel='info'
        )

        self._duration = 0
        self._position = 0
        self._inmove = True
        self.player.wid = int(self.fm_video.winId())
        
        # @self.player.property_observer('time-pos')
        # def time_obserber(name, value):
        #     if value is not None and not self.inmove:
        #         self._position = value
        #         self.update_time_display()

        self.bt_play.clicked.connect(self.playPause)

    def update_time_display(self):
        if not self._inmove:
            self.lb_time.setText('')

    def format_time(self, seconds):
        if seconds is None:
            return '00:00:00'
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f'{minutes:02d}:{seconds:02d}'
    
    def set_video(self, url:str):
        self.player.loadfile(url)
    
    def play(self):
        self.player.pause = False

    def pause(self):
        self.player.pause = True

    def stop(self):
        self.player.stop()

    def set_vol(self, value):
        self.player.volume = value
        self.lb_vol.setText(f'{value}%')

    def closeEvent(self, event):
        self.player.terminate()
        event.accept()

    def _getProperty(self, prop:str) -> str|bool :
        return self.player._get_property(prop)
    
    def _setProperty(self, *args):
        self.player._set_property(*args)

    def playPause(self):
        std:bool = self._getProperty(prop='core-idle')
        self.player.pause = not std
           


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    app.setStyle("Windows11")
    wg = PlayerMpv()

    v1 = "D:/temp-test/video.mp4"
    wg.set_video(v1)
    wg.show()
    sys.exit(app.exec())