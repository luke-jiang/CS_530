import vtk
import sys
import argparse
import random

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QGridLayout
from PyQt5.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


cfd_FileName = "tdelta-low.vtk"     # the CFD file containing the vector field info
wing_FileName = "tdelta-wing.vtk"   # the geometry of delta wing

origins = [20, 100, 190]

def make():
    cfdReader = vtk.vtkStructuredPointsReader()
    cfdReader.SetFileName(cfd_FileName)
    cfdReader.Update()

    wingReader = vtk.vtkUnstructuredGridReader()
    wingReader.SetFileName(wing_FileName)
    wingReader.Update()

    # wing pipeline
    wingMapper = vtk.vtkDataSetMapper()
    wingMapper.SetInputConnection(wingReader.GetOutputPort())

    wingActor = vtk.vtkActor()
    wingActor.SetMapper(wingMapper)
    wingActor.GetProperty().SetColor(0.5, 0.5, 0.5)

    # streamline pipeline
    arrow = vtk.vtkArrowSource()
    arrow.SetTipLength(0.1)
    arrow.SetShaftRadius(0.0001)

    lut = vtk.vtkColorTransferFunction()
    lut.SetColorSpaceToHSV()
    for i in range(0, 6):
        lut.AddHSVPoint(i * 46, 0.1 * i, 1, 1)

    colorBar = vtk.vtkScalarBarActor()
    colorBar.SetOrientationToHorizontal()
    colorBar.SetLookupTable(lut)
    colorBarWidget = vtk.vtkScalarBarWidget()
    colorBarWidget.SetScalarBarActor(colorBar)


    streamerActors = list()

    for _ in range(0, 100):   # 200
        x = random.uniform(0, 100)
        y = random.uniform(-50, 50)
        z = 10

        integ = vtk.vtkRungeKutta4()
        streamer = vtk.vtkStreamTracer()
        streamer.SetInputConnection(cfdReader.GetOutputPort())
        streamer.SetStartPosition(x, y, z)
        streamer.SetMaximumPropagation(250)
        streamer.SetIntegrationDirectionToForward()
        streamer.SetIntegrator(integ)
        streamer.SetComputeVorticity(True)

        streamTube = vtk.vtkTubeFilter()
        streamTube.SetInputConnection(streamer.GetOutputPort())
        streamTube.SetRadius(2)
        streamTube.SetNumberOfSides(10)
        streamTube.SetVaryRadiusToVaryRadiusByVector()

        streamerMapper = vtk.vtkPolyDataMapper()
        streamerMapper.SetInputConnection(streamTube.GetOutputPort())
        streamerMapper.SetLookupTable(lut)
        streamerMapper.SetScalarModeToUsePointFieldData()
        streamerMapper.SelectColorArray(0)

        streamerActor = vtk.vtkActor()
        streamerActor.SetMapper(streamerMapper)
        streamerActor.GetProperty().SetOpacity(0.4)
        streamerActors.append(streamerActor)

    return streamerActors, wingActor, colorBarWidget


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName('The Main Window')
        MainWindow.setWindowTitle('streamtubes')

        self.centralWidget = QWidget(MainWindow)
        self.gridlayout = QGridLayout(self.centralWidget)
        self.vtkWidget = QVTKRenderWindowInteractor(self.centralWidget)

        self.gridlayout.addWidget(self.vtkWidget, 0, 0, 4, 4)

        MainWindow.setCentralWidget(self.centralWidget)


class IsosurfaceDemo(QMainWindow):

    def __init__(self, margs, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        [self.streamerActors, self.wingActor, self.colorBarWidget] = make()

        self.ren = vtk.vtkRenderer()
        self.ren.AddActor(self.wingActor)
        for i in self.streamerActors:
            self.ren.AddActor(i)
        self.ren.SetBackground(0.75, 0.75, 0.75)
        self.ren.ResetCamera()

        self.ui.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.ui.vtkWidget.GetRenderWindow().GetInteractor()

        self.colorBarWidget.SetInteractor(self.iren)
        self.colorBarWidget.On()


if __name__ == "__main__":
    # --define argument parser and parse arguments--
    parser = argparse.ArgumentParser()
    parser.add_argument('data')
    parser.add_argument('gradmag')
    args = parser.parse_args()

    # --main app--
    app = QApplication(sys.argv)
    window = IsosurfaceDemo(margs=args)
    window.ui.vtkWidget.GetRenderWindow().SetSize(800, 800)
    window.show()
    window.setWindowState(Qt.WindowMaximized)
    window.iren.Initialize()

    sys.exit(app.exec_())