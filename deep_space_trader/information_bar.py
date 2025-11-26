import os

from PyQt5 import QtWidgets, QtCore, QtGui

from deep_space_trader.planet_image import PlanetImage

GROUPBOX_STYLE= "QGroupBox{ font-size: 12px; }"
LABEL_STYLE = "QLabel{ font-size: 14px; }"

class InfoBar(QtWidgets.QWidget):
    def __init__(self, parent):
        super(InfoBar, self).__init__(parent)

        self.parent = parent

        planetLayout = QtWidgets.QVBoxLayout()

        self.planetImage = PlanetImage(self.parent)
        planetLayout.addWidget(self.planetImage)

        self.planetLabel = QtWidgets.QLabel()
        self.planetLabel.setAlignment(QtCore.Qt.AlignCenter)
        planetLayout.addWidget(self.planetLabel)

        planetGroup = QtWidgets.QGroupBox("Current planet")
        planetGroup.setStyleSheet(GROUPBOX_STYLE)
        planetGroup.setAlignment(QtCore.Qt.AlignCenter)
        planetGroup.setLayout(planetLayout)

        dayLayout = QtWidgets.QHBoxLayout()
        self.dayLabel = QtWidgets.QLabel("")
        self.dayLabel.setStyleSheet(LABEL_STYLE)
        self.dayLabel.setAlignment(QtCore.Qt.AlignCenter)
        dayLayout.addWidget(self.dayLabel)
        dayGroup = QtWidgets.QGroupBox("Current day")
        dayGroup.setStyleSheet(GROUPBOX_STYLE)
        dayGroup.setAlignment(QtCore.Qt.AlignCenter)
        dayGroup.setLayout(dayLayout)

        moneyLayout = QtWidgets.QHBoxLayout()
        self.moneyLabel = QtWidgets.QLabel("")
        self.moneyLabel.setStyleSheet(LABEL_STYLE)
        self.moneyLabel.setAlignment(QtCore.Qt.AlignCenter)
        moneyLayout.addWidget(self.moneyLabel)
        moneyGroup = QtWidgets.QGroupBox("Money")
        moneyGroup.setStyleSheet(GROUPBOX_STYLE)
        moneyGroup.setAlignment(QtCore.Qt.AlignCenter)
        moneyGroup.setLayout(moneyLayout)

        purchasesLayout = QtWidgets.QHBoxLayout()
        self.purchasesLabel = QtWidgets.QLabel("")
        self.purchasesLabel.setStyleSheet(LABEL_STYLE)
        self.purchasesLabel.setAlignment(QtCore.Qt.AlignCenter)
        purchasesLayout.addWidget(self.purchasesLabel)
        purchasesGroup = QtWidgets.QGroupBox("Purchases")
        purchasesGroup.setStyleSheet(GROUPBOX_STYLE)
        purchasesGroup.setAlignment(QtCore.Qt.AlignCenter)
        purchasesGroup.setLayout(purchasesLayout)

        warehouseTripsLayout = QtWidgets.QHBoxLayout()
        self.warehouseTripsLabel = QtWidgets.QLabel("")
        self.warehouseTripsLabel.setStyleSheet(LABEL_STYLE)
        self.warehouseTripsLabel.setAlignment(QtCore.Qt.AlignCenter)
        warehouseTripsLayout.addWidget(self.warehouseTripsLabel)
        warehouseTripsGroup = QtWidgets.QGroupBox("Warehouse trips")
        warehouseTripsGroup.setStyleSheet(GROUPBOX_STYLE)
        warehouseTripsGroup.setAlignment(QtCore.Qt.AlignCenter)
        warehouseTripsGroup.setLayout(warehouseTripsLayout)

        planetCountLayout = QtWidgets.QHBoxLayout()
        self.planetCountLabel = QtWidgets.QLabel("")
        self.planetCountLabel.setStyleSheet(LABEL_STYLE)
        self.planetCountLabel.setAlignment(QtCore.Qt.AlignCenter)
        planetCountLayout.addWidget(self.planetCountLabel)
        planetCountGroup = QtWidgets.QGroupBox("Planets discovered")
        planetCountGroup.setStyleSheet(GROUPBOX_STYLE)
        planetCountGroup.setAlignment(QtCore.Qt.AlignCenter)
        planetCountGroup.setLayout(planetCountLayout)

        scoutFleetLayout = QtWidgets.QHBoxLayout()
        self.scoutFleetLabel = QtWidgets.QLabel("")
        self.scoutFleetLabel.setStyleSheet(LABEL_STYLE)
        self.scoutFleetLabel.setAlignment(QtCore.Qt.AlignCenter)
        scoutFleetLayout.addWidget(self.scoutFleetLabel)
        scoutFleetGroup = QtWidgets.QGroupBox("Scout fleet level")
        scoutFleetGroup.setStyleSheet(GROUPBOX_STYLE)
        scoutFleetGroup.setAlignment(QtCore.Qt.AlignCenter)
        scoutFleetGroup.setLayout(scoutFleetLayout)

        battleFleetLayout = QtWidgets.QHBoxLayout()
        self.battleFleetLabel = QtWidgets.QLabel("")
        self.battleFleetLabel.setStyleSheet(LABEL_STYLE)
        self.battleFleetLabel.setAlignment(QtCore.Qt.AlignCenter)
        battleFleetLayout.addWidget(self.battleFleetLabel)
        battleFleetGroup = QtWidgets.QGroupBox("Battle fleet level")
        battleFleetGroup.setStyleSheet(GROUPBOX_STYLE)
        battleFleetGroup.setAlignment(QtCore.Qt.AlignCenter)
        battleFleetGroup.setLayout(battleFleetLayout)

        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.mainLayout.addWidget(planetGroup)
        self.mainLayout.addWidget(dayGroup)
        self.mainLayout.addWidget(moneyGroup)
        self.mainLayout.addWidget(purchasesGroup)
        self.mainLayout.addWidget(warehouseTripsGroup)
        self.mainLayout.addWidget(planetCountGroup)
        self.mainLayout.addWidget(scoutFleetGroup)
        self.mainLayout.addWidget(battleFleetGroup)
        self.update()

    def update(self):
        self.planetLabel.setText(self.parent.state.current_planet.full_name)
        self.planetImage.update()
        self.dayLabel.setText('%d/%d' % (self.parent.state.day, self.parent.state.max_days))
        self.moneyLabel.setText('{:,}'.format(self.parent.state.money))
        self.planetCountLabel.setText('{:,}'.format(self.parent.state.planets_discovered))
        self.purchasesLabel.setText('%s/%s' % (self.parent.state.store_purchases, self.parent.state.max_store_purchases_per_day))
        self.warehouseTripsLabel.setText('%s/%s' % (self.parent.state.warehouse_trips, self.parent.state.warehouse_trips_per_day))

        if self.parent.state.battle_level == 0:
            battle_label_txt = "No battle fleet"
        else:
            battle_label_txt = '%d/%d' % (self.parent.state.battle_level, self.parent.state.max_battle_level)

        battle_label_txt += '<br>(%d%% chance of<br>winning battles)' % int(self.parent.state.battle_victory_chance_percentage())

        scout_label_text = '%d/%d' % (self.parent.state.scout_level, self.parent.state.max_scout_level)

        upper, lower = self.parent.state.planet_discovery_range
        scout_label_text += ("<br>Scout expedition<br>yields between<br>{0:,} - {1:,}"
                             "<br>new planets)".format(upper, lower))

        self.scoutFleetLabel.setText(scout_label_text)
        self.battleFleetLabel.setText(battle_label_txt)

        super(InfoBar, self).update()
