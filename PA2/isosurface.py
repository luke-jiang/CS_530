#!/usr/bin/env python

import vtk
import sys
import argparse

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSlider, QGridLayout, QLabel, QPushButton
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


def make(ct_name, contourVal, clipX, clipY, clipZ):
    # read the CT image
    ct = vtk.vtkXMLImageDataReader()
    ct.SetFileName(ct_name)
    ct.Update()

    # the contour filter
    contour = vtk.vtkContourFilter()
    # contour.SetValue(0, 500)
    contour.SetValue(0, contourVal)
    contour.SetInputConnection(ct.GetOutputPort())

    # three planes for each dimension
    planeX = vtk.vtkPlane()
    planeX.SetOrigin(clipX, 0, 0)
    planeX.SetNormal(1.0, 0, 0)
    clipperX = vtk.vtkClipPolyData()
    clipperX.SetInputConnection(contour.GetOutputPort())
    clipperX.SetClipFunction(planeX)

    planeY = vtk.vtkPlane()
    planeY.SetOrigin(0, clipY, 0)
    planeY.SetNormal(0, 1.0, 0)
    clipperY = vtk.vtkClipPolyData()
    clipperY.SetInputConnection(clipperX.GetOutputPort())
    clipperY.SetClipFunction(planeY)

    planeZ = vtk.vtkPlane()
    planeZ.SetOrigin(0, 0, clipZ)
    planeZ.SetNormal(0, 0, 1.0)
    clipperZ = vtk.vtkClipPolyData()
    clipperZ.SetInputConnection(clipperY.GetOutputPort())
    clipperZ.SetClipFunction(planeZ)

    # the color map
    colorTrans = vtk.vtkColorTransferFunction()
    colorTrans.SetColorSpaceToRGB()
    colorTrans.AddRGBPoint(1319, 0.9, 0.9, 0.9)  # bone
    colorTrans.AddRGBPoint(1153, 0.9, 0.9, 0.9)  # bone
    colorTrans.AddRGBPoint(500, 197/256, 140/256, 133/256)  # skin
    colorTrans.AddRGBPoint(753, 197 / 256, 140 / 256, 133 / 256)  # skin

    # color bar to diaplay the color scale
    colorBar = vtk.vtkScalarBarActor()
    colorBar.SetOrientationToHorizontal()
    colorBar.SetLookupTable(colorTrans)

    colorBarWidget = vtk.vtkScalarBarWidget()
    colorBarWidget.SetScalarBarActor(colorBar)

    # mapper and actor
    mapper = vtk.vtkDataSetMapper()
    mapper.SetInputConnection(clipperZ.GetOutputPort())
    mapper.SetLookupTable(colorTrans)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    return contour, planeX, planeY, planeZ, actor, colorBarWidget


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName('The Main Window')
        MainWindow.setWindowTitle('isosurface')

        self.centralWidget = QWidget(MainWindow)
        self.gridlayout = QGridLayout(self.centralWidget)
        self.vtkWidget = QVTKRenderWindowInteractor(self.centralWidget)

        self.slider_contour = QSlider()
        self.slider_clipX = QSlider()
        self.slider_clipY = QSlider()
        self.slider_clipZ = QSlider()

        self.gridlayout.addWidget(self.vtkWidget, 0, 0, 4, 4)

        self.gridlayout.addWidget(QLabel("Contour Value"), 4, 0, 1, 1)
        self.gridlayout.addWidget(self.slider_contour, 4, 1, 1, 1)

        self.gridlayout.addWidget(QLabel("Clip X"), 4, 2, 1, 1)
        self.gridlayout.addWidget(self.slider_clipX, 4, 3, 1, 1)

        self.gridlayout.addWidget(QLabel("Clip Y"), 5, 0, 1, 1)
        self.gridlayout.addWidget(self.slider_clipY, 5, 1, 1, 1)

        self.gridlayout.addWidget(QLabel("Clip Z"), 5, 2, 1, 1)
        self.gridlayout.addWidget(self.slider_clipZ, 5, 3, 1, 1)

        MainWindow.setCentralWidget(self.centralWidget)


class IsosurfaceDemo(QMainWindow):

    def __init__(self, margs, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # self.contourVal = 0
        # self.clipX = 0
        # self.clipY = 0
        # self.clipZ = 0

        # extract default isovalue and three clip positions
        self.contourVal = margs.val[0]
        self.clipX = margs.clip[0]
        self.clipY = margs.clip[1]
        self.clipZ = margs.clip[2]

        # ct_name = "vffeet-ct-small.vti"

        ct_name = margs.file

        [self.contour, self.planeX, self.planeY, self.planeZ, self.actor, self.colorBarWidget] = \
            make(ct_name, self.contourVal, self.clipX, self.clipY, self.clipZ)
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

        slider_setup(self.ui.slider_contour, self.contourVal, [500, 1500], 25)
        slider_setup(self.ui.slider_clipX, self.clipX, [0, 200], 5)
        slider_setup(self.ui.slider_clipY, self.clipY, [0, 200], 5)
        slider_setup(self.ui.slider_clipZ, self.clipZ, [0, 200], 5)

    def contour_callback(self, val):
        print(val)
        self.contourVal = val
        self.contour.SetValue(0, self.contourVal)
        self.ui.vtkWidget.GetRenderWindow().Render()

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
    # global args

    parser = argparse.ArgumentParser(
        description="Parser for isosurface")
    parser.add_argument('file')
    parser.add_argument('--val', type=int, metavar='int', nargs=1, help='initial isovalue', default=[500])
    parser.add_argument('--clip', type=int, metavar='int', nargs=3,
                        help='initial positions of clipping planes', default=[0, 0, 0])

    args = parser.parse_args()


    app = QApplication(sys.argv)
    window = IsosurfaceDemo(margs=args)
    window.ui.vtkWidget.GetRenderWindow().SetSize(800, 800)
    window.show()
    window.setWindowState(Qt.WindowMaximized)
    window.iren.Initialize()

    window.ui.slider_contour.valueChanged.connect(window.contour_callback)
    window.ui.slider_clipX.valueChanged.connect(window.clipX_callback)
    window.ui.slider_clipY.valueChanged.connect(window.clipY_callback)
    window.ui.slider_clipZ.valueChanged.connect(window.clipZ_callback)

    sys.exit(app.exec_())
