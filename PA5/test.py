import vtk
import sys
import argparse
import math

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSlider, QGridLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from Project5.plot import *

velocity_colormap = [[0.0, 0, 1, 1],
                     [0.218395, 0, 0, 1],
                     [0.241661, 0, 0, 0.502],
                     [0.266927, 1, 0, 0],
                     [0.485321, 1, 1, 0]]

pressure_colormap = [[0.908456, 0.231373, 0.298039, 0.752941],
                     [0.989821, 0.865003, 0.865003, 0.865003],
                     [1.07119, 0.705882, 0.015686, 0.14902]]



def read():
    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName("train-small.vtu")
    reader.Update()
    # print(reader.GetOutput())
    # tmp = getValues([reader.GetOutput(), 1], [-22600, -11172, 100, 50, 50, 0, 10])
    # print(tmp)
    # graph()
    return reader

def drawLine():
    linesrc = vtk.vtkLineSource()
    linesrc.SetPoint1(-22600, -11172, 100)
    linesrc.SetPoint2(47391, 12639, 100)
    linesrc.Update()

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(linesrc.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(0.2, 0.2, 0.2)
    actor.GetProperty().SetLineWidth(4)

    return actor



def getValues(data, points):
    [dataset, index] = data
    locator = vtk.vtkPointLocator()
    locator.SetDataSet(dataset)
    locator.BuildLocator()
    darray = dataset.GetPointData().GetArray(index)
    vals = list()
    [x, y, z, xs, ys, zs, step] = points
    for i in range(0, step):
        xi = x + xs * i
        yi = y + ys * i
        zi = z + zs * i
        id = locator.FindClosestPoint(xi, yi, zi)
        val = darray.GetTuple(id)
        vals.append(val)
    return vals

def sample_along_line(dataset, points):
    locator = vtk.vtkPointLocator()
    locator.SetDataSet(dataset)
    locator.BuildLocator()

    pressureArr = dataset.GetPointData().GetArray(0)
    velocityArr = dataset.GetPointData().GetArray(1)

    locations = list()
    velocities = list()
    pressures = list()

    [x, y, z, xs, ys, zs, step] = points
    for i in range(0, step):
        xi = x + xs * i
        yi = y + ys * i
        zi = z + zs * i
        id = locator.FindClosestPoint(xi, yi, zi)

        (p,) = pressureArr.GetTuple(id)
        (vx, vy, vz) = velocityArr.GetTuple(id)
        v = math.sqrt(vx ** 2 + vy ** 2 + vz ** 2)
        pressures.append(p)
        velocities.append(v)
        locations.append(i)

    return [locations, pressures, velocities]


def makeTrain(reader):
    lut = vtk.vtkColorTransferFunction()
    lut.SetColorSpaceToRGB()
    for [val, R, G, B] in pressure_colormap:
        lut.AddRGBPoint(val, R, G, B)

    mapper = vtk.vtkDataSetMapper()
    mapper.SetInputConnection(reader.GetOutputPort())
    mapper.SetScalarModeToUsePointFieldData()
    mapper.SelectColorArray(0)
    mapper.SetLookupTable(lut)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetOpacity(0.5)

    return actor

def makeStream(reader):
    arrow = vtk.vtkArrowSource()
    arrow.SetTipLength(0.1)
    arrow.SetShaftRadius(0.0001)

    lut = vtk.vtkColorTransferFunction()
    lut.SetColorSpaceToRGB()
    for [val, R, G, B] in velocity_colormap:
        lut.AddRGBPoint(val, R, G, B)

    streamerActors = list()

    for x in range(-20000, 10000, 2000):
        for z in range(0, 8000, 1000):
            y = -10000
            integ = vtk.vtkRungeKutta4()
            streamer = vtk.vtkStreamTracer()
            streamer.SetInputConnection(reader.GetOutputPort())
            streamer.SetStartPosition(x, y, z)
            streamer.SetMaximumPropagation(250000)
            streamer.SetIntegrationDirectionToForward()
            streamer.SetIntegrator(integ)
            streamer.SetComputeVorticity(True)

            streamerMapper = vtk.vtkPolyDataMapper()
            streamerMapper.SetInputConnection(streamer.GetOutputPort())
            streamerMapper.SetLookupTable(lut)
            streamerMapper.SetScalarModeToUsePointFieldData()
            streamerMapper.SelectColorArray(1) # color by velocity

            streamerActor = vtk.vtkActor()
            streamerActor.SetMapper(streamerMapper)
            # streamerActor.GetProperty().SetColor(0, 0, 1)

            streamerActors.append(streamerActor)

    return streamerActors


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName('The Main Window')
        # MainWindow.setWindowTitle('isosurface')

        self.centralWidget = QWidget(MainWindow)
        self.gridlayout = QGridLayout(self.centralWidget)
        self.vtkWidget = QVTKRenderWindowInteractor(self.centralWidget)

        self.push_plot = QPushButton()
        self.push_plot.setText('Plot')

        self.gridlayout.addWidget(self.vtkWidget, 0, 0, 4, 4)
        self.gridlayout.addWidget(self.push_plot, 5, 5, 1, 1)
        # self.gridlayout.addWidget(QLabel("X0"), 4, 0, 1, 1)
        # self.gridlayout.addWidget(self.slider_x0, 4, 1, 1, 1)

        MainWindow.setCentralWidget(self.centralWidget)


class Demo(QMainWindow):

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # self.frame_counter = 0

        self.reader = read()
        self.trainActor = makeTrain(self.reader)
        self.streamerActors = makeStream(self.reader)
        self.lineActor = drawLine()

        self.ren = vtk.vtkRenderer()
        self.ren.AddActor(self.trainActor)
        self.ren.AddActor(self.lineActor)
        for i in self.streamerActors:
            self.ren.AddActor(i)

        self.ren.SetBackground(0.75, 0.75, 0.75)
        self.ren.ResetCamera()

        # self.rightRen = vtk.vtkRenderer()
        # self.rightRen.SetViewPort(plot())
        # self.rightRen.SetBackground(0.75, 0.75, 0.75)
        # self.rightRen.ResetCamera()


        self.ui.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.ui.vtkWidget.GetRenderWindow().GetInteractor()

    def plot_callback(self):
        data = sample_along_line(self.reader.GetOutput(), [-22600, -11172, 100, 1000, 1000, 1000, 100])
        graph(data)


if __name__ == "__main__":
    # --define argument parser and parse arguments--
    # parser = argparse.ArgumentParser()
    # parser.add_argument('cfd_file')
    # parser.add_argument('wing_file')
    # args = parser.parse_args()

    # --main app--
    app = QApplication(sys.argv)
    window = Demo()
    window.ui.vtkWidget.GetRenderWindow().SetSize(800, 800)
    window.show()
    window.setWindowState(Qt.WindowMaximized)
    window.iren.Initialize()

    # --hook up callbacks--
    # window.ui.slider_x0.valueChanged.connect(window.X0_callback)
    window.ui.push_plot.clicked.connect(window.plot_callback)

    sys.exit(app.exec_())
