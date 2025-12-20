from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph


class PriceHistoryGraph(QtWidgets.QDialog):
    def __init__(self, parent, item):

        super(PriceHistoryGraph, self).__init__(parent)

        self.setMinimumWidth(600)
        self.setMinimumHeight(600)

        self.parent = parent
        self.item = item
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.mainLayout)

        self.graph = pyqtgraph.PlotWidget()
        self.graph.plotItem.vb.setMouseEnabled(x=False, y=False)

        self.graph.setLabel('left', "<span style=\"font-size:30px\">Price</span>")
        self.graph.setLabel('bottom', "<span style=\"font-size:30px\">Day</span>")

        self.mainLayout.addWidget(self.graph)

        self.setWindowTitle("Price history for %s on %s" %
                            (item.type.name, parent.state.current_planet.full_name))

        planet = parent.state.current_planet
        range_end = self.parent.state.day + 1
        range_start = (self.parent.state.day - len(self.item.value_history)) + 1

        # Decrease font size of x-axis ticks
        ax = self.graph.getAxis('bottom')
        font = QtGui.QFont()
        font.setPixelSize(12)
        ax.setStyle(tickFont=font)

        x_axis = list(range(range_start, range_end))
        self.graph.plot(x_axis, self.item.value_history, pen='g')
        self.graph.showGrid(x=True, y=True, alpha=0.5)
        self.graph.setBackground('#101010')

        # Ensure no fraction values (days) are shown on the X-axis
        dx = [(value, str(value)) for value in list((range(int(min(x_axis)), int(max(x_axis)+1))))]
        ax.setTicks([dx, []])
