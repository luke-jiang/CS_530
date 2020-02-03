#!/usr/bin/env python

# CS 530
# Project 1 Task 2
# Luke Jiang
# 02/03/2020

# use Contour filter to show the contour lines of the height field
# isocontour line defined in interval [-10000, 8000] with step = 1000
# use colorTrans to make low contours blue and high contours yellow, mark the
# sea-level contour red.


import vtk
import sys

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSlider, QGridLayout, QLabel, QPushButton
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


def make(elev_name, img_name):

    # --Process the elevation data--
    elevation = vtk.vtkXMLImageDataReader()
    elevation.SetFileName(elev_name)  # "elevation_medium.vti"
    elevation.Update()

    geometry = vtk.vtkImageDataGeometryFilter()
    geometry.SetInputConnection(elevation.GetOutputPort())

    # the contour filter, [-10000, 8000] with step=1000
    contour = vtk.vtkContourFilter()
    contour.GenerateValues(19, -10000, 8000)
    contour.SetInputConnection(geometry.GetOutputPort())

    # the tube filter that wrap isocontours into tubes
    tube = vtk.vtkTubeFilter()
    tube.SetInputConnection(contour.GetOutputPort())
    tube.SetRadius(50000)

    # define color map
    colorTrans = vtk.vtkColorTransferFunction()
    colorTrans.SetColorSpaceToRGB()
    colorTrans.AddRGBPoint(-10000, 0, 0.651, 1)
    colorTrans.AddRGBPoint(-1000, 0.91, 0.96, 1)
    colorTrans.AddRGBPoint(0, 1, 0, 0)
    colorTrans.AddRGBPoint(1000, 0.99, 1, 0.89)
    colorTrans.AddRGBPoint(8000, 1, 1, 0)

    heightMapper = vtk.vtkDataSetMapper()
    heightMapper.SetInputConnection(tube.GetOutputPort())
    heightMapper.SetLookupTable(colorTrans)

    heightActor = vtk.vtkActor()
    heightActor.SetMapper(heightMapper)

    # --Process the satellite image to get texture--
    satellite_img = vtk.vtkJPEGReader()
    satellite_img.SetFileName(img_name) # "world.topo.bathy.200408.medium.jpg"
    satellite_img.Update()  # use an object before the pipeline updates it for you

    texture = vtk.vtkTexture()
    texture.SetInputConnection(satellite_img.GetOutputPort())

    textureMapper = vtk.vtkDataSetMapper()
    textureMapper.SetInputData(elevation.GetOutput())
    textureMapper.SetScalarRange(0, 255)
    textureMapper.ScalarVisibilityOff()

    textureActor = vtk.vtkActor()
    textureActor.SetMapper(textureMapper)
    textureActor.SetTexture(texture)

    return [tube, heightActor, textureActor]


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName('The Main Window')
        MainWindow.setWindowTitle('isocontour')

        self.centralWidget = QWidget(MainWindow)
        self.gridlayout = QGridLayout(self.centralWidget)
        self.vtkWidget = QVTKRenderWindowInteractor(self.centralWidget)

        self.slider_radius = QSlider()
        self.push_quit = QPushButton()
        self.push_quit.setText('Quit')

        self.gridlayout.addWidget(self.vtkWidget, 0, 0, 4, 4)
        self.gridlayout.addWidget(QLabel("Tube Radius"), 4, 0, 1, 1)
        self.gridlayout.addWidget(self.slider_radius, 4, 1, 1, 1)
        self.gridlayout.addWidget(self.push_quit, 5, 5, 1, 1)

        MainWindow.setCentralWidget(self.centralWidget)


class IsocontourDemo(QMainWindow):

    def __init__(self, margs, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.radius = 50000

        # elev_name = "elevation_medium.vti"
        # img_name = "world.topo.bathy.200408.medium.jpg"
        elev_name = margs[1]
        img_name = margs[2]

        [self.tube, self.heightActor, self.textureActor] = make(elev_name, img_name)
        self.ren = vtk.vtkRenderer()
        self.ren.AddActor(self.heightActor)
        self.ren.AddActor(self.textureActor)
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

        slider_setup(self.ui.slider_radius, self.radius, [30000, 100000], 1000)

    def radius_callback(self, val):
        self.radius = val
        self.tube.SetRadius(self.radius)
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

    window.ui.slider_radius.valueChanged.connect(window.radius_callback)
    window.ui.push_quit.clicked.connect(window.quit_callback)

    sys.exit(app.exec_())
