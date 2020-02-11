#!/usr/bin/env python

import vtk
import sys
import argparse

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSlider, QGridLayout, QLabel, QPushButton
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


def make(ct_name, gm_name, isoValues, colormap_data):
    ct = vtk.vtkXMLImageDataReader()
    ct.SetFileName(ct_name)
    ct.Update()

    gm = vtk.vtkXMLImageDataReader()
    gm.SetFileName(gm_name)
    gm.Update()
    print(gm.GetOutput().GetPointData().GetArray(0).GetRange())  # Get data range

    # TODO: Add muscle contour value
    ctContour = vtk.vtkContourFilter()
    i = 0
    for v in isoValues:
        ctContour.SetValue(i, v)
        i += 1
    # ctContour.SetValue(0, 550)
    # ctContour.SetValue(1, 1349)
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
    probe.SetSourceConnection(gm.GetOutputPort()) #
    probe.SetInputConnection(clipperZ.GetOutputPort())

    # TODO: make color map looks better
    colorTrans = vtk.vtkColorTransferFunction()
    colorTrans.SetColorSpaceToRGB()
    for c in colormap_data:
        colorTrans.AddRGBPoint(c[0], c[1], c[2], c[3])
    # colorTrans.AddRGBPoint(0, 1, 1, 1)
    # colorTrans.AddRGBPoint(2500, 1, 1, 1)
    # colorTrans.AddRGBPoint(109404, 1, 0, 0)


    mapper = vtk.vtkDataSetMapper()
    mapper.SetInputConnection(probe.GetOutputPort())
    mapper.SetLookupTable(colorTrans)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    colorBar = vtk.vtkScalarBarActor()
    colorBar.SetOrientationToHorizontal()
    colorBar.SetLookupTable(colorTrans)

    colorBarWidget = vtk.vtkScalarBarWidget()
    colorBarWidget.SetScalarBarActor(colorBar)

    return planeX, planeY, planeZ, actor, colorBarWidget


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

    def __init__(self, margs, colormap, isoValues, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.clipX = margs.clip[0]
        self.clipY = margs.clip[1]
        self.clipZ = margs.clip[2]

        # ct_name = "vffeet-ct-small.vti"
        # gm_name = "vffeet-gm-small.vti"

        ct_name = margs.data
        gm_name = margs.gradmag

        [self.planeX, self.planeY, self.planeZ, self.actor, self.colorBarWidget] = \
            make(ct_name, gm_name, isoValues, colormap)
        self.ren = vtk.vtkRenderer()
        self.ren.AddActor(self.actor)
        self.ren.SetBackground(0.75, 0.75, 0.75)
        self.ren.ResetCamera()
        # self.ren.GetActiveCamera().Azimuth(180)
        # self.ren.GetActiveCamera().Roll(180)
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
    parser = argparse.ArgumentParser()
    parser.add_argument('data')
    parser.add_argument('gradmag')
    parser.add_argument('isoVal')
    parser.add_argument('--cmap', type=str, metavar='filename', help='input colormap file',
                        default='NULL')
    parser.add_argument('--clip', type=int, metavar='int', nargs=3,
                        help='initial positions of clipping planes', default=[0, 0, 0])

    args = parser.parse_args()

    # process colormap argument
    default_colormap = [[0, 1, 1, 1], [2500, 1, 1, 1], [109404, 1, 0, 0]]
    colormap = args.cmap
    if colormap != 'NULL':
        default_colormap.clear()
        with open(colormap, 'r') as fd:
            lines = fd.read().splitlines()
            for line in lines:
                if len(line) > 0 and line[0] != '#':
                    l = [int(i) for i in line.split()]
                    default_colormap.append(l)
    # print(default_colormap)

    # process isovalue argument
    isoValues = list()  # [550, 1349]
    with open(args.isoVal, 'r') as fd:
        line = fd.read().split()
        isoValues = [int(i) for i in line]
    # print(isoValues)

    # main app
    app = QApplication(sys.argv)
    window = IsosurfaceDemo(margs=args, colormap=default_colormap, isoValues=isoValues)
    window.ui.vtkWidget.GetRenderWindow().SetSize(800, 800)
    window.show()
    window.setWindowState(Qt.WindowMaximized)
    window.iren.Initialize()

    window.ui.slider_clipX.valueChanged.connect(window.clipX_callback)
    window.ui.slider_clipY.valueChanged.connect(window.clipY_callback)
    window.ui.slider_clipZ.valueChanged.connect(window.clipZ_callback)

    sys.exit(app.exec_())
