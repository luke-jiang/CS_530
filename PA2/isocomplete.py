#!/usr/bin/env python

# CS 530
# Project 2 Task 4
# Luke Jiang
# 02/14/2020

"""
Command line interface: python isocomplete.py <data> <gradma> <params> [--clip <X> <Y> <Z>]
    <data>:     3D scalar dataset to visualize
    <gradma>:   gradient magnitide
    <params>:   the file containing all the information necessary to visualize the isosurfaces.
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
DATA = [[800, 19000, 69000, 197, 140, 133, 0.5],
        [1100, 10000, 49000, 204, 71, 62, 0.7],
        [1300, 0, 72000, 230, 230, 230, 1.0]]


def makeBasic(ct_name, gm_name):
    """
    Read two datasets, create three plane clip functions and the renderer
    :param ct_name: file name of CT dataset
    :param gm_name: file name of gradient magnitude dataset
    """
    ct = vtk.vtkXMLImageDataReader()
    ct.SetFileName(ct_name)
    ct.Update()

    gm = vtk.vtkXMLImageDataReader()
    gm.SetFileName(gm_name)
    gm.Update()

    planeX = vtk.vtkPlane()
    planeX.SetOrigin(0, 0, 0)
    planeX.SetNormal(1.0, 0, 0)

    planeY = vtk.vtkPlane()
    planeY.SetOrigin(0, 0, 0)
    planeY.SetNormal(0, 1.0, 0)

    planeZ = vtk.vtkPlane()
    planeZ.SetOrigin(0, 0, 0)
    planeZ.SetNormal(0, 0, 1.0)

    # enable depth peeling in renderer
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.75, 0.75, 0.75)
    ren.SetUseDepthPeeling(1)
    ren.SetMaximumNumberOfPeels(100)
    ren.SetOcclusionRatio(0.4)
    ren.ResetCamera()

    return ct, gm, [planeX, planeY, planeZ], ren


def make(ct, gm, planes, data):
    """
    make pipeline for each isovalue
    :param planes: plane clip functions
    :param data: content in "params" given by the user
    :return: a list of actors to be added to the renderer
    """
    actors = list()
    i = 0

    for [isoValue, gradmin, gradmax, colorR, colorG, colorB, opacity] in data:

        ctContour = vtk.vtkContourFilter()
        ctContour.SetValue(i, isoValue)
        ctContour.SetInputConnection(ct.GetOutputPort())

        clipperX = vtk.vtkClipPolyData()
        clipperX.SetInputConnection(ctContour.GetOutputPort())
        clipperX.SetClipFunction(planes[0])

        clipperY = vtk.vtkClipPolyData()
        clipperY.SetInputConnection(clipperX.GetOutputPort())
        clipperY.SetClipFunction(planes[1])

        clipperZ = vtk.vtkClipPolyData()
        clipperZ.SetInputConnection(clipperY.GetOutputPort())
        clipperZ.SetClipFunction(planes[2])

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

        colorTrans = vtk.vtkColorTransferFunction()
        colorTrans.SetColorSpaceToRGB()
        colorTrans.AddRGBPoint(isoValue, colorR/256, colorG/256, colorB/256)

        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputConnection(maxClip.GetOutputPort())
        mapper.SetLookupTable(colorTrans)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetOpacity(opacity)
        actors.append(actor)

        i += 1

    return actors


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

        ct, gm, self.planes, self.ren = makeBasic(ct_name, gm_name)
        actors = make(ct, gm, self.planes, data)
        for actor in actors:
            self.ren.AddActor(actor)

        # enable depth peeling
        self.ui.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.ui.vtkWidget.GetRenderWindow().SetAlphaBitPlanes(True)
        self.ui.vtkWidget.GetRenderWindow().SetMultiSamples(0)
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
        self.planes[0].SetOrigin(val, 0, 0)
        self.ui.vtkWidget.GetRenderWindow().Render()

    def clipY_callback(self, val):
        self.clipY = val
        self.planes[1].SetOrigin(0, val, 0)
        self.ui.vtkWidget.GetRenderWindow().Render()

    def clipZ_callback(self, val):
        self.clipZ = val
        self.planes[2].SetOrigin(0, 0, val)
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

    # --parse params data--
    data = list()
    params = args.params
    with open(params, 'r') as fd:
        lines = fd.read().splitlines()
        for line in lines:
            if len(line) > 0 and line[0] != '#':
                intline = [float(i) for i in line.split()]
                data.append(intline)
    # print(data)

    # --main app--
    app = QApplication(sys.argv)
    window = IsosurfaceDemo(margs=args, data=data)
    window.ui.vtkWidget.GetRenderWindow().SetSize(800, 800)
    window.show()
    window.setWindowState(Qt.WindowMaximized)
    window.iren.Initialize()

    # --hook up callbacks--
    window.ui.slider_clipX.valueChanged.connect(window.clipX_callback)
    window.ui.slider_clipY.valueChanged.connect(window.clipY_callback)
    window.ui.slider_clipZ.valueChanged.connect(window.clipZ_callback)

    sys.exit(app.exec_())
