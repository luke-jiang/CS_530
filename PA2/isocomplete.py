#!/usr/bin/env python

import vtk
import sys
import argparse

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSlider, QGridLayout, QLabel
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

GRAD_MAX = 109404           # maximum of gradient magnitude dataset

DATA = [[800, 19000, 69000, 197, 140, 133],
        [1100, 10000, 49000, 204, 71, 62],
        [1300, 0, 72000, 230, 230, 230]]


def make(ct_name, gm_name, data):
    ct = vtk.vtkXMLImageDataReader()
    ct.SetFileName(ct_name)
    ct.Update()

    gm = vtk.vtkXMLImageDataReader()
    gm.SetFileName(gm_name)
    gm.Update()

    ctContour = vtk.vtkContourFilter()
    i = 0
    for d in data:
        ctContour.SetValue(i, d[0])
        i += 1
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


    # minClip = vtk.vtkClipPolyData()
    # minClip.SetInputConnection(probe.GetOutputPort())
    # minClip.InsideOutOff()
    # for d in data:
    #     minClip.SetValue(d[1])
    #
    # maxClip = vtk.vtkClipPolyData()
    # maxClip.SetInputConnection(minClip.GetOutputPort())
    # maxClip.InsideOutOn()
    # for d in data:
    #     maxClip.SetValue(d[2])

    # TODO: make color map looks better
    colorTrans = vtk.vtkColorTransferFunction()
    colorTrans.SetColorSpaceToRGB()
    for d in data:
        colorTrans.AddRGBPoint(d[0], d[3]/256, d[4]/256, d[5]/256)


    mapper = vtk.vtkDataSetMapper()
    mapper.SetInputConnection(clipperZ.GetOutputPort())
    mapper.SetLookupTable(colorTrans)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    # colorBar = vtk.vtkScalarBarActor()
    # colorBar.SetOrientationToHorizontal()
    # colorBar.SetLookupTable(colorTrans)
    #
    # colorBarWidget = vtk.vtkScalarBarWidget()
    # colorBarWidget.SetScalarBarActor(colorBar)

    return ctContour, planeX, planeY, planeZ, actor


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

        self.gridlayout.addWidget(self.vtkWidget, 0, 0, 4, 4)

        self.gridlayout.addWidget(QLabel("Clip X"), 4, 0, 1, 1)
        self.gridlayout.addWidget(self.slider_clipX, 4, 1, 1, 1)

        self.gridlayout.addWidget(QLabel("Clip Y"), 4, 2, 1, 1)
        self.gridlayout.addWidget(self.slider_clipY, 4, 3, 1, 1)

        self.gridlayout.addWidget(QLabel("Clip Z"), 5, 0, 1, 1)
        self.gridlayout.addWidget(self.slider_clipZ, 5, 1, 1, 1)

        MainWindow.setCentralWidget(self.centralWidget)


class IsosurfaceDemo(QMainWindow):

    def __init__(self, margs, data, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.clipX = margs.clip[0]          # default clipX position
        self.clipY = margs.clip[1]          # default clipY position
        self.clipZ = margs.clip[2]          # default clipZ position
        ct_name = margs.data                # CT file name
        gm_name = margs.gradmag             # gradient magnitude file name

        [self.contour, self.planeX, self.planeY, self.planeZ, self.actor] = make(ct_name, gm_name, data)

        self.ren = vtk.vtkRenderer()
        self.ren.AddActor(self.actor)
        self.ren.SetBackground(0.75, 0.75, 0.75)
        self.ren.ResetCamera()

        self.ui.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.ui.vtkWidget.GetRenderWindow().GetInteractor()


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



if __name__ == "__main__":
    # --define argument parser and parse arguments--
    parser = argparse.ArgumentParser()
    parser.add_argument('data')
    parser.add_argument('gradmag')
    parser.add_argument('params')
    parser.add_argument('--clip', type=int, metavar='int', nargs=3,
                        help='initial positions of clipping planes', default=[0, 0, 0])
    args = parser.parse_args()


    # --main app--
    app = QApplication(sys.argv)
    window = IsosurfaceDemo(margs=args, data=DATA)
    window.ui.vtkWidget.GetRenderWindow().SetSize(800, 800)
    window.show()
    window.setWindowState(Qt.WindowMaximized)
    window.iren.Initialize()

    # --hook up callbacks--
    window.ui.slider_clipX.valueChanged.connect(window.clipX_callback)
    window.ui.slider_clipY.valueChanged.connect(window.clipY_callback)
    window.ui.slider_clipZ.valueChanged.connect(window.clipZ_callback)

    sys.exit(app.exec_())