import os

from PyQt5 import QtWidgets, QtCore, QtGui

from deep_space_trader.planet_image import PlanetImage


class InfoBar(QtWidgets.QWidget):
    def __init__(self, parent):
        super(InfoBar, self).__init__(parent)

        self.parent = parent

        planetLayout = QtWidgets.QHBoxLayout()

        self.planetLabel = QtWidgets.QLabel()
        self.planetLabel.setAlignment(QtCore.Qt.AlignCenter)
        planetLayout.addWidget(self.planetLabel)

        self.planetImage = PlanetImage(self.parent)
        planetLayout.addWidget(self.planetImage)

        planetGroup = QtWidgets.QGroupBox("Current planet")
        planetGroup.setAlignment(QtCore.Qt.AlignCenter)
        planetGroup.setLayout(planetLayout)

        dayLayout = QtWidgets.QHBoxLayout()
        self.dayLabel = QtWidgets.QLabel("")
        self.dayLabel.setAlignment(QtCore.Qt.AlignCenter)
        dayLayout.addWidget(self.dayLabel)
        dayGroup = QtWidgets.QGroupBox("Current day")
        dayGroup.setAlignment(QtCore.Qt.AlignCenter)
        dayGroup.setLayout(dayLayout)

        moneyLayout = QtWidgets.QHBoxLayout()
        self.moneyLabel = QtWidgets.QLabel("")
        self.moneyLabel.setAlignment(QtCore.Qt.AlignCenter)
        moneyLayout.addWidget(self.moneyLabel)
        moneyGroup = QtWidgets.QGroupBox("Money")
        moneyGroup.setAlignment(QtCore.Qt.AlignCenter)
        moneyGroup.setLayout(moneyLayout)

        planetCountLayout = QtWidgets.QHBoxLayout()
        self.planetCountLabel = QtWidgets.QLabel("")
        self.planetCountLabel.setAlignment(QtCore.Qt.AlignCenter)
        planetCountLayout.addWidget(self.planetCountLabel)
        planetCountGroup = QtWidgets.QGroupBox("Planets discovered")
        planetCountGroup.setAlignment(QtCore.Qt.AlignCenter)
        planetCountGroup.setLayout(planetCountLayout)

        capacityLayout = QtWidgets.QHBoxLayout()
        self.capacityLabel = QtWidgets.QLabel("")
        self.capacityLabel.setAlignment(QtCore.Qt.AlignCenter)
        capacityLayout.addWidget(self.capacityLabel)
        capacityGroup = QtWidgets.QGroupBox("Capacity")
        capacityGroup.setAlignment(QtCore.Qt.AlignCenter)
        capacityGroup.setLayout(capacityLayout)

        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.mainLayout.addWidget(planetGroup)
        self.mainLayout.addWidget(dayGroup)
        self.mainLayout.addWidget(moneyGroup)
        self.mainLayout.addWidget(planetCountGroup)
        self.mainLayout.addWidget(capacityGroup)
        self.update()

    def update(self):
        self.planetLabel.setText(self.parent.state.current_planet.full_name)
        self.planetImage.update()
        self.dayLabel.setText('%d/%d' % (self.parent.state.day, self.parent.state.max_days))
        self.moneyLabel.setText('{:,}'.format(self.parent.state.money))
        self.planetCountLabel.setText(str(self.parent.state.planets_discovered))
        self.capacityLabel.setText(str(self.parent.state.capacity))
        super(InfoBar, self).update()
