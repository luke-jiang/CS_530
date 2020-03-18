



import vtk
import sys
import argparse

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSlider, QGridLayout, QLabel
import PyQt5.QtCore as QtCore
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

    # plane cut pipeline
    arrow = vtk.vtkArrowSource()
    arrow.SetTipLength(0.1)
    arrow.SetShaftRadius(0.0001)

    colorTrans = vtk.vtkColorTransferFunction()
    colorTrans.SetColorSpaceToRGB()
    colorTrans.AddRGBPoint(0, 0, 0, 1)
    colorTrans.AddRGBPoint(230, 1, 0, 0)

    colorBar = vtk.vtkScalarBarActor()
    colorBar.SetOrientationToHorizontal()
    colorBar.SetLookupTable(colorTrans)
    colorBarWidget = vtk.vtkScalarBarWidget()
    colorBarWidget.SetScalarBarActor(colorBar)

    planes = list()
    cutActors = list()

    for origin in origins:

        plane = vtk.vtkPlane()
        plane.SetOrigin(origin, 0, 0)
        plane.SetNormal(1.0, 0, 0)
        planes.append(plane)

        planeCut = vtk.vtkCutter()
        planeCut.SetInputConnection(cfdReader.GetOutputPort())
        planeCut.SetCutFunction(plane)

        arrowFilter = vtk.vtkGlyph3D()
        arrowFilter.SetInputConnection(0, planeCut.GetOutputPort())
        arrowFilter.SetInputConnection(1, arrow.GetOutputPort())
        arrowFilter.ScalingOn()
        arrowFilter.SetScaleModeToScaleByVector()
        arrowFilter.SetScaleFactor(0.1)
        arrowFilter.Update()
        # print(arrowFilter.GetOutput().GetPointData().GetArray("GlyphVector"))

        arrayCalc = vtk.vtkArrayCalculator()
        arrayCalc.SetInputConnection(arrowFilter.GetOutputPort())
        arrayCalc.AddVectorArrayName("GlyphVector")
        arrayCalc.SetFunction("mag(GlyphVector)")
        arrayCalc.SetResultArrayName("v_mag")
        arrayCalc.Update()
        # print(arrayCalc.GetOutput().GetPointData().GetArray("v_mag"))

        cutMapper = vtk.vtkDataSetMapper()
        cutMapper.SetInputConnection(arrowFilter.GetOutputPort())
        cutMapper.SetLookupTable(colorTrans)
        cutMapper.ScalarVisibilityOn()
        cutMapper.SetScalarRange(arrayCalc.GetOutput().GetPointData().GetArray("v_mag").GetRange())

        cutActor = vtk.vtkActor()
        cutActor.SetMapper(cutMapper)
        # cutActor.GetProperty().SetColor(0, 0, 1)
        cutActor.GetProperty().SetOpacity(0.3)

        cutActors.append(cutActor)

    return cutActors, wingActor, planes, colorBarWidget


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName('The Main Window')
        # MainWindow.setWindowTitle('isosurface')

        self.centralWidget = QWidget(MainWindow)
        self.gridlayout = QGridLayout(self.centralWidget)
        self.vtkWidget = QVTKRenderWindowInteractor(self.centralWidget)

        # self.slider_x0 = QSlider()

        self.gridlayout.addWidget(self.vtkWidget, 0, 0, 4, 4)

        # self.gridlayout.addWidget(QLabel("X0"), 4, 0, 1, 1)
        # self.gridlayout.addWidget(self.slider_x0, 4, 1, 1, 1)

        MainWindow.setCentralWidget(self.centralWidget)


class IsosurfaceDemo(QMainWindow):

    def __init__(self, margs, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        [self.cutActors, self.wingActor, self.planes, self.colorBarWidget] = make()

        self.ren = vtk.vtkRenderer()
        self.ren.AddActor(self.wingActor)
        for i in self.cutActors:
            self.ren.AddActor(i)
        self.ren.SetBackground(0.75, 0.75, 0.75)
        self.ren.ResetCamera()

        self.ui.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.ui.vtkWidget.GetRenderWindow().GetInteractor()

        self.colorBarWidget.SetInteractor(self.iren)
        self.colorBarWidget.On()

        # def slider_setup(slider, val, bounds, interv):
        #     slider.setOrientation(QtCore.Qt.Horizontal)
        #     slider.setValue(float(val))
        #     slider.setTracking(False)
        #     slider.setTickInterval(interv)
        #     slider.setTickPosition(QSlider.TicksAbove)
        #     slider.setRange(bounds[0], bounds[1])

        # slider_setup(self.ui.slider_x0, 99, [0, 230], 1)

    # def X0_callback(self, val):
    #     self.planes(0).SetOrigin(val, 0, 0)
    #     self.ui.vtkWidget.GetRenderWindow().Render()


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

    # --hook up callbacks--
    # window.ui.slider_x0.valueChanged.connect(window.X0_callback)

    sys.exit(app.exec_())








