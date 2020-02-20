#!/usr/bin/env python

# CS 530
# Project 2 Task 1
# Luke Jiang
# 02/11/2020

""" Description:
Display the CT dataset using isosurfacing while supporting interactive
    modification of the corresponding isovalue.
Use three clipping planes for each dimension to show internal details.

Command line interface: python isosurface.py <head.vti>
    <data>:     head scalar dataset to visualize
"""

""" Observations:
Identify salient isovalues:
    Head-to-Muscle:     1020
    Muscle-to-Bone:     1080
"""

import vtk
import sys
import argparse

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSlider, QGridLayout, QLabel, QPushButton
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


INIT_CONTOUR_VAL = 700
MAX_CONTOUR_VAL = 1200

REN_DATA = [[1020, 197, 140, 133, 0.7],
            [1080, 230, 230, 230, 0.9]]

def makeBasic(filename):
    # read the head image
    reader = vtk.vtkXMLImageDataReader()
    reader.SetFileName(filename)
    reader.Update()

    # enable depth peeling in renderer
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.75, 0.75, 0.75)
    ren.SetUseDepthPeeling(1)
    ren.SetMaximumNumberOfPeels(100)
    ren.SetOcclusionRatio(0.4)
    ren.ResetCamera()

    return reader, ren


def make(reader, renData):
    [isoValue, R, G, B, opacity] = renData
    # the contour filter
    contour = vtk.vtkContourFilter()
    contour.SetValue(0, isoValue)
    contour.SetInputConnection(reader.GetOutputPort())

    # define the color map
    colorTrans = vtk.vtkColorTransferFunction()
    colorTrans.SetColorSpaceToRGB()
    colorTrans.AddRGBPoint(isoValue, R/256, G/256, B/256)

    # mapper and actor
    mapper = vtk.vtkDataSetMapper()
    mapper.SetInputConnection(contour.GetOutputPort())
    mapper.SetLookupTable(colorTrans)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetOpacity(opacity)

    return actor


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName('The Main Window')
        MainWindow.setWindowTitle('salient_head')

        self.centralWidget = QWidget(MainWindow)
        self.gridlayout = QGridLayout(self.centralWidget)
        self.vtkWidget = QVTKRenderWindowInteractor(self.centralWidget)

        self.slider_contour = QSlider()

        self.gridlayout.addWidget(self.vtkWidget, 0, 0, 4, 4)

        self.gridlayout.addWidget(QLabel("Contour Value"), 4, 0, 1, 1)
        self.gridlayout.addWidget(self.slider_contour, 4, 1, 1, 1)

        MainWindow.setCentralWidget(self.centralWidget)


class IsosurfaceDemo(QMainWindow):

    def __init__(self, margs, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        filename = margs.file                # head dataset file name
        self.contourVal = INIT_CONTOUR_VAL   # initial contour value

        self.reader, self.ren = makeBasic(filename)

        for d in REN_DATA:
            actor = make(self.reader, d)
            self.ren.AddActor(actor)

        self.ui.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.ui.vtkWidget.GetRenderWindow().GetInteractor()

        def slider_setup(slider, val, bounds, interv):
            slider.setOrientation(QtCore.Qt.Horizontal)
            slider.setValue(float(val))
            slider.setTracking(False)
            slider.setTickInterval(interv)
            slider.setTickPosition(QSlider.TicksAbove)
            slider.setRange(bounds[0], bounds[1])

        slider_setup(self.ui.slider_contour, self.contourVal, [INIT_CONTOUR_VAL, MAX_CONTOUR_VAL], 10)

    def contour_callback(self, val):
        print(val)
        self.contourVal = val
        self.contour.SetValue(0, self.contourVal)
        self.ui.vtkWidget.GetRenderWindow().Render()


if __name__ == "__main__":

    # --define argument parser and parse arguments--
    parser = argparse.ArgumentParser(
        description="Parser for salient_head")
    parser.add_argument('file')
    args = parser.parse_args()

    # --main app--
    app = QApplication(sys.argv)
    window = IsosurfaceDemo(margs=args)
    window.ui.vtkWidget.GetRenderWindow().SetSize(800, 800)
    window.show()
    window.setWindowState(Qt.WindowMaximized)
    window.iren.Initialize()

    # --hook up callbacks--
    # window.ui.slider_contour.valueChanged.connect(window.contour_callback)

    sys.exit(app.exec_())
