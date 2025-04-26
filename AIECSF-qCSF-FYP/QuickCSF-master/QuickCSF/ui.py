# -*- coding: utf-8 -*
'''User interaction (display and input)'''

import sys, traceback
import logging
import math, time

import numpy

from qtpy import QtCore, QtGui, QtWidgets, QtMultimedia
import argparseqt.gui

from . import assets

logger = logging.getLogger(__name__)

DEFAULT_INSTRUCTIONS = '''In this test, you will see two options - one is blank and the other contains a circular pattern with stripes.

Each option will be shown with a sound cue. After both sounds have played, you need to select which option contained the striped pattern.

Press [ ← Left Arrow ] if the striped pattern appeared with the first sound.
Press [ → Right Arrow ] if the striped pattern appeared with the second sound.

Throughout the test, please keep your eyes focused on the central dot.

If unsure, make your best guess.

Press [ Space ] to start the test.'''

class QuickCSFWindow(QtWidgets.QMainWindow):
    '''The main window for QuickCSF.app'''

    participantReady = QtCore.Signal()
    participantResponse = QtCore.Signal(object)

    def __init__(self, instructions=None, parent=None):
        super().__init__(parent)
        # Initialize counters
        self.correct_count = 0
        self.total_count = 0
        
        # Initialize dialog text
        self.dialog_titles = {
            'exit': 'Exit Test',
            'break': 'Break Time',
            'continue': 'Continue Test',
            'error': 'Error'
        }
        
        self.dialog_messages = {
            'exit': 'Are you sure you want to exit the test?',
            'continue': 'Would you like to continue with another test?',
            'break': 'Take a short break to rest your eyes.\nPress OK when ready to continue.',
            'error': 'An unexpected error occurred.\nPlease contact the test administrator.'
        }

        # Initialize error dialog text
        self.exit_title = 'Confirm Exit'
        self.exit_message = 'Are you sure you want to exit the test?'
        self.error_title = 'Missing Information'
        self.error_message = 'Please provide the following required information:\n\nSession ID\nViewing distance (mm)'
        self.application_error = 'An unexpected error occurred.\n\nThe application will now exit. Details may be available below.'

        self.displayWidget = QtWidgets.QLabel(self)
        self.displayWidget.setAlignment(QtCore.Qt.AlignCenter)
        self.displayWidget.setWordWrap(True)
        self.displayWidget.setMargin(100)
        self.displayWidget.setStyleSheet(
            '''
                background: rgb(127, 127, 127);
                color: #bbb;
                font-size: 28pt;
            '''
        )

        self.instructionsText = instructions if instructions is not None else DEFAULT_INSTRUCTIONS

        self.breakText = 'Well done! Take a break.\n\nPress [ Space ] when ready to continue.'
        self.readyText = 'Ready?'
        self.responseText = 'Make your choice'
        self.finishedText = 'Test Complete!'

        self.setCentralWidget(self.displayWidget)
        self.sounds = {
            'tone': QtMultimedia.QSound(assets.locate('tone.wav')),
            'good': QtMultimedia.QSound(assets.locate('good.wav')),
            'bad': QtMultimedia.QSound(assets.locate('bad.wav')),
        }

    def showInstructions(self):
        self.displayWidget.setText(self.instructionsText)

    def showReadyPrompt(self):
        self.displayWidget.setText(self.readyText)

    def showFixationCross(self):
        self.displayWidget.setText('+')

    def showStimulus(self, stimulus):
        self.displayWidget.setPixmap(QtGui.QPixmap.fromImage(stimulus))
        self.sounds['tone'].play()

    def showNonStimulus(self):
        self.showBlank()
        self.sounds['tone'].play()

    def showMask(self):
        self.displayWidget.setText('')

    def showBlank(self):
        self.displayWidget.clear()  # Clear all content
        self.displayWidget.setText('')  # Set empty text

    def giveFeedback(self, good):
        self.total_count += 1
        if good:
            self.correct_count += 1
            self.displayWidget.setText(f'Correct!\n\nAccuracy: {(self.correct_count/self.total_count*100):.1f}%')
            self.sounds['good'].play()
        else:
            self.displayWidget.setText(f'Incorrect\n\nAccuracy: {(self.correct_count/self.total_count*100):.1f}%')
            self.sounds['bad'].play()

    def showResponsePrompt(self):
        self.displayWidget.setText(self.responseText)

    def showBreak(self):
        self.displayWidget.setText(self.breakText)

    def showFinished(self, results):
        outputDisplay = f'''{self.finishedText}

Test Results:
------------
Accuracy: {(self.correct_count/self.total_count*100):.1f}% ({self.correct_count}/{self.total_count})

Vision Parameters:
----------------'''
        # Format parameter names to be more readable
        param_names = {
            'peakSensitivity': 'Peak Sensitivity',
            'peakFrequency': 'Peak Frequency',
            'bandwidth': 'Bandwidth',
            'delta': 'Delta',
            'aulcsf': 'Area Under CSF'
        }
        
        for key, value in results.items():
            if key in param_names:
                outputDisplay += f'\n{param_names[key]}: {value:.4f}'

        self.displayWidget.setText(outputDisplay)
        
        # Ask if user wants to continue with another test
        reply = QtWidgets.QMessageBox.question(
            self,
            self.dialog_titles['continue'],
            self.dialog_messages['continue'],
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self.reset_test()
        else:
            QtWidgets.QApplication.quit()
            
    def reset_test(self):
        """Reset test counters and start a new test"""
        self.correct_count = 0
        self.total_count = 0
        self.showInstructions()

    def keyReleaseEvent(self, event):
        logger.debug(f'Key released {event.key()}')
        if event.key() == QtCore.Qt.Key_Escape:
            reply = QtWidgets.QMessageBox.question(
                self,
                self.dialog_titles['exit'],
                self.dialog_messages['exit'],
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                QtWidgets.QApplication.quit()
        elif event.key() == QtCore.Qt.Key_Space:
            self.participantReady.emit()
        elif event.key() in (QtCore.Qt.Key_4, QtCore.Qt.Key_Left):
            self.participantResponse.emit(True)
        elif event.key() in (QtCore.Qt.Key_6, QtCore.Qt.Key_Right):
            self.participantResponse.emit(False)

    def onNewState(self, stateName, data):
        logger.debug(f'New state: {stateName} [{data}]')

        if stateName == 'INSTRUCTIONS':
            self.showInstructions()
        elif stateName == 'BREAKING':
            self.showBreak()
        elif stateName == 'WAIT_FOR_READY':
            self.showReadyPrompt()
        elif 'FIXATION' in stateName:
            self.showFixationCross()
        elif '_BLANK' in stateName:
            self.showBlank()
        elif stateName == 'SHOW_STIMULUS_1':
            if data.stimulusOnFirst:
                self.showStimulus(data.stimulus)
            else:
                self.showNonStimulus()
        elif stateName == 'SHOW_MASK_1':
            self.showMask()
        elif stateName == 'SHOW_STIMULUS_2':
            if not data.stimulusOnFirst:
                self.showStimulus(data.stimulus)
            else:
                self.showNonStimulus()
        elif stateName == 'SHOW_MASK_2':
            self.showMask()
        elif stateName == 'WAIT_FOR_RESPONSE':
            self.showResponsePrompt()
        elif stateName == 'FEEDBACK':
            self.giveFeedback(data.correct)
        elif stateName == 'FINISHED':
            self.showFinished(data)

def getSettings(parser, settings, requiredFields=[]):
    '''Display a GUI to collect experiment settings'''
    dialog = argparseqt.gui.ArgDialog(parser)
    dialog.setValues(settings)
    dialog.exec_()
    if dialog.result() == QtWidgets.QDialog.Accepted:
        settings = dialog.getValues()

        for field in requiredFields:
            if settings[field] == None:
                QtWidgets.QMessageBox.critical(
                    None,
                     'Missing Information',
                     'Please provide the following required information:\n\nsessionID\ndistance_mm (viewing distance in mm)'
                )
                return None
    else:
        return None

    return settings

def exception_handler(excType, exc, tb, extraDetails=None, parentWindow=None):
    if issubclass(excType, KeyboardInterrupt):
        sys.__excepthook__(excType, exc, tb)
        return

    stack = traceback.format_tb(tb)

    details = '%s: %s\n%s' % (excType.__name__, exc, ''.join(stack))
    print('UNHANDLED EXCEPTION! ' + details, file=sys.stderr)

    dialog = QtWidgets.QMessageBox(parentWindow)
    dialog.setWindowTitle('QuickCSF - Application Error')
    dialog.setText('Something went wrong and we were not prepared for it :(\n\nThe application will now exit, but some details may be available below.')

    if extraDetails is not None:
        details = extraDetails + '\n\n' + details

    dialog.setDetailedText(details)
    dialog.setModal(True)
    dialog.exec_()
    QtWidgets.QApplication.exit()

def popupUncaughtExceptions(extraDetails=None, parent=None):
    sys.excepthook = lambda excType, exc, tb: exception_handler(excType, exc, tb, extraDetails, parent)
