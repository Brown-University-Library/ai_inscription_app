#!/usr/bin/env python
import sys, importlib.util
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
spec = importlib.util.spec_from_file_location("leiden_epidoc", "leiden-epidoc.py")
leiden_epidoc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(leiden_epidoc)
app = QApplication(sys.argv)
window = leiden_epidoc.LeidenEpiDocGUI()
window.show()
window.input_text.setPlainText("Sample input")
window.translation_text.setPlainText("Translation text\nLine 2")
window.notes_text.setPlainText("Notes content\nLine 2")
window.analysis_text.setPlainText("Analysis content\nLine 2")
window.full_results_text.setPlainText("Full results\nLine 2")
def capture():
    window.grab().save("/tmp/separated_tabs.png")
    print("Done")
    app.quit()
QTimer.singleShot(500, capture)
app.exec()
