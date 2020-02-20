#!/usr/bin/env python

# CS 530
# Project 2 Task 3
# Luke Jiang
# 02/13/2020

""" Description:
Use the gradient magnitude data to filter out unwanted portions of your isosurfaces.
Use two vtkClipData filters, one for gradmax and one for gradmin

Command line interface: python iso2dtf.py <data> <gradma> [--val <val>] [--clip <X> <Y> <Z>]
    <data>:     3D scalar dataset to visualize
    <gradma>:   gradient magnitide
    <val>:      initial isocontour value (optional)
    <X>:        initial position of the clipping plane in x-axis (optional)
    <Y>:        initial position of the clipping plane in y-axis (optional)
    <Z>:        initial position of the clipping plane in z-axis (optional)
"""

import vtk
import sys
import argparse

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSlider, QGridLayout, QLabel
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

GRAD_MAX = 109404           # maximum of gradient magnitude dataset


def make(ct_name, gm_name, contourVal, gradmin, gradmax):
    ct = vtk.vtkXMLImageDataReader()
    ct.SetFileName(ct_name)
    ct.Update()

    gm = vtk.vtkXMLImageDataReader()
    gm.SetFileName(gm_name)
    gm.Update()

    ctContour = vtk.vtkContourFilter()
    ctContour.SetValue(0, contourVal)
    ctContour.SetInputConnection(ct.GetOutputPort())

    planeX = vtk.vtkPlane()
    planeX.SetOrigin(0, 0, 0)
    planeX.SetNormal(1.0, 0, 0)
    clipperX = vtk.vtkClipPolyData()
    clipperX.SetInputConnection(ctContour.GetOutputPort())
    clipperX.SetClipFunction(planeX)

    planeY = vtk.vtkPlane()
    planeY.SetOrigin(0, 0, 0)
    planeY.SetNormal(0, 1.0, 0)
    clipperY = vtk.vtkClipPolyData()
    clipperY.SetInputConnection(clipperX.GetOutputPort())
    clipperY.SetClipFunction(planeY)

    planeZ = vtk.vtkPlane()
    planeZ.SetOrigin(0, 0, 0)
    planeZ.SetNormal(0, 0, 1.0)
    clipperZ = vtk.vtkClipPolyData()
    clipperZ.SetInputConnection(clipperY.GetOutputPort())
    clipperZ.SetClipFunction(planeZ)

    probe = vtk.vtkProbeFilter()
    probe.SetSourceConnection(gm.GetOutputPort())
    probe.SetInputConnection(clipperZ.GetOutputPort())

    minClip = vtk.vtkClipPolyData()
    minClip.SetInputConnection(probe.GetOutputPort())
    minClip.InsideOutOff()
    minClip.SetValue(gradmin)

    maxClip = vtk.vtkClipPolyData()
    maxClip.SetInputConnection(minClip.GetOutputPort())
    maxClip.InsideOutOn()
    maxClip.SetValue(gradmax)

    # TODO: make color map looks better
    colorTrans = vtk.vtkColorTransferFunction()
    colorTrans.SetColorSpaceToRGB()
    colorTrans.AddRGBPoint(0, 1, 1, 1)
    colorTrans.AddRGBPoint(2500, 1, 1, 1)
    colorTrans.AddRGBPoint(109404, 1, 0, 0)


    mapper = vtk.vtkDataSetMapper()
    mapper.SetInputConnection(maxClip.GetOutputPort())
    mapper.SetLookupTable(colorTrans)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    colorBar = vtk.vtkScalarBarActor()
    colorBar.SetOrientationToHorizontal()
    colorBar.SetLookupTable(colorTrans)

    colorBarWidget = vtk.vtkScalarBarWidget()
    colorBarWidget.SetScalarBarActor(colorBar)

    return ctContour, planeX, planeY, planeZ, minClip, maxClip, actor, colorBarWidget


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName('The Main Window')
        MainWindow.setWindowTitle('isosurface')

        self.centralWidget = QWidget(MainWindow)
        self.gridlayout = QGridLayout(self.centralWidget)
        self.vtkWidget = QVTKRenderWindowInteractor(self.centralWidget)

        self.slider_clipX = QSlider()
        self.slider_clipY = QSlider()
        self.slider_clipZ = QSlider()
        self.slider_contour = QSlider()
        self.slider_gradmax = QSlider()
        self.slider_gradmin = QSlider()

        self.gridlayout.addWidget(self.vtkWidget, 0, 0, 4, 4)

        self.gridlayout.addWidget(QLabel("Clip X"), 4, 0, 1, 1)
        self.gridlayout.addWidget(self.slider_clipX, 4, 1, 1, 1)

        self.gridlayout.addWidget(QLabel("Clip Y"), 4, 2, 1, 1)
        self.gridlayout.addWidget(self.slider_clipY, 4, 3, 1, 1)

        self.gridlayout.addWidget(QLabel("Clip Z"), 5, 0, 1, 1)
        self.gridlayout.addWidget(self.slider_clipZ, 5, 1, 1, 1)

        self.gridlayout.addWidget(QLabel("Isovalue"), 5, 2, 1, 1)
        self.gridlayout.addWidget(self.slider_contour, 5, 3, 1, 1)

        self.gridlayout.addWidget(QLabel("Gradient Max"), 6, 0, 1, 1)
        self.gridlayout.addWidget(self.slider_gradmax, 6, 1, 1, 1)

        self.gridlayout.addWidget(QLabel("Gradient Min"), 6, 2, 1, 1)
        self.gridlayout.addWidget(self.slider_gradmin, 6, 3, 1, 1)

        MainWindow.setCentralWidget(self.centralWidget)


class IsosurfaceDemo(QMainWindow):

    def __init__(self, margs, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.clipX = margs.clip[0]          # default clipX position
        self.clipY = margs.clip[1]          # default clipY position
        self.clipZ = margs.clip[2]          # default clipZ position
        self.contourVal = margs.val         # default isosurface value
        self.gradmin = 0                    # default minimum gradient
        self.gradmax = GRAD_MAX             # default maximum gradient
        ct_name = margs.data                # CT file name
        gm_name = margs.gradmag             # gradient magnitude file name

        [self.contour, self.planeX, self.planeY, self.planeZ, self.minClip, self.maxClip,
         self.actor, self.colorBarWidget] = make(ct_name, gm_name, self.contourVal, self.gradmin, self.gradmax)

        self.ren = vtk.vtkRenderer()
        self.ren.AddActor(self.actor)
        self.ren.SetBackground(0.75, 0.75, 0.75)
        self.ren.ResetCamera()

        self.ui.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.ui.vtkWidget.GetRenderWindow().GetInteractor()

        self.colorBarWidget.SetInteractor(self.iren)
        self.colorBarWidget.On()


        def slider_setup(slider, val, bounds, interv):
            slider.setOrientation(QtCore.Qt.Horizontal)
            slider.setValue(float(val))
            slider.setTracking(False)
            slider.setTickInterval(interv)
            slider.setTickPosition(QSlider.TicksAbove)
            slider.setRange(bounds[0], bounds[1])

        # define range and initial value for each slider bar
        slider_setup(self.ui.slider_clipX, self.clipX, [0, 200], 5)
        slider_setup(self.ui.slider_clipY, self.clipY, [0, 200], 5)
        slider_setup(self.ui.slider_clipZ, self.clipZ, [0, 200], 5)
        slider_setup(self.ui.slider_contour, self.contourVal/25, [500/25, 1500/25], 1)
        slider_setup(self.ui.slider_gradmin, 0, [0, GRAD_MAX/1000], 1)
        slider_setup(self.ui.slider_gradmax, GRAD_MAX/1000, [0, GRAD_MAX/1000], 1)


    def clipX_callback(self, val):
        self.clipX = val
        self.planeX.SetOrigin(val, 0, 0)
        self.ui.vtkWidget.GetRenderWindow().Render()

    def clipY_callback(self, val):
        self.clipY = val
        self.planeY.SetOrigin(0, val, 0)
        self.ui.vtkWidget.GetRenderWindow().Render()

    def clipZ_callback(self, val):
        self.clipZ = val
        self.planeZ.SetOrigin(0, 0, val)
        self.ui.vtkWidget.GetRenderWindow().Render()

    def contour_callback(self, val):
        print("contour: " + str(val*25))
        self.contourVal = val*25
        self.contour.SetValue(0, self.contourVal)
        self.ui.vtkWidget.GetRenderWindow().Render()

    def gradmin_callback(self, val):
        print("gradmin: " + str(val*1000))
        self.gradmin = val*1000
        self.minClip.SetValue(val*1000)
        self.ui.vtkWidget.GetRenderWindow().Render()

    def gradmax_callback(self, val):
        print("gradmax: " + str(val*1000))
        self.gradmax = val*1000
        self.maxClip.SetValue(val*1000)
        self.ui.vtkWidget.GetRenderWindow().Render()


if __name__ == "__main__":
    # --define argument parser and parse arguments--
    parser = argparse.ArgumentParser()
    parser.add_argument('data')
    parser.add_argument('gradmag')
    parser.add_argument('--val', type=int, metavar='int', default=500)
    parser.add_argument('--clip', type=int, metavar='int', nargs=3,
                        help='initial positions of clipping planes', default=[0, 0, 0])
    args = parser.parse_args()

    # --main app--
    app = QApplication(sys.argv)
    window = IsosurfaceDemo(margs=args)
    window.ui.vtkWidget.GetRenderWindow().SetSize(800, 800)
    window.show()
    window.setWindowState(Qt.WindowMaximized)
    window.iren.Initialize()

    # --hook up callbacks--
    window.ui.slider_clipX.valueChanged.connect(window.clipX_callback)
    window.ui.slider_clipY.valueChanged.connect(window.clipY_callback)
    window.ui.slider_clipZ.valueChanged.connect(window.clipZ_callback)
    window.ui.slider_contour.valueChanged.connect(window.contour_callback)
    window.ui.slider_gradmin.valueChanged.connect(window.gradmin_callback)
    window.ui.slider_gradmax.valueChanged.connect(window.gradmax_callback)

    sys.exit(app.exec_())
