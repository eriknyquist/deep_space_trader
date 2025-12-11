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
        self.tooltipsEnabled = True

        self.planetImage = PlanetImage(self.parent)
        planetLayout.addWidget(self.planetImage)

        self.planetLabel = QtWidgets.QLabel()
        self.planetLabel.setAlignment(QtCore.Qt.AlignCenter)
        planetLayout.addWidget(self.planetLabel)

        self.planetGroup = QtWidgets.QGroupBox("Current planet")
        self.planetGroup.setStyleSheet(GROUPBOX_STYLE)
        self.planetGroup.setAlignment(QtCore.Qt.AlignCenter)
        self.planetGroup.setLayout(planetLayout)

        dayLayout = QtWidgets.QHBoxLayout()
        self.dayLabel = QtWidgets.QLabel("")
        self.dayLabel.setStyleSheet(LABEL_STYLE)
        self.dayLabel.setAlignment(QtCore.Qt.AlignCenter)
        dayLayout.addWidget(self.dayLabel)
        self.dayGroup = QtWidgets.QGroupBox("Current day")
        self.dayGroup.setStyleSheet(GROUPBOX_STYLE)
        self.dayGroup.setAlignment(QtCore.Qt.AlignCenter)
        self.dayGroup.setLayout(dayLayout)

        moneyLayout = QtWidgets.QHBoxLayout()
        self.moneyLabel = QtWidgets.QLabel("")
        self.moneyLabel.setStyleSheet(LABEL_STYLE)
        self.moneyLabel.setAlignment(QtCore.Qt.AlignCenter)
        moneyLayout.addWidget(self.moneyLabel)
        self.moneyGroup = QtWidgets.QGroupBox("Money")
        self.moneyGroup.setStyleSheet(GROUPBOX_STYLE)
        self.moneyGroup.setAlignment(QtCore.Qt.AlignCenter)
        self.moneyGroup.setLayout(moneyLayout)

        dayMoneyLayout = QtWidgets.QVBoxLayout()
        dayMoneyLayout.addWidget(self.dayGroup)
        dayMoneyLayout.addWidget(self.moneyGroup)

        purchasesLayout = QtWidgets.QHBoxLayout()
        self.purchasesLabel = QtWidgets.QLabel("")
        self.purchasesLabel.setStyleSheet(LABEL_STYLE)
        self.purchasesLabel.setAlignment(QtCore.Qt.AlignCenter)
        purchasesLayout.addWidget(self.purchasesLabel)
        self.purchasesGroup = QtWidgets.QGroupBox("Purchases")
        self.purchasesGroup.setStyleSheet(GROUPBOX_STYLE)
        self.purchasesGroup.setAlignment(QtCore.Qt.AlignCenter)
        self.purchasesGroup.setLayout(purchasesLayout)

        warehouseTripsLayout = QtWidgets.QHBoxLayout()
        self.warehouseTripsLabel = QtWidgets.QLabel("")
        self.warehouseTripsLabel.setStyleSheet(LABEL_STYLE)
        self.warehouseTripsLabel.setAlignment(QtCore.Qt.AlignCenter)
        warehouseTripsLayout.addWidget(self.warehouseTripsLabel)
        self.warehouseTripsGroup = QtWidgets.QGroupBox("Warehouse trips")
        self.warehouseTripsGroup.setStyleSheet(GROUPBOX_STYLE)
        self.warehouseTripsGroup.setAlignment(QtCore.Qt.AlignCenter)
        self.warehouseTripsGroup.setLayout(warehouseTripsLayout)

        purchasesWarehouseLayout = QtWidgets.QVBoxLayout()
        purchasesWarehouseLayout.addWidget(self.purchasesGroup)
        purchasesWarehouseLayout.addWidget(self.warehouseTripsGroup)

        planetCountLayout = QtWidgets.QHBoxLayout()
        self.planetCountLabel = QtWidgets.QLabel("")
        self.planetCountLabel.setStyleSheet(LABEL_STYLE)
        self.planetCountLabel.setAlignment(QtCore.Qt.AlignCenter)
        planetCountLayout.addWidget(self.planetCountLabel)
        self.planetCountGroup = QtWidgets.QGroupBox("Planets discovered")
        self.planetCountGroup.setStyleSheet(GROUPBOX_STYLE)
        self.planetCountGroup.setAlignment(QtCore.Qt.AlignCenter)
        self.planetCountGroup.setLayout(planetCountLayout)

        scoutFleetLayout = QtWidgets.QHBoxLayout()
        self.scoutFleetLabel = QtWidgets.QLabel("")
        self.scoutFleetLabel.setStyleSheet(LABEL_STYLE)
        self.scoutFleetLabel.setAlignment(QtCore.Qt.AlignCenter)
        scoutFleetLayout.addWidget(self.scoutFleetLabel)
        self.scoutFleetGroup = QtWidgets.QGroupBox("Scout fleet level")
        self.scoutFleetGroup.setStyleSheet(GROUPBOX_STYLE)
        self.scoutFleetGroup.setAlignment(QtCore.Qt.AlignCenter)
        self.scoutFleetGroup.setLayout(scoutFleetLayout)

        battleFleetLayout = QtWidgets.QHBoxLayout()
        self.battleFleetLabel = QtWidgets.QLabel("")
        self.battleFleetLabel.setStyleSheet(LABEL_STYLE)
        self.battleFleetLabel.setAlignment(QtCore.Qt.AlignCenter)
        battleFleetLayout.addWidget(self.battleFleetLabel)
        self.battleFleetGroup = QtWidgets.QGroupBox("Battle fleet level")
        self.battleFleetGroup.setStyleSheet(GROUPBOX_STYLE)
        self.battleFleetGroup.setAlignment(QtCore.Qt.AlignCenter)
        self.battleFleetGroup.setLayout(battleFleetLayout)

        healthLayout = QtWidgets.QHBoxLayout()
        self.healthBar = QtWidgets.QProgressBar(self)
        self.healthBar.setOrientation(QtCore.Qt.Vertical)
        self.healthBar.setRange(0, 100)
        self.healthBar.setValue(100)
        self.healthBar.setFixedWidth(20)
        self.healthBar.setStyleSheet("QProgressBar::chunk { background-color: #00FF00; }")
        self.healthBar.setFormat(None)
        healthLayout.addWidget(self.healthBar)
        self.healthGroup = QtWidgets.QGroupBox("Health")
        self.healthGroup.setStyleSheet(GROUPBOX_STYLE)
        self.healthGroup.setAlignment(QtCore.Qt.AlignCenter)
        self.healthGroup.setLayout(healthLayout)
        self.healthGroup.setFixedWidth(60)
        healthLayout.setContentsMargins(5, 5, 5, 5)

        scoutBattleLayout = QtWidgets.QVBoxLayout()
        scoutBattleLayout.addWidget(self.scoutFleetGroup)
        scoutBattleLayout.addWidget(self.battleFleetGroup)

        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.mainLayout.addWidget(self.planetGroup)
        self.mainLayout.addLayout(dayMoneyLayout)
        self.mainLayout.addLayout(purchasesWarehouseLayout)
        self.mainLayout.addLayout(scoutBattleLayout)
        self.mainLayout.addWidget(self.planetCountGroup)
        self.mainLayout.addWidget(self.healthGroup)

        self.update()

    def interpColor(self, start, end, percent):
        r_span = start[0] - end[0] if start[0] > end[0] else end[0] - start[0]
        g_span = start[1] - end[1] if start[1] > end[1] else end[1] - start[1]
        b_span = start[2] - end[2] if start[2] > end[2] else end[2] - start[2]

        r_delta = (float(r_span) / 100.0) * float(percent)
        g_delta = (float(g_span) / 100.0) * float(percent)
        b_delta = (float(b_span) / 100.0) * float(percent)

        return [
            int(float(start[0]) + r_delta if start[0] < end[0] else start[0] - r_delta),
            int(float(start[1]) + g_delta if start[1] < end[1] else start[1] - g_delta),
            int(float(start[2]) + b_delta if start[2] < end[2] else start[2] - b_delta)
        ]

    def setHealthBarColor(self):
        highColor = [0, 255, 0]    # Green
        medColor = [255, 237, 41]  # Yellow
        lowColor = [255, 0, 0]     # Red

        if self.parent.state.health >= 50.0:
            color = self.interpColor(medColor, highColor, (self.parent.state.health - 50.0) * 2.0)
        else:
            color = self.interpColor(lowColor, medColor, self.parent.state.health * 2.0)

        colorstr = "{:02X}{:02X}{:02X}".format(color[0], color[1], color[2])
        self.healthBar.setStyleSheet("QProgressBar::chunk {{ background-color: #{}; }}".format(colorstr))

    def enableTooltips(self, enabled):
        self.tooltipsEnabled = enabled
        self.setTooltips()

    def setTooltips(self):
        if self.tooltipsEnabled:
            self.planetGroup.setToolTip("the planet you are currently on")
            self.moneyGroup.setToolTip("how much money you currently have")
            self.planetCountGroup.setToolTip("how many planets you have discovered since day 1")
            self.dayGroup.setToolTip('%d days remaining' % (self.parent.state.max_days - self.parent.state.day))
            self.purchasesGroup.setToolTip('%d store purchases remaining today' %
                                           (self.parent.state.max_store_purchases_per_day - self.parent.state.store_purchases))
            self.warehouseTripsGroup.setToolTip('%d warehouse trips remaining today' %
                                                (self.parent.state.warehouse_trips_per_day - self.parent.state.warehouse_trips))

            if self.parent.state.scout_level > 0:
                upper, lower = self.parent.state.planet_discovery_range
                self.scoutFleetGroup.setToolTip("{0:,} - {1:,} new planets per scout expedition".format(upper, lower))
            else:
                self.scoutFleetGroup.setToolTip("Scout expeditions are not possible")

            self.battleFleetGroup.setToolTip('%d%% chance of winning battles' % int(self.parent.state.battle_victory_chance_percentage()))
            self.healthGroup.setToolTip("%d%%" % self.parent.state.health)
        else:
            self.planetGroup.setToolTip(None)
            self.moneyGroup.setToolTip(None)
            self.planetCountGroup.setToolTip(None)
            self.dayGroup.setToolTip(None)
            self.purchasesGroup.setToolTip(None)
            self.warehouseTripsGroup.setToolTip(None)
            self.scoutFleetGroup.setToolTip(None)
            self.battleFleetGroup.setToolTip(None)
            self.healthGroup.setToolTip(None)

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

        self.battleFleetLabel.setText(battle_label_txt)

        if self.parent.state.scout_level == 0:
            scout_label_txt = "No scout fleet"
        else:
            scout_label_txt = '%d/%d' % (self.parent.state.scout_level, self.parent.state.max_scout_level)

        self.scoutFleetLabel.setText(scout_label_txt)

        self.healthBar.setValue(self.parent.state.health)
        self.setHealthBarColor()

        self.setTooltips()

        super(InfoBar, self).update()
