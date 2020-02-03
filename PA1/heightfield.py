#!/usr/bin/env python

# CS 530
# Project 1 Task 1
# Luke Jiang
# 02/03/2020

# Use Warp filter to show the height field


import vtk
import sys

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSlider, QGridLayout, QLabel, QPushButton
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


def make(elev_name, img_name):

    # --Process the elevation data--
    elevation = vtk.vtkXMLImageDataReader()
    elevation.SetFileName(elev_name)

    # extract geometry
    geometry = vtk.vtkImageDataGeometryFilter()
    geometry.SetInputConnection(elevation.GetOutputPort())

    # filter to create height map of elevation
    warp = vtk.vtkWarpScalar()
    warp.SetInputConnection(geometry.GetOutputPort())
    warp.SetScaleFactor(0)

    mapper = vtk.vtkDataSetMapper()
    mapper.SetInputConnection(warp.GetOutputPort())
    mapper.SetScalarRange(0, 255)
    mapper.ScalarVisibilityOff()

    # --Process the image for texture--
    satellite_img = vtk.vtkJPEGReader()
    satellite_img.SetFileName(img_name)

    texture = vtk.vtkTexture()  # an algorithm
    texture.SetInputConnection(satellite_img.GetOutputPort())

    # --Put the height map and the texture on actor--
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.SetTexture(texture)

    return [warp, actor]


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName('The Main Window')
        MainWindow.setWindowTitle('heightfield')

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

        # elev_name = "elevation_medium.vti"
        # img_name = "world.topo.bathy.200408.medium.jpg"
        elev_name = margs[1]
        img_name = margs[2]

        [self.warp, self.actor] = make(elev_name, img_name)
        self.ren = vtk.vtkRenderer()
        self.ren.AddActor(self.actor)
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
    app = QApplication(sys.argv)
    window = IsocontourDemo(margs=sys.argv)
    window.ui.vtkWidget.GetRenderWindow().SetSize(800, 800)
    window.show()
    window.setWindowState(Qt.WindowMaximized)
    window.iren.Initialize()

    window.ui.slider_warpScale.valueChanged.connect(window.radius_callback)
    window.ui.push_quit.clicked.connect(window.quit_callback)

    sys.exit(app.exec_())

