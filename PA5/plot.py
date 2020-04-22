import vtk
import math


def graph(data):
    table = vtk.vtkTable()
    arrX = vtk.vtkFloatArray()
    arrX.SetName("X")
    table.AddColumn(arrX)
    arrP = vtk.vtkFloatArray()
    arrP.SetName("Pressure")
    table.AddColumn(arrP)
    arrV = vtk.vtkFloatArray()
    arrV.SetName("Velocity")
    table.AddColumn(arrV)

    [locations, pressures, velocities] = data

    numPoints = min(len(locations), len(pressures))
    # inc = 7.5 / (numPoints - 1)
    table.SetNumberOfRows(numPoints)
    for i in range(0, numPoints):
        table.SetValue(i, 0, locations[i])
        table.SetValue(i, 1, pressures[i])
        table.SetValue(i, 2, velocities[i])

    view = vtk.vtkContextView()
    chart = vtk.vtkChartXY()
    view.GetScene().AddItem(chart)

    line1 = chart.AddPlot(vtk.vtkChart.LINE)
    line1.SetInputData(table, "X", "Pressure")
    line1.SetColor(0, 255, 0, 255)
    line1.SetWidth(2.0)

    line2 = chart.AddPlot(vtk.vtkChart.LINE)
    line2.SetInputData(table, "X", "Velocity")
    line2.SetColor(0, 0, 0, 255)
    line2.SetWidth(2.0)

    view.GetInteractor().Initialize()
    view.GetInteractor().Start()
