import vtk
import sys
import argparse
import math

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSlider, QGridLayout, QLabel, QPushButton, QLineEdit, QTextEdit
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


velocity_colormap = [[0.0, 0, 1, 1],
                     [0.218395, 0, 0, 1],
                     [0.241661, 0, 0, 0.502],
                     [0.266927, 1, 0, 0],
                     [0.485321, 1, 1, 0]]

pressure_colormap = [[0.908456, 0.231373, 0.298039, 0.752941],
                     [0.989821, 0.865003, 0.865003, 0.865003],
                     [1.07119, 0.705882, 0.015686, 0.14902]]

# range of the input data set
datarange = [(-23274., -11937., 0.), (46753., 11875., 13427.)]

DATA_PRESSURE = 0
DATA_VELOCITY = 1


def read():
    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName("train-small.vtu")
    reader.Update()
    # print(reader.GetOutput())
    # tmp = getValues([reader.GetOutput(), 1], [-22600, -11172, 100, 50, 50, 0, 10])
    # print(tmp)
    # graph()
    return reader


def drawLine(p0, p1):
    """
    Draw a line from point p0 to p1.
    :param p0: starting point
    :param p1: ending point
    :return: an actor
    """
    (x0, y0, z0) = p0
    (x1, y1, z1) = p1
    linesrc = vtk.vtkLineSource()
    linesrc.SetPoint1(x0, y0, z0)
    linesrc.SetPoint2(x1, y1, z1)
    linesrc.Update()

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(linesrc.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(0.2, 0.2, 0.2)
    actor.GetProperty().SetLineWidth(4)

    return actor


def sample_along_line(dataset, points):
    """
    Sample pressure and velocity magnitude along a line
    :param dataset: the dataset that contains two arrays
    :param points: [start_x, start_y, start_z, x_step, y_step, z_step, total_points]
    :return: three arrays storing location, pressure and velocity
             magnitude data
    """
    locator = vtk.vtkPointLocator()
    locator.SetDataSet(dataset)
    locator.BuildLocator()

    pressureArr = dataset.GetPointData().GetArray(DATA_PRESSURE)
    velocityArr = dataset.GetPointData().GetArray(DATA_VELOCITY)

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
        locations.append((xi, yi, zi))

    return [locations, pressures, velocities]


def graph(data):
    """
    Showing the graph the velocity and pressure functions in a new view
    """
    table = vtk.vtkTable()
    arrX = vtk.vtkFloatArray()
    arrX.SetName("X")
    table.AddColumn(arrX)
    arrP = vtk.vtkFloatArray()
    arrP.SetName("Pressure")
    table.AddColumn(arrP)
    arrV = vtk.vtkFloatArray()
    arrV.SetName("V_mag")
    table.AddColumn(arrV)

    [locations, pressures, velocities] = data

    numPoints = min(len(locations), len(pressures))

    table.SetNumberOfRows(numPoints)
    for i in range(0, numPoints):
        table.SetValue(i, 0, i)
        table.SetValue(i, 1, pressures[i])
        table.SetValue(i, 2, velocities[i])

    view = vtk.vtkContextView()
    chart = vtk.vtkChartXY()
    chart.SetShowLegend(True)
    chart.SetTitle("Pressure and Velocity Magnitude vs. Location")
    chart.GetTitleProperties().SetFontSize(25)
    view.GetScene().AddItem(chart)

    line1 = chart.AddPlot(vtk.vtkChart.LINE)
    line1.SetInputData(table, "X", "Pressure")
    line1.SetColor(166, 101, 174)
    line1.SetWidth(2.0)

    line2 = chart.AddPlot(vtk.vtkChart.LINE)
    line2.SetInputData(table, "X", "V_mag")
    line2.SetColor(230, 54, 56)
    line2.SetWidth(2.0)

    view.GetRenderWindow().SetSize(1000, 800)
    view.GetInteractor().Initialize()
    view.GetInteractor().Start()


def makeTrain(reader):
    """
    Render the train dataset, colored using pressure value
    """
    lut = vtk.vtkColorTransferFunction()
    lut.SetColorSpaceToRGB()
    for [val, R, G, B] in pressure_colormap:
        lut.AddRGBPoint(val, R, G, B)

    mapper = vtk.vtkDataSetMapper()
    mapper.SetInputConnection(reader.GetOutputPort())
    mapper.SetScalarModeToUsePointFieldData()
    mapper.SelectColorArray(DATA_PRESSURE)
    mapper.SetLookupTable(lut)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetOpacity(0.5)

    return actor


def makeStream(reader):
    """
    Create streamlines for the data set, colored by velocity magnitude
    """
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
            streamerMapper.SelectColorArray(DATA_VELOCITY)

            streamerActor = vtk.vtkActor()
            streamerActor.SetMapper(streamerMapper)

            streamerActors.append(streamerActor)

    return streamerActors


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName('The Main Window')
        MainWindow.setWindowTitle('Train')

        self.centralWidget = QWidget(MainWindow)
        self.gridlayout = QGridLayout(self.centralWidget)
        self.vtkWidget = QVTKRenderWindowInteractor(self.centralWidget)

        # start and end points of the line
        self.x0_val = QLineEdit()
        self.y0_val = QLineEdit()
        self.z0_val = QLineEdit()

        self.x1_val = QLineEdit()
        self.y1_val = QLineEdit()
        self.z1_val = QLineEdit()

        # sampling resolution
        self.resolution = QSlider()
        self.res_val = QLineEdit()
        self.res_val.setText("000")
        self.res_val.setFixedWidth(150)
        self.res_val.setAlignment(Qt.AlignLeft)
        self.res_val.setReadOnly(True)

        # push buttons
        self.push_drawLine = QPushButton()
        self.push_drawLine.setText("draw line")
        self.push_plot = QPushButton()
        self.push_plot.setText('plot')
        self.push_saveData = QPushButton()
        self.push_saveData.setText("save data")
        self.push_saveCamPos = QPushButton()
        self.push_saveCamPos.setText("save camera position")

        # dialog
        self.info = QTextEdit()
        self.info.setReadOnly(True)
        self.info.setAcceptRichText(True)
        self.info.setHtml("<div style='font-weight: bold'>Outputs</div>")



        self.gridlayout.addWidget(self.vtkWidget, 0, 0, 12, 10)

        # self.gridlayout.addWidget(QLabel("Line Position"), 0, 11, 1, 1)
        # self.gridlayout.addWidget(QLabel("Line Position"), 0, 12, 1, 1)
        self.gridlayout.addWidget(QLabel("x0"), 0, 11, 1, 1)
        self.gridlayout.addWidget(self.x0_val, 0, 12, 1, 1)
        self.gridlayout.addWidget(QLabel("y0"), 1, 11, 1, 1)
        self.gridlayout.addWidget(self.y0_val, 1, 12, 1, 1)
        self.gridlayout.addWidget(QLabel("z0"), 2, 11, 1, 1)
        self.gridlayout.addWidget(self.z0_val, 2, 12, 1, 1)

        self.gridlayout.addWidget(QLabel("x1"), 3, 11, 1, 1)
        self.gridlayout.addWidget(self.x1_val, 3, 12, 1, 1)
        self.gridlayout.addWidget(QLabel("y1"), 4, 11, 1, 1)
        self.gridlayout.addWidget(self.y1_val, 4, 12, 1, 1)
        self.gridlayout.addWidget(QLabel("z1"), 5, 11, 1, 1)
        self.gridlayout.addWidget(self.z1_val, 5, 12, 1, 1)

        self.gridlayout.addWidget(QLabel("Sample Resolution"), 6, 11, 1, 1)
        self.gridlayout.addWidget(self.res_val, 6, 12, 1, 1)
        self.gridlayout.addWidget(self.resolution, 7, 11, 1, 2)

        self.gridlayout.addWidget(self.push_plot, 8, 11, 1, 1)
        self.gridlayout.addWidget(self.push_drawLine, 8, 12, 1, 1)
        self.gridlayout.addWidget(self.push_saveData, 9, 11, 1, 1)
        self.gridlayout.addWidget(self.push_saveCamPos, 9, 12, 1, 1)

        self.gridlayout.addWidget(self.info, 10, 11, 2, 2)

        MainWindow.setCentralWidget(self.centralWidget)


class Demo(QMainWindow):

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # self.frame_counter = 0
        self.p0 = datarange[0]
        self.p1 = datarange[1]

        self.reader = read()
        self.trainActor = makeTrain(self.reader)
        self.streamerActors = makeStream(self.reader)
        self.lineActor = drawLine(self.p0, self.p1)

        self.ren = vtk.vtkRenderer()
        self.ren.AddActor(self.trainActor)
        self.ren.AddActor(self.lineActor)
        for i in self.streamerActors:
            self.ren.AddActor(i)

        self.ren.SetBackground(0.75, 0.75, 0.75)
        self.ren.ResetCamera()

        self.ui.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.ui.vtkWidget.GetRenderWindow().GetInteractor()

        def slider_setup(slider, val, bounds, interv):
            slider.setOrientation(QtCore.Qt.Horizontal)
            slider.setValue(float(val))
            slider.setTracking(False)
            slider.setTickInterval(interv)
            slider.setTickPosition(QSlider.TicksAbove)
            slider.setRange(bounds[0], bounds[1])

        slider_setup(self.ui.resolution, 0, [0, 200], 5)

        def lineEdit_setup(lineEdit, val):
            lineEdit.setText(str(val))
            lineEdit.setFixedWidth(150)
            lineEdit.setAlignment(Qt.AlignLeft)

        lineEdit_setup(self.ui.x0_val, self.p0[0])
        lineEdit_setup(self.ui.y0_val, self.p0[1])
        lineEdit_setup(self.ui.z0_val, self.p0[2])
        lineEdit_setup(self.ui.x1_val, self.p1[0])
        lineEdit_setup(self.ui.y1_val, self.p1[1])
        lineEdit_setup(self.ui.z1_val, self.p1[2])

    def plot_callback(self):
        step = 100
        p0 = self.p0
        p1 = self.p1
        x = p1[0] - p0[0]
        y = p1[1] - p0[1]
        z = p1[2] - p0[2]
        points_data = [p0[0], p0[1], p0[2], x / step, y / step, z / step, step]
        data = sample_along_line(self.reader.GetOutput(), points_data)
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
