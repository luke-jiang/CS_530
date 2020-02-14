#!/usr/bin/env python

# CS 530
# Project 2 Task 2
# Luke Jiang
# 02/11/2020

""" Description:
Color map the value of gradient magnitude to a list of given isosurfaces.

Command line interface: python isogm.py <data> <gradmag> <isoval> [--cmap <colors>] [--clip <X> <Y> <Z>]
    <data>:     3D scalar dataset to visualize
    <gradma>:   gradient magnitide
    <isoval>:   name of a .txt file containing the isovalues to use
    <colors>:   name of a .txt file containing a color map definition (optional)
    <X>:        initial position of the clipping plane in x-axis (optional)
    <Y>:        initial position of the clipping plane in y-axis (optional)
    <Z>:        initial position of the clipping plane in z-axis (optional)
"""

""" Observations:
The bones have low gradient magnitude, the skin has high gradient magnitude, muscles in between.
"""


import vtk
import sys
import argparse

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSlider, QGridLayout, QLabel, QPushButton
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

# default values
DEFAULT_COLORMAP = [[0, 1, 1, 1], [2500, 1, 1, 1], [109404, 1, 0, 0]]
DEFAULT_PLANE_POS = [0, 0, 0]


def make(ct_name, gm_name, isoValues, colormap_data):
    # read the CT file
    ct = vtk.vtkXMLImageDataReader()
    ct.SetFileName(ct_name)
    ct.Update()

    # read the gradient magnitude file
    gm = vtk.vtkXMLImageDataReader()
    gm.SetFileName(gm_name)
    gm.Update()
    # print(gm.GetOutput().GetPointData().GetArray(0).GetRange())  # Get data range

    # extract isosurfaces given contour isovalues
    ctContour = vtk.vtkContourFilter()
    i = 0
    for v in isoValues:
        ctContour.SetValue(i, v)
        i += 1
    ctContour.SetInputConnection(ct.GetOutputPort())

    # three clipping planes
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

    # resample the gradient magnitude on isosurfaces (assicoate
    # each vertex of the isosurfaces to corresponding gradient magnitude)
    probe = vtk.vtkProbeFilter()
    probe.SetSourceConnection(gm.GetOutputPort())
    probe.SetInputConnection(clipperZ.GetOutputPort())

    # define the color map
    colorTrans = vtk.vtkColorTransferFunction()
    colorTrans.SetColorSpaceToRGB()
    for c in colormap_data:
        colorTrans.AddRGBPoint(c[0], c[1], c[2], c[3])

    # color bar to display the color scale
    colorBar = vtk.vtkScalarBarActor()
    colorBar.SetOrientationToHorizontal()
    colorBar.SetLookupTable(colorTrans)

    colorBarWidget = vtk.vtkScalarBarWidget()
    colorBarWidget.SetScalarBarActor(colorBar)

    # mapper and actor
    mapper = vtk.vtkDataSetMapper()
    mapper.SetInputConnection(probe.GetOutputPort())
    mapper.SetLookupTable(colorTrans)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

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

        self.clipX = margs.clip[0]          # default clipX position
        self.clipY = margs.clip[1]          # default clipY position
        self.clipZ = margs.clip[2]          # default clipZ position
        ct_name = margs.data                # CT file name
        gm_name = margs.gradmag

        [self.planeX, self.planeY, self.planeZ, self.actor, self.colorBarWidget] = \
            make(ct_name, gm_name, isoValues, colormap)

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
    parser.add_argument('isoVal')
    parser.add_argument('--cmap', type=str, metavar='filename', help='input colormap file', default='NULL')
    parser.add_argument('--clip', type=int, metavar='int', nargs=3,
                        help='initial positions of clipping planes', default=DEFAULT_PLANE_POS)
    args = parser.parse_args()

    # --process colormap argument--
    colormap = DEFAULT_COLORMAP
    colormapFile = args.cmap
    if colormapFile != 'NULL':
        colormap.clear()
        with open(colormapFile, 'r') as fd:
            lines = fd.read().splitlines()
            for line in lines:
                if len(line) > 0 and line[0] != '#':
                    intline = [int(i) for i in line.split()]
                    colormap.append(intline)
    # print(colormap)

    # --process isovalue argument--
    isoValues = list()  # [550, 1349]
    with open(args.isoVal, 'r') as fd:
        line = fd.read().split()
        isoValues = [int(i) for i in line]
    # print(isoValues)

    # --main app--
    app = QApplication(sys.argv)
    window = IsosurfaceDemo(margs=args, colormap=colormap, isoValues=isoValues)
    window.ui.vtkWidget.GetRenderWindow().SetSize(800, 800)
    window.show()
    window.setWindowState(Qt.WindowMaximized)
    window.iren.Initialize()

    # --hook up callbacks--
    window.ui.slider_clipX.valueChanged.connect(window.clipX_callback)
    window.ui.slider_clipY.valueChanged.connect(window.clipY_callback)
    window.ui.slider_clipZ.valueChanged.connect(window.clipZ_callback)

    sys.exit(app.exec_())
