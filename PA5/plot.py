import vtk
import math

table = vtk.vtkTable()
arrX = vtk.vtkFloatArray()
arrX.SetName("X Axis")
table.AddColumn(arrX)
arrC = vtk.vtkFloatArray()
arrC.SetName("Cosine")
table.AddColumn(arrC)
arrS = vtk.vtkFloatArray()
arrS.SetName("Sine")
table.AddColumn(arrS)

numPoints = 69
inc = 7.5 / (numPoints - 1)
table.SetNumberOfRows(numPoints)
for i in range(0, numPoints):
    table.SetValue(i, 0, i * inc)
    table.SetValue(i, 1, math.cos(i * inc))
    table.SetValue(i, 2, math.sin(i * inc))

view = vtk.vtkContextView()
chart = vtk.vtkChartXY()
view.GetScene().AddItem(chart)

line = chart.AddPlot(0)
line.SetInputData(table)
line.SetInputArray(0, "X Axis")
line.SetInputArray(1, "Sine")
# line.SetInputArray(2, "Cosine")
line.SetColor(0, 255, 0, 255)
line.SetWidth(2.0)
#
# line = chart.AddPlot(0)
# line.SetInputData(table, 0, 2)
# line.SetColor(255, 0, 0, 255)
# line.SetWidth(1.0)

view.GetInteractor().Initialize()
view.GetInteractor().Start()



