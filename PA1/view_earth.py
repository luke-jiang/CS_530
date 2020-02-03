#!/usr/bin/env python

# CS 530
# Project 1 Task 3
# Luke Jiang
# 02/03/2020

# Combine part1 and part2 to a globe

import vtk
import sys

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSlider, QGridLayout, QLabel, QPushButton
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


def make(elev_name, img_name):
    # --Process the elevation data--
    # --Apply warp filter to get height map--
    elevation = vtk.vtkXMLPolyDataReader()
    elevation.SetFileName(elev_name)
    elevation.Update()

    warp = vtk.vtkWarpScalar()
    warp.SetInputConnection(elevation.GetOutputPort())
    warp.SetScaleFactor(0)

    mapper = vtk.vtkDataSetMapper()
    mapper.SetInputConnection(warp.GetOutputPort())
    mapper.SetScalarRange(0, 255)
    mapper.ScalarVisibilityOff()

    # --Process the texture image--
    satellite_img = vtk.vtkJPEGReader()
    satellite_img.SetFileName(img_name)

    texture = vtk.vtkTexture()
    texture.SetInputConnection(satellite_img.GetOutputPort())

    textureActor = vtk.vtkActor()
    textureActor.SetMapper(mapper)
    textureActor.SetTexture(texture)

    # --Apply tube filter and contour filter--
    contour = vtk.vtkContourFilter()
    contour.GenerateValues(19, -10000, 8000)
    contour.SetInputConnection(warp.GetOutputPort())

    tube = vtk.vtkTubeFilter()
    tube.SetInputConnection(contour.GetOutputPort())
    tube.SetRadius(50000)

    colorTrans = vtk.vtkColorTransferFunction()
    colorTrans.SetColorSpaceToRGB()
    colorTrans.AddRGBPoint(-10000, 0, 0.651, 1)
    colorTrans.AddRGBPoint(-1000, 0.91, 0.96, 1)
    colorTrans.AddRGBPoint(0, 1, 0, 0)
    colorTrans.AddRGBPoint(1000, 0.99, 1, 0.89)
    colorTrans.AddRGBPoint(8000, 1, 1, 0)

    contourMapper = vtk.vtkDataSetMapper()
    contourMapper.SetInputConnection(tube.GetOutputPort())
    contourMapper.SetLookupTable(colorTrans)

    contourActor = vtk.vtkActor()
    contourActor.SetMapper(contourMapper)

    return [warp, textureActor, contourActor]


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName('The Main Window')
        MainWindow.setWindowTitle('globe')

        self.centralWidget = QWidget(MainWindow)
        self.gridlayout = QGridLayout(self.centralWidget)
        self.vtkWidget = QVTKRenderWindowInteractor(self.centralWidget)

        self.slider_warpScale = QSlider()
        self.push_quit = QPushButton()
        self.push_quit.setText('Quit')

        self.gridlayout.addWidget(self.vtkWidget, 0, 0, 4, 4)
        self.gridlayout.addWidget(QLabel("Warp Scale Factor"), 4, 0, 1, 1)
        self.gridlayout.addWidget(self.slider_warpScale, 4, 1, 1, 1)
        self.gridlayout.addWidget(self.push_quit, 5, 5, 1, 1)

        MainWindow.setCentralWidget(self.centralWidget)

class IsocontourDemo(QMainWindow):

    def __init__(self, margs, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.warpScale = 0

        elev_name = margs[1]
        img_name = margs[2]

        [self.warp, self.textureActor, self.contourActor] = make(elev_name, img_name)
        self.ren = vtk.vtkRenderer()
        self.ren.AddActor(self.textureActor)
        self.ren.AddActor(self.contourActor)
        self.ren.SetBackground(0.75, 0.75, 0.75)
        self.ren.ResetCamera()
        self.ren.GetActiveCamera().Azimuth(180)
        self.ren.GetActiveCamera().Roll(180)
        self.ui.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.ui.vtkWidget.GetRenderWindow().GetInteractor()

        def slider_setup(slider, val, bounds, interv):
            slider.setOrientation(QtCore.Qt.Horizontal)
            slider.setValue(float(val))
            slider.setTracking(False)
            slider.setTickInterval(interv)
            slider.setTickPosition(QSlider.TicksAbove)
            slider.setRange(bounds[0], bounds[1])

        slider_setup(self.ui.slider_warpScale, self.warpScale, [0, 200], 10)

    def radius_callback(self, val):
        self.warpScale = val
        self.warp.SetScaleFactor(self.warpScale)
        self.ui.vtkWidget.GetRenderWindow().Render()

    def quit_callback(self):
        sys.exit()


if __name__ == "__main__":
    # "elevation_sphere_medium.vtp"
    # "world.topo.bathy.200408.medium.jpg"
    app = QApplication(sys.argv)
    window = IsocontourDemo(margs=sys.argv)
    window.ui.vtkWidget.GetRenderWindow().SetSize(800, 800)
    window.show()
    window.setWindowState(Qt.WindowMaximized)
    window.iren.Initialize()

    window.ui.slider_warpScale.valueChanged.connect(window.radius_callback)
    window.ui.push_quit.clicked.connect(window.quit_callback)

    sys.exit(app.exec_())

