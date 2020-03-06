#!/usr/bin/env python

# CS 530
# Project 3 Task 2
# Luke Jiang
# 03/02/2020

""" Description:
Use volume rendering to render the flame dataset

Command line interface: python dvr_flame.py <flame.vti>

"""


import vtk
import sys
import argparse

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QGridLayout
from PyQt5.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


# color transfer function
# format: [isovalue, R, G, B]
CTF = [[16000, 50, 50, 255],
       [25000, 100, 100, 255],
       [30000, 255, 163, 0],
       [31000, 155, 163, 0],
       [52000, 255, 242, 242],
       [62000, 255, 27, 27]]

# opacity transfer function
# format: [isovalue, opacity]
OTF = [[0,      0],
       [15999,  0],
       [16000,  0.4],
       [25000,  0.4],
       [30000,  0.1],
       [31000,  0.1],
       [52000,  0.4],
       [63000,  0.4],
       [63001,  0.0]]

SAMP_DIST = 0.25

# camera settings
CAM = [[216, 958, 751],         # position
       [239, 359, 59],          # focal point
       [0.66, 0.58, -0.48],     # up vector
       [389, 1644]]             # clipping range


def make(filename):
    # read the head image
    reader = vtk.vtkXMLImageDataReader()
    reader.SetFileName(filename)
    reader.Update()

    # define the color map
    colorTrans = vtk.vtkColorTransferFunction()
    colorTrans.SetColorSpaceToRGB()
    for [isoVal, R, G, B] in CTF:
        colorTrans.AddRGBPoint(isoVal, R/256, G/256, B/256)

    # define the opacity transfer function
    opacityTrans = vtk.vtkPiecewiseFunction()
    for [isoVal, o] in OTF:
        opacityTrans.AddPoint(isoVal, o)

    # define volume property
    vProp = vtk.vtkVolumeProperty()
    vProp.SetColor(colorTrans)
    vProp.SetScalarOpacity(opacityTrans)
    vProp.SetInterpolationTypeToLinear()
    vProp.ShadeOff()

    mapper = vtk.vtkSmartVolumeMapper()
    mapper.SetInputConnection(reader.GetOutputPort())
    mapper.AutoAdjustSampleDistancesOff()
    mapper.SetSampleDistance(0.25)

    volume = vtk.vtkVolume()
    volume.SetMapper(mapper)
    volume.SetProperty(vProp)

    # enable depth peeling in renderer
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.45, 0.45, 0.45)
    ren.AddVolume(volume)
    ren.ResetCamera()

    return ren, mapper


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName('The Main Window')
        MainWindow.setWindowTitle('salient_flame')

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

        filename = margs.file
        self.frame_counter = 0

        self.ren, self.mapper = make(filename)
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
            file_name = "dvr_flame_" + str(self.frame_counter).zfill(5) + ".png"
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
    parser = argparse.ArgumentParser()
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
