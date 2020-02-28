#!/usr/bin/env python

# CS 530
# Project 3 Task 1
# Luke Jiang
# 02/21/2020

""" Description:
Find and display salient isosurfaces of the flame dataset

Command line interface: python isoflame.py <flame.vti>
    <data>:     flame scalar dataset to visualize
"""

""" Observations:
Identify salient isovalues:
    sheet structure to tubular:    9000    
"""

# 92 99 223  blue   low isovalue
# 220 30 53  red    high isovalue

import vtk
import sys
import argparse

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSlider, QGridLayout, QLabel, QPushButton
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


INIT_CONTOUR_VAL = 1000
MAX_CONTOUR_VAL = 65000

# REN_DATA = [[9000, 112, 123, 223, 0.5],
#             [49000, 220, 30, 53, 0.5]]

# REN_DATA = [[32000, 87,  86,  124, 0.5],
#             [35000, 108, 115, 128, 0.4],
#             [38000, 201, 62,  71,  0.3],
#             [41000, 240, 94,  82,  0.2],
#             [42000, 212, 149, 150, 0.1]]

# REN_DATA = [[32000, 45,  119,  247, 0.5],
#             [35000, 189, 212, 252, 0.4],
#             [38000, 247, 20,  20,  0.3],
#             [41000, 286, 130, 130,  0.3],
#             [42000, 225, 240, 240, 0.3]]

REN_DATA1 = [[32000, 87,  86,  124, 0],
            [35000, 108, 115, 128, 0],
            [31000, 201, 62,  71,  0.3],
            [41000, 240, 94,  82,  0.4],
            [51000, 252, 175, 175, 0.7]]

REN_DATA = [[32000, 50,  50,  255, 0.3],
            [35000, 100, 100, 255, 0.2],
            [41000, 255, 242,  242,  0.5], # 0.7
            # [46000, 255, 150, 150, 0.4],  # 0.6
            [51000, 255, 27, 27, 0.3]]  #0.5

def makeBasic(filename):
    # read the head image
    reader = vtk.vtkXMLImageDataReader()
    reader.SetFileName(filename)
    reader.Update()

    # enable depth peeling in renderer
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.75, 0.75, 0.75)
    ren.SetUseDepthPeeling(1)
    ren.SetMaximumNumberOfPeels(50)
    ren.SetOcclusionRatio(0)
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
    # colorTrans.AddRGBPoint(isoValue+1000, (R+10)/256, (G+10)/256, (B+10)/256)

    # mapper and actor
    mapper = vtk.vtkDataSetMapper()
    mapper.SetInputConnection(contour.GetOutputPort())
    mapper.SetLookupTable(colorTrans)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetOpacity(opacity)

    return contour, actor


def basic(reader):
    # the contour filter
    contour = vtk.vtkContourFilter()
    contour.SetValue(0, 1000)
    contour.SetInputConnection(reader.GetOutputPort())

    # mapper and actor
    mapper = vtk.vtkDataSetMapper()
    mapper.SetInputConnection(contour.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    return contour, actor


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName('The Main Window')
        MainWindow.setWindowTitle('salient_flame')

        self.centralWidget = QWidget(MainWindow)
        self.gridlayout = QGridLayout(self.centralWidget)
        self.vtkWidget = QVTKRenderWindowInteractor(self.centralWidget)

        self.slider_contour0 = QSlider()
        self.slider_contour1 = QSlider()
        self.slider_opacity0 = QSlider()
        self.slider_opacity1 = QSlider()

        self.gridlayout.addWidget(self.vtkWidget, 0, 0, 4, 4)

        self.gridlayout.addWidget(QLabel("Contour0 Value"), 4, 0, 1, 1)
        self.gridlayout.addWidget(self.slider_contour0, 4, 1, 1, 1)

        self.gridlayout.addWidget(QLabel("Contour1 Value"), 4, 2, 1, 1)
        self.gridlayout.addWidget(self.slider_contour1, 4, 3, 1, 1)

        self.gridlayout.addWidget(QLabel("Contour0 Opacity"), 5, 0, 1, 1)
        self.gridlayout.addWidget(self.slider_opacity0, 5, 1, 1, 1)

        self.gridlayout.addWidget(QLabel("Contour1 Opacity"), 5, 2, 1, 1)
        self.gridlayout.addWidget(self.slider_opacity1, 5, 3, 1, 1)

        MainWindow.setCentralWidget(self.centralWidget)


class IsosurfaceDemo(QMainWindow):

    def __init__(self, margs, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        filename = margs.file                # flame dataset file name
        self.contourVal = INIT_CONTOUR_VAL   # initial contour value
        self.frame_counter = 0

        self.reader, self.ren = makeBasic(filename)
        self.contours = list()
        self.actors = list()

        for d in REN_DATA:
            contour, actor = make(self.reader, d)
            self.ren.AddActor(actor)
            self.actors.append(actor)
            self.contours.append(contour)

        self.ui.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.ui.vtkWidget.GetRenderWindow().GetInteractor()
        self.iren.AddObserver("KeyPressEvent", self.key_pressed_callback)

        def slider_setup(slider, val, bounds, interv):
            slider.setOrientation(QtCore.Qt.Horizontal)
            slider.setValue(float(val))
            slider.setTracking(False)
            slider.setTickInterval(interv)
            slider.setTickPosition(QSlider.TicksAbove)
            slider.setRange(bounds[0], bounds[1])

        # need to adjust the range of slide bars because the initial position of widget would be wrong
        # if init val > 100
        slider_contour_range = [0, (MAX_CONTOUR_VAL - INIT_CONTOUR_VAL) / 1000]
        slider_setup(self.ui.slider_contour0, (REN_DATA[2][0] - INIT_CONTOUR_VAL)/1000, slider_contour_range, 1)
        slider_setup(self.ui.slider_contour1, (REN_DATA[3][0] - INIT_CONTOUR_VAL)/1000, slider_contour_range, 1)
        slider_setup(self.ui.slider_opacity0, REN_DATA[2][4]*10, [0, 10], 1)
        slider_setup(self.ui.slider_opacity1, REN_DATA[3][4]*10, [0, 10], 1)


    def contour0_callback(self, val):
        cval = val * 1000 + INIT_CONTOUR_VAL
        print("contour0: " + str(cval))
        self.contours[2].SetValue(0, cval)
        self.ui.vtkWidget.GetRenderWindow().Render()

    def contour1_callback(self, val):
        cval = val * 1000 + INIT_CONTOUR_VAL
        print("contour1: " + str(cval))
        self.contours[3].SetValue(0, cval)
        self.ui.vtkWidget.GetRenderWindow().Render()

    def opacity0_callback(self, val):
        self.actors[2].GetProperty().SetOpacity(val / 10)
        self.ui.vtkWidget.GetRenderWindow().Render()

    def opacity1_callback(self, val):
        self.actors[3].GetProperty().SetOpacity(val / 10)
        self.ui.vtkWidget.GetRenderWindow().Render()

    def key_pressed_callback(self, obj, event):
        key = obj.GetKeySym()
        if key == "s":
            # save frame
            file_name = "salient_flame_frame" + str(self.frame_counter).zfill(5) + ".png"
            window = self.ui.vtkWidget.GetRenderWindow()
            image = vtk.vtkWindowToImageFilter()
            image.SetInput(window)
            png_writer = vtk.vtkPNGWriter()
            png_writer.SetInputConnection(image.GetOutputPort())
            png_writer.SetFileName(file_name)
            window.Render()
            png_writer.Write()
            self.frame_counter += 1
        elif key == "c":
            # print camera setting
            camera = self.ren.GetActiveCamera()
            print("Camera settings:")
            print("  * position:        %s" % (camera.GetPosition(),))
            print("  * focal point:     %s" % (camera.GetFocalPoint(),))
            print("  * up vector:       %s" % (camera.GetViewUp(),))
            print("  * clipping range:  %s" % (camera.GetClippingRange(),))


if __name__ == "__main__":

    # --define argument parser and parse arguments--
    parser = argparse.ArgumentParser(
        description="Parser for flame_head")
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
    window.ui.slider_contour0.valueChanged.connect(window.contour0_callback)
    window.ui.slider_contour1.valueChanged.connect(window.contour1_callback)
    window.ui.slider_opacity0.valueChanged.connect(window.opacity0_callback)
    window.ui.slider_opacity1.valueChanged.connect(window.opacity1_callback)

    sys.exit(app.exec_())
