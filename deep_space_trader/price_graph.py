from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph


class PriceHistoryGraph(QtWidgets.QDialog):
    def __init__(self, parent, item):

        super(PriceHistoryGraph, self).__init__(parent)

        self.parent = parent
        self.item = item
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.mainLayout)

        self.graph = pyqtgraph.PlotWidget()
        self.graph.setLabel('left', "<span style=\"font-size:30px\">Price</span>")
        self.graph.setLabel('bottom', "<span style=\"font-size:30px\">Days</span>")
        self.mainLayout.addWidget(self.graph)

        self.setWindowTitle("Price history for %s on %s" %
                            (item.type.name, parent.state.current_planet.full_name))

        planet = parent.state.current_planet
        range_end = self.parent.state.day + 1
        range_start = (self.parent.state.day - len(self.item.value_history)) + 1

        x_axis = list(range(range_start, range_end))
        self.graph.plot(x_axis, self.item.value_history)
