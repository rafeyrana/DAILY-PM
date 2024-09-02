import sys
from PyQt5.QtWidgets import QApplication
from gui.commit_history_gui import CommitHistoryGUI
from gui.virtual_pm_gui import VirtualPMGUI

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Uncomment one of the following lines to run the desired GUI
    # gui = CommitHistoryGUI()
    gui = VirtualPMGUI()

    gui.show()
    sys.exit(app.exec_())