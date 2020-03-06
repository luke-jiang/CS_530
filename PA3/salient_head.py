#!/usr/bin/env python

# CS 530
# Project 3 Task 1
# Luke Jiang
# 03/02/2020

""" Description:
Find and display salient isosurfaces of the head dataset
(namely, boundaries between skin, muscle, and skull)

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
from PyQt5.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


REN_DATA = [[500, 197, 140, 133, 0.6],
            [1030, 204, 71, 62, 0.7],
            [1140, 230, 230, 230, 1.0]]


# camera settings
CAM = [[781, -214, 78],             # position
       [134, 134, 146],             # focal point
       [0.079, 0.328, -0.941],      # up vector
       [342, 1237]]                 # clipping range

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

    return contour, actor


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName('The Main Window')
        MainWindow.setWindowTitle('salient_head')

        self.centralWidget = QWidget(MainWindow)
        self.gridlayout = QGridLayout(self.centralWidget)
        self.vtkWidget = QVTKRenderWindowInteractor(self.centralWidget)

        self.gridlayout.addWidget(self.vtkWidget, 0, 0, 4, 4)

        MainWindow.setCentralWidget(self.centralWidget)


class IsosurfaceDemo(QMainWindow):

    def __init__(self, margs, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        filename = margs.file                # head dataset file name
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

        # set camera position
        self.camera = self.ren.GetActiveCamera()
        self.camera.SetPosition(CAM[0][0], CAM[0][1], CAM[0][2])
        self.camera.SetFocalPoint(CAM[1][0], CAM[1][1], CAM[1][2])
        self.camera.SetViewUp(CAM[2])
        self.camera.SetClippingRange(CAM[3])

        self.iren.AddObserver("KeyPressEvent", self.key_pressed_callback)

    def key_pressed_callback(self, obj, event):
        key = obj.GetKeySym()
        if key == "s":
            # save frame
            file_name = "salient_head" + str(self.frame_counter).zfill(5) + ".png"
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

    sys.exit(app.exec_())
