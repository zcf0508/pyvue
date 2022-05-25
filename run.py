import sys
import time

from Vue.Proxy import effect
from Vue import ref
from PyQt6.QtWidgets import QApplication, QWidget


def main():
    app = QApplication(sys.argv)

    hello = ref("hello world.")

    w = QWidget()
    
    @effect
    def init():
        w.resize(250, 200)
        w.move(300, 300)
        w.setWindowTitle(hello["value"])

    w.show()

    time.sleep(3)

    hello["value"] = "hello pyvue!"

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
