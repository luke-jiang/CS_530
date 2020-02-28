#!/usr/bin/env python

# CS 530
# Project 3 Task 2
# Luke Jiang
# 02/21/2020


import vtk
import sys
import argparse

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSlider, QGridLayout, QLabel, QPushButton
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

# valid range of isovalues
INIT_CONTOUR_VAL = 700
MAX_CONTOUR_VAL = 1200

# [isovalue, R, G, B, opacity]
REN_DATA = [[1010, 197, 140, 133, 0.4],
            [1080, 230, 230, 230, 1.0]]



def makeBasic(filename):
    # read the head image
    reader = vtk.vtkXMLImageDataReader()
    reader.SetFileName(filename)
    reader.Update()

    # enable depth peeling in renderer
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.75, 0.75, 0.75)
    # ren.SetUseDepthPeeling(1)
    # ren.SetMaximumNumberOfPeels(100)
    # ren.SetOcclusionRatio(0.4)
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
    colorTrans.AddRGBPoint(isoValue, R / 256, G / 256, B / 256)

    # define the opacity transfer function
    # opacityTrans = vtk.vtkPiecewiseFunction()
    # opacityTrans.AddPoint(1080, 1.0)
    # opacityTrans.AddPoint(1010, 0.4)

    # define volume property
    vProp = vtk.vtkVolumeProperty()
    vProp.SetColor(colorTrans)
    # vProp.SetScalarOpacity(opacityTrans)
    vProp.SetInterpolationTypeToLinear()
    vProp.ShadeOn()

    mapper = vtk.vtkSmartVolumeMapper()
    mapper.SetInputConnection(reader.GetOutputPort())

    volume = vtk.vtkVolume()
    volume.SetMapper(mapper)
    volume.SetProperty(vProp)

    return contour, volume


def make1(filename):
    # read the head image
    reader = vtk.vtkXMLImageDataReader()
    reader.SetFileName(filename)
    reader.Update()

    # define the color map
    colorTrans = vtk.vtkColorTransferFunction()
    colorTrans.SetColorSpaceToRGB()
    colorTrans.AddRGBPoint(1010, 197/256, 140/256, 133/256)
    colorTrans.AddRGBPoint(1080, 230/256, 230/256, 230/256)

    # define the opacity transfer function
    opacityTrans = vtk.vtkPiecewiseFunction()
    opacityTrans.AddPoint(0, 0)
    opacityTrans.AddPoint(1000, 0)
    opacityTrans.AddPoint(1010, 0.4)
    opacityTrans.AddPoint(1080, 0.1)


    # define volume property
    vProp = vtk.vtkVolumeProperty()
    vProp.SetColor(colorTrans)
    vProp.SetScalarOpacity(opacityTrans)
    vProp.SetInterpolationTypeToLinear()
    vProp.ShadeOn()

    mapper = vtk.vtkSmartVolumeMapper()
    mapper.SetInputConnection(reader.GetOutputPort())

    volume = vtk.vtkVolume()
    volume.SetMapper(mapper)
    volume.SetProperty(vProp)

    # enable depth peeling in renderer
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.75, 0.75, 0.75)
    ren.AddVolume(volume)
    # ren.SetUseDepthPeeling(1)
    # ren.SetMaximumNumberOfPeels(100)
    # ren.SetOcclusionRatio(0.4)
    ren.ResetCamera()

    return ren



class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName('The Main Window')
        MainWindow.setWindowTitle('salient_head')

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

        # self.gridlayout.addWidget(QLabel("Contour0 Opacity"), 5, 0, 1, 1)
        # self.gridlayout.addWidget(self.slider_opacity0, 5, 1, 1, 1)
        #
        # self.gridlayout.addWidget(QLabel("Contour1 Opacity"), 5, 2, 1, 1)
        # self.gridlayout.addWidget(self.slider_opacity1, 5, 3, 1, 1)

        MainWindow.setCentralWidget(self.centralWidget)


class IsosurfaceDemo(QMainWindow):

    def __init__(self, margs, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        filename = margs.file                # head dataset file name
        self.contourVal = INIT_CONTOUR_VAL   # initial contour value
        self.frame_counter = 0

        # self.reader, self.ren = makeBasic(filename)
        # self.contours = list()
        # self.volumes = list()
        # for d in REN_DATA:
        #     contour, volume = make(self.reader, d)
        #     self.ren.AddVolume(volume)
        #     self.volumes.append(volume)
        #     self.contours.append(contour)
        #
        # self.ui.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        # self.iren = self.ui.vtkWidget.GetRenderWindow().GetInteractor()
        # self.iren.AddObserver("KeyPressEvent", self.key_pressed_callback)

        self.ren = make1(filename)
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
        slider_contour_range = [0, (MAX_CONTOUR_VAL - INIT_CONTOUR_VAL) / 10]
        slider_setup(self.ui.slider_contour0, (REN_DATA[0][0] - INIT_CONTOUR_VAL)/10, slider_contour_range, 1)
        slider_setup(self.ui.slider_contour1, (REN_DATA[1][0] - INIT_CONTOUR_VAL)/10, slider_contour_range, 1)
        slider_setup(self.ui.slider_opacity0, REN_DATA[0][4]*10, [0, 10], 1)
        slider_setup(self.ui.slider_opacity1, REN_DATA[1][4]*10, [0, 10], 1)

    # def contour0_callback(self, val):
    #     cval = val * 10 + INIT_CONTOUR_VAL
    #     print("contour0: " + str(cval))
    #     self.contours[0].SetValue(0, cval)
    #     self.ui.vtkWidget.GetRenderWindow().Render()
    #
    # def contour1_callback(self, val):
    #     cval = val * 10 + INIT_CONTOUR_VAL
    #     print("contour1: " + str(cval))
    #     self.contours[1].SetValue(0, cval)
    #     self.ui.vtkWidget.GetRenderWindow().Render()

    # def opacity0_callback(self, val):
    #     self.actors[0].GetProperty().SetOpacity(val / 10)
    #     self.ui.vtkWidget.GetRenderWindow().Render()
    #
    # def opacity1_callback(self, val):
    #     self.actors[1].GetProperty().SetOpacity(val / 10)
    #     self.ui.vtkWidget.GetRenderWindow().Render()

    def key_pressed_callback(self, obj, event):
        key = obj.GetKeySym()
        if key == "s":
            # save frame
            file_name = "salient_head_frame" + str(self.frame_counter).zfill(5) + ".png"
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

    # --hook up callbacks--
    # window.ui.slider_contour0.valueChanged.connect(window.contour0_callback)
    # window.ui.slider_contour1.valueChanged.connect(window.contour1_callback)
    # window.ui.slider_opacity0.valueChanged.connect(window.opacity0_callback)
    # window.ui.slider_opacity1.valueChanged.connect(window.opacity1_callback)

    sys.exit(app.exec_())
