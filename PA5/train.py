#!/usr/bin/env python

# CS 530
# Final Project
# Luke Jiang
# 04/25/2020

# python train.py train-small.vtu

import vtk
import sys
import argparse
import math
from datetime import datetime

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSlider, QGridLayout, QLabel, QPushButton, \
    QLineEdit, QTextEdit, QCheckBox
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


# color map for pressure
pressure_colormap = [[0.908456, 0.231373, 0.298039, 0.752941],
                      [0.989821, 0.865003, 0.865003, 0.865003],
                      [1.07119, 0.705882, 0.015686, 0.14902]]

# color map for velocity
velocity_colormap = [[0.0, 0, 1, 1],
                     [0.218395, 0, 0, 1],
                     [0.241661, 0, 0, 0.502],
                     [0.266927, 1, 0, 0],
                     [0.485321, 1, 1, 0]]

# range of the input data set
datarange = [(-23274., -11937., 0.), (46753., 11875., 13427.)]

# default sampling resolution
init_resolution = 100

# default camera position
init_cam_pos = [(11739.94921875, -30.8115234375, 151939.9891022906),
                (11739.94921875, -30.8115234375, 6713.68798828125),
                (0.0, 1.0, 0.0),
                (130413.79900618957, 164222.48404136402)]

DATA_PRESSURE = 0
DATA_VELOCITY = 1


def read(filename):
    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName(filename)
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

    return linesrc, actor


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


def LPF(data):
    """
    1-D Low Pass Filter that averages out the data to be plotted
    """
    data1 = list.copy(data)
    num = len(data) - 1
    for i in range(1, num):
        data1[i] = (data[i - 1] + data[i] + data[i + 1]) / 3
    data1[0] = data[0]
    data1[num] = data[num]
    return data1


def graph(data, smooth=False):
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

    if smooth:
        velocities = LPF(velocities)
        pressures = LPF(pressures)

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
    actor.GetProperty().SetOpacity(0.7)

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

    colorBar = vtk.vtkScalarBarActor()
    colorBar.SetOrientationToHorizontal()
    colorBar.SetTitle("Velocity Magnitude")
    colorBar.SetNumberOfLabels(4)
    colorBar.SetMaximumHeightInPixels(300)
    colorBar.SetMaximumWidthInPixels(140)
    # colorBar.GetLabelTextProperty().SetFontSize(50)
    # colorBar.GetTitleTextProperty().SetFontSize(1)
    # colorBar.SetAnnotationTextScaling(0.1)
    colorBar.SetLookupTable(lut)
    colorBarWidget = vtk.vtkScalarBarWidget()
    colorBarWidget.SetScalarBarActor(colorBar)

    streamerActors = list()

    for x in range(-20000, 10000, 2000):
        for z in range(0, 8000, 1000):
            y = -10000
            integ = vtk.vtkRungeKutta4()
            streamer = vtk.vtkStreamTracer()
            # streamer.SetInputConnection(reader.GetOutputPort())
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

    return streamerActors, colorBarWidget


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName('The Main Window')
        MainWindow.setWindowTitle('Train')

        self.centralWidget = QWidget(MainWindow)
        self.gridlayout = QGridLayout(self.centralWidget)
        self.vtkWidget = QVTKRenderWindowInteractor(self.centralWidget)

        # checkboxes
        self.show_colorbar = QCheckBox()
        self.show_colorbar.setChecked(True)
        self.show_streamlines = QCheckBox()
        self.show_streamlines.setChecked(True)
        self.smooth = QCheckBox()
        self.smooth.setChecked(False)

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
        self.res_val.setText(str(init_resolution))
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
        self.push_resetLine = QPushButton()
        self.push_resetLine.setText("reset line")
        self.push_resetCamPos = QPushButton()
        self.push_resetCamPos.setText("reset camera position")

        # dialog
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        # self.log.setAcceptRichText(True)
        # self.log.setHtml("<div style='font-weight: bold'>Outputs</div>")


        self.gridlayout.addWidget(self.vtkWidget, 0, 0, 16, 11)

        self.gridlayout.addWidget(QLabel("Show Colorbar"), 0, 11, 1, 1)
        self.gridlayout.addWidget(self.show_colorbar, 0, 12, 1, 1)
        self.gridlayout.addWidget(QLabel("Show Streamlines"), 1, 11, 1, 1)
        self.gridlayout.addWidget(self.show_streamlines, 1, 12, 1, 1)
        self.gridlayout.addWidget(QLabel("Smooth Plot"), 2, 11, 1, 1)
        self.gridlayout.addWidget(self.smooth, 2, 12, 1, 1)

        self.gridlayout.addWidget(QLabel("x0"), 3, 11, 1, 1)
        self.gridlayout.addWidget(self.x0_val, 3, 12, 1, 1)
        self.gridlayout.addWidget(QLabel("y0"), 4, 11, 1, 1)
        self.gridlayout.addWidget(self.y0_val, 4, 12, 1, 1)
        self.gridlayout.addWidget(QLabel("z0"), 5, 11, 1, 1)
        self.gridlayout.addWidget(self.z0_val, 5, 12, 1, 1)

        self.gridlayout.addWidget(QLabel("x1"), 6, 11, 1, 1)
        self.gridlayout.addWidget(self.x1_val, 6, 12, 1, 1)
        self.gridlayout.addWidget(QLabel("y1"), 7, 11, 1, 1)
        self.gridlayout.addWidget(self.y1_val, 7, 12, 1, 1)
        self.gridlayout.addWidget(QLabel("z1"), 8, 11, 1, 1)
        self.gridlayout.addWidget(self.z1_val, 8, 12, 1, 1)

        self.gridlayout.addWidget(QLabel("Sample Resolution"), 9, 11, 1, 1)
        self.gridlayout.addWidget(self.res_val, 9, 12, 1, 1)
        self.gridlayout.addWidget(self.resolution, 10, 11, 1, 2)

        self.gridlayout.addWidget(self.push_plot, 11, 11, 1, 1)
        self.gridlayout.addWidget(self.push_drawLine, 11, 12, 1, 1)
        self.gridlayout.addWidget(self.push_saveData, 12, 11, 1, 1)
        self.gridlayout.addWidget(self.push_saveCamPos, 12, 12, 1, 1)
        self.gridlayout.addWidget(self.push_resetLine, 13, 11, 1, 1)
        self.gridlayout.addWidget(self.push_resetCamPos, 13, 12, 1, 1)

        self.gridlayout.addWidget(self.log, 14, 11, 2, 2)

        MainWindow.setCentralWidget(self.centralWidget)


class Demo(QMainWindow):

    def __init__(self, parent=None, margs=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.p0 = datarange[0]
        self.p1 = datarange[1]
        self.dataCache = None
        self.resolution = init_resolution
        self.filename = margs.train_file
        self.camPos = init_cam_pos
        self.LPFen = False

        self.reader = read(self.filename)
        self.trainActor = makeTrain(self.reader)
        self.streamerActors, self.streamline_colorbar = makeStream(self.reader)
        self.linesrc, self.lineActor = drawLine(self.p0, self.p1)

        self.ren = vtk.vtkRenderer()
        self.ren.AddActor(self.trainActor)
        self.ren.AddActor(self.lineActor)
        for i in self.streamerActors:
            self.ren.AddActor(i)

        self.ren.SetBackground(0.75, 0.75, 0.75)
        self.ren.ResetCamera()

        self.ui.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.ui.vtkWidget.GetRenderWindow().GetInteractor()

        self.streamline_colorbar.SetInteractor(self.iren)
        self.streamline_colorbar.On()

        def slider_setup(slider, val, bounds, interv):
            slider.setOrientation(QtCore.Qt.Horizontal)
            slider.setValue(float(val))
            slider.setTracking(False)
            slider.setTickInterval(interv)
            slider.setTickPosition(QSlider.TicksAbove)
            slider.setRange(bounds[0], bounds[1])

        slider_setup(self.ui.resolution, init_resolution, [50, 200], 5)

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

    def show_colorbar_callback(self):
        show = self.ui.show_colorbar.isChecked()
        if show:
            self.streamline_colorbar.On()
        else:
            self.streamline_colorbar.Off()
        self.ui.log.insertPlainText("-Show color bar: " + ("ON" if show else "OFF") + "\n")

    def show_streamlines_callback(self):
        show = self.ui.show_streamlines.isChecked()
        for a in self.streamerActors:
            a.GetProperty().SetOpacity(1 if show else 0)
        self.ui.log.insertPlainText("-Show streamlines: " + ("ON" if show else "OFF") + "\n")

    def smooth_callback(self):
        self.LPFen = self.ui.smooth.isChecked()
        self.ui.log.insertPlainText("-Smooth plot option: " + ("ON" if self.LPFen else "OFF") + "\n")

    def plot_callback(self):

        step = self.resolution
        p0 = self.p0
        p1 = self.p1
        x = p1[0] - p0[0]
        y = p1[1] - p0[1]
        z = p1[2] - p0[2]
        points_data = [p0[0], p0[1], p0[2], x / step, y / step, z / step, step]
        data = sample_along_line(self.reader.GetOutput(), points_data)
        self.dataCache = data
        self.ui.log.insertPlainText("-Plotting pressure and velocity along line\n")
        p_avg = sum(data[1]) / step
        v_avg = sum(data[2]) / step
        self.ui.log.insertPlainText("Average pressure: " + str(p_avg) + "\n")
        self.ui.log.insertPlainText("Average velocity: " + str(v_avg) + "\n")
        graph(data, self.LPFen)

    def check_range(self, s):
        self.ui.log.insertPlainText("-Value " + s + " is out of range\n")

    def drawLine_callback(self):
        x0 = float(self.ui.x0_val.text())
        if x0 < datarange[0][0] or x0 > datarange[1][0]:
            self.check_range("x0"); return
        y0 = float(self.ui.y0_val.text())
        if y0 < datarange[0][1] or y0 > datarange[1][1]:
            self.check_range("y0"); return
        z0 = float(self.ui.z0_val.text())
        if z0 < datarange[0][2] or z0 > datarange[1][2]:
            self.check_range("z0"); return

        x1 = float(self.ui.x1_val.text())
        if x1 < datarange[0][0] or x1 > datarange[1][0]:
            self.ocheck_range("x1"); return
        y1 = float(self.ui.y1_val.text())
        if y1 < datarange[0][1] or y1 > datarange[1][1]:
            self.check_range("y1"); return
        z1 = float(self.ui.z1_val.text())
        if z1 < datarange[0][2] or z1 > datarange[1][2]:
            self.check_range("z1"); return

        self.p0 = (x0, y0, z0)
        self.p1 = (x1, y1, z1)
        self.linesrc.SetPoint1(x0, y0, z0)
        self.linesrc.SetPoint2(x1, y1, z1)
        self.linesrc.Update()
        self.ui.log.insertPlainText('-Line drawn from ' + str(self.p0) + ' to ' + str(self.p1) +  '\n')
        self.ui.vtkWidget.GetRenderWindow().Render()

    def resolution_callback(self, val):
        oldval = self.resolution
        self.resolution = val
        self.ui.res_val.setText(str(val))
        self.ui.log.insertPlainText('-Sample resolution changed from ' + str(oldval) + ' to ' + str(val) + '\n')

    def saveData_callback(self):
        curr = str(datetime.now())
        filename = "train_line " + curr
        if self.dataCache is None:
            self.ui.log.insertPlainText('-Error: no data to save\n')
            return
        with open(filename, 'w') as fd:
            fd.write(str(self.dataCache))
        self.ui.log.insertPlainText('-Data written to file ' + filename + '\n')

    def saveCamPos_callback(self):
        camera = self.ren.GetActiveCamera()
        self.ui.log.insertPlainText("-Camera settings:\n")
        self.ui.log.insertPlainText("  * position:        %s\n" % (camera.GetPosition(),))
        self.ui.log.insertPlainText("  * focal point:     %s\n" % (camera.GetFocalPoint(),))
        self.ui.log.insertPlainText("  * up vector:       %s\n" % (camera.GetViewUp(),))
        self.ui.log.insertPlainText("  * clipping range:  %s\n" % (camera.GetClippingRange(),))
        self.camPos[0] = camera.GetPosition()
        self.camPos[1] = camera.GetFocalPoint()
        self.camPos[2] = camera.GetViewUp()
        self.camPos[3] = camera.GetClippingRange()

    def resetLine_callback(self):
        self.p0 = datarange[0]
        self.p1 = datarange[1]
        self.linesrc.SetPoint1(self.p0[0], self.p0[1], self.p0[2])
        self.linesrc.SetPoint2(self.p1[0], self.p1[1], self.p1[2])
        self.linesrc.Update()
        self.ui.log.insertPlainText('-Line reset\n')
        self.ui.vtkWidget.GetRenderWindow().Render()

    def resetCamPos_callback(self):
        camera = self.ren.GetActiveCamera()
        camera.SetPosition(self.camPos[0])
        camera.SetFocalPoint(self.camPos[1])
        camera.SetViewUp(self.camPos[2])
        camera.SetClippingRange(self.camPos[3])
        self.ui.log.insertPlainText('-Camera position is reset\n')



if __name__ == "__main__":
    # --define argument parser and parse arguments--
    parser = argparse.ArgumentParser()
    parser.add_argument('train_file')
    args = parser.parse_args()

    # --main app--
    app = QApplication(sys.argv)
    window = Demo(margs=args)
    window.ui.vtkWidget.GetRenderWindow().SetSize(800, 800)
    window.show()
    window.setWindowState(Qt.WindowMaximized)
    window.iren.Initialize()

    # --hook up callbacks--
    window.ui.show_colorbar.toggled.connect(window.show_colorbar_callback)
    window.ui.show_streamlines.toggled.connect(window.show_streamlines_callback)
    window.ui.smooth.toggled.connect(window.smooth_callback)

    window.ui.push_plot.clicked.connect(window.plot_callback)
    window.ui.push_drawLine.clicked.connect(window.drawLine_callback)
    window.ui.push_saveData.clicked.connect(window.saveData_callback)
    window.ui.push_saveCamPos.clicked.connect(window.saveCamPos_callback)
    window.ui.push_resetCamPos.clicked.connect(window.resetCamPos_callback)
    window.ui.push_resetLine.clicked.connect(window.resetLine_callback)

    window.ui.resolution.valueChanged.connect(window.resolution_callback)



    sys.exit(app.exec_())
