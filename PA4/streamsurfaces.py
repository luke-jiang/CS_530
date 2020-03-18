import vtk
import sys
import argparse

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

    datamin = 0
    datamax = 230
    lut = vtk.vtkColorTransferFunction()
    lut.SetColorSpaceToHSV()
    lut.AddHSVPoint(datamin, 0, 1, 1)
    dis = float(datamax - datamin) / 7
    for i in range(0, 8):
        lut.AddHSVPoint(float(datamin + dis * i), 0.1 * i, 1, 1)

    colorBar = vtk.vtkScalarBarActor()
    colorBar.SetOrientationToHorizontal()
    colorBar.SetLookupTable(lut)
    colorBarWidget = vtk.vtkScalarBarWidget()
    colorBarWidget.SetScalarBarActor(colorBar)

    # use rake to generate a series of streamlines
    rakePoints = [-230, 230]
    streamerActors = list()
    rakeActors = list()

    for i in range(0, 2):   # 200
        rake = vtk.vtkLineSource()
        rake.SetPoint1(0, 0, 0)
        rake.SetPoint2(0, rakePoints[i], 0)
        rake.SetResolution(20)
        rakeMapper = vtk.vtkPolyDataMapper()
        rakeMapper.SetInputConnection(rake.GetOutputPort())
        rakeActor = vtk.vtkActor()
        rakeActor.SetMapper(rakeMapper)
        rakeActors.append(rakeActor)

        integ = vtk.vtkRungeKutta4()
        streamer = vtk.vtkStreamTracer()
        streamer.SetInputConnection(cfdReader.GetOutputPort())
        streamer.SetSourceConnection(rake.GetOutputPort())
        streamer.SetMaximumPropagation(250)
        streamer.SetIntegrationDirectionToForward()
        streamer.SetIntegrator(integ)
        streamer.SetComputeVorticity(True)

        scalarSurface = vtk.vtkRuledSurfaceFilter()
        scalarSurface.SetInputConnection(streamer.GetOutputPort())
        scalarSurface.SetOffset(0)
        scalarSurface.SetOnRatio(0)
        # scalarSurface.PassLinesOn()
        scalarSurface.SetRuledModeToPointWalk()

        streamerMapper = vtk.vtkPolyDataMapper()
        streamerMapper.SetInputConnection(scalarSurface.GetOutputPort())
        streamerMapper.SetLookupTable(lut)
        streamerMapper.SetScalarModeToUsePointFieldData()
        streamerMapper.SelectColorArray(0)

        streamerActor = vtk.vtkActor()
        streamerActor.SetMapper(streamerMapper)
        streamerActor.GetProperty().SetOpacity(1)
        streamerActors.append(streamerActor)

    return streamerActors, wingActor, rakeActors, colorBarWidget



class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName('The Main Window')
        MainWindow.setWindowTitle('streamsurfaces')

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

        [self.streamerActors, self.wingActor, self.rakeActors, self.colorBarWidget] = make()

        self.ren = vtk.vtkRenderer()
        self.ren.AddActor(self.wingActor)
        for i in self.streamerActors:
            self.ren.AddActor(i)
        for i in self.rakeActors:
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
