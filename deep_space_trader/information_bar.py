from PyQt5 import QtWidgets, QtCore, QtGui

from deep_space_trader.planet_image import PlanetImage
from deep_space_trader import constants as const
from deep_space_trader import reputation
from deep_space_trader.i18n import translate, formatNumber, formatPercent

# Engine power bar colour: solid blue, so it isn't confused with the health bar
ENGINE_BAR_COLOR = "#3399ff"

GROUPBOX_STYLE= "QGroupBox{ font-size: 12px; }"
LABEL_STYLE = "QLabel{ font-size: 14px; }"

class ReputationBar(QtWidgets.QProgressBar):
    """
    Vertical bar from 0 to 100, with a dashed mark where planets start refusing to trade
    """
    def __init__(self, parent):
        super(ReputationBar, self).__init__(parent)
        self.setOrientation(QtCore.Qt.Vertical)
        self.setRange(0, 100)
        self.setFixedWidth(20)
        self.setFormat(None)

    def paintEvent(self, event):
        super(ReputationBar, self).paintEvent(event)

        rect = self.rect().adjusted(1, 1, -1, -1)
        y = rect.bottom() - int(round(rect.height() * const.REFUSE_TRADE_REPUTATION / 100.0))
        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QPen(QtGui.QColor("black"), 1, QtCore.Qt.DashLine))
        painter.drawLine(rect.left(), y, rect.right(), y)
        painter.end()


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

        self.planetGroup = QtWidgets.QGroupBox(self.tr("Current planet"))
        self.planetGroup.setStyleSheet(GROUPBOX_STYLE)
        self.planetGroup.setAlignment(QtCore.Qt.AlignCenter)
        self.planetGroup.setLayout(planetLayout)

        moneyLayout = QtWidgets.QHBoxLayout()
        self.moneyLabel = QtWidgets.QLabel("")
        self.moneyLabel.setStyleSheet(LABEL_STYLE)
        self.moneyLabel.setAlignment(QtCore.Qt.AlignCenter)
        moneyLayout.addWidget(self.moneyLabel)
        self.moneyGroup = QtWidgets.QGroupBox(self.tr("Money"))
        self.moneyGroup.setStyleSheet(GROUPBOX_STYLE)
        self.moneyGroup.setAlignment(QtCore.Qt.AlignCenter)
        self.moneyGroup.setLayout(moneyLayout)

        dailyCostLayout = QtWidgets.QHBoxLayout()
        self.dailyCostLabel = QtWidgets.QLabel("")
        self.dailyCostLabel.setStyleSheet(LABEL_STYLE)
        self.dailyCostLabel.setAlignment(QtCore.Qt.AlignCenter)
        dailyCostLayout.addWidget(self.dailyCostLabel)
        self.dailyCostGroup = QtWidgets.QGroupBox(self.tr("Daily cost"))
        self.dailyCostGroup.setStyleSheet(GROUPBOX_STYLE)
        self.dailyCostGroup.setAlignment(QtCore.Qt.AlignCenter)
        self.dailyCostGroup.setLayout(dailyCostLayout)

        moneyLayout = QtWidgets.QVBoxLayout()
        moneyLayout.addWidget(self.dailyCostGroup)
        moneyLayout.addWidget(self.moneyGroup)

        purchasesLayout = QtWidgets.QHBoxLayout()
        self.purchasesLabel = QtWidgets.QLabel("")
        self.purchasesLabel.setStyleSheet(LABEL_STYLE)
        self.purchasesLabel.setAlignment(QtCore.Qt.AlignCenter)
        purchasesLayout.addWidget(self.purchasesLabel)
        self.purchasesGroup = QtWidgets.QGroupBox(self.tr("Purchases"))
        self.purchasesGroup.setStyleSheet(GROUPBOX_STYLE)
        self.purchasesGroup.setAlignment(QtCore.Qt.AlignCenter)
        self.purchasesGroup.setLayout(purchasesLayout)

        warehouseTripsLayout = QtWidgets.QHBoxLayout()
        self.warehouseTripsLabel = QtWidgets.QLabel("")
        self.warehouseTripsLabel.setStyleSheet(LABEL_STYLE)
        self.warehouseTripsLabel.setAlignment(QtCore.Qt.AlignCenter)
        warehouseTripsLayout.addWidget(self.warehouseTripsLabel)
        self.warehouseTripsGroup = QtWidgets.QGroupBox(self.tr("Warehouse trips"))
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
        self.planetCountGroup = QtWidgets.QGroupBox(self.tr("Planets discovered"))
        self.planetCountGroup.setStyleSheet(GROUPBOX_STYLE)
        self.planetCountGroup.setAlignment(QtCore.Qt.AlignCenter)
        self.planetCountGroup.setLayout(planetCountLayout)

        dayLayout = QtWidgets.QHBoxLayout()
        self.dayLabel = QtWidgets.QLabel("")
        self.dayLabel.setStyleSheet(LABEL_STYLE)
        self.dayLabel.setAlignment(QtCore.Qt.AlignCenter)
        dayLayout.addWidget(self.dayLabel)
        self.dayGroup = QtWidgets.QGroupBox(self.tr("Current day"))
        self.dayGroup.setStyleSheet(GROUPBOX_STYLE)
        self.dayGroup.setAlignment(QtCore.Qt.AlignCenter)
        self.dayGroup.setLayout(dayLayout)

        planetDayLayout = QtWidgets.QVBoxLayout()
        planetDayLayout.addWidget(self.planetCountGroup)
        planetDayLayout.addWidget(self.dayGroup)

        scoutFleetLayout = QtWidgets.QHBoxLayout()
        self.scoutFleetLabel = QtWidgets.QLabel("")
        self.scoutFleetLabel.setStyleSheet(LABEL_STYLE)
        self.scoutFleetLabel.setAlignment(QtCore.Qt.AlignCenter)
        scoutFleetLayout.addWidget(self.scoutFleetLabel)
        self.scoutFleetGroup = QtWidgets.QGroupBox(self.tr("Scout fleet level"))
        self.scoutFleetGroup.setStyleSheet(GROUPBOX_STYLE)
        self.scoutFleetGroup.setAlignment(QtCore.Qt.AlignCenter)
        self.scoutFleetGroup.setLayout(scoutFleetLayout)

        battleFleetLayout = QtWidgets.QHBoxLayout()
        self.battleFleetLabel = QtWidgets.QLabel("")
        self.battleFleetLabel.setStyleSheet(LABEL_STYLE)
        self.battleFleetLabel.setAlignment(QtCore.Qt.AlignCenter)
        battleFleetLayout.addWidget(self.battleFleetLabel)
        self.battleFleetGroup = QtWidgets.QGroupBox(self.tr("Battle fleet level"))
        self.battleFleetGroup.setStyleSheet(GROUPBOX_STYLE)
        self.battleFleetGroup.setAlignment(QtCore.Qt.AlignCenter)
        self.battleFleetGroup.setLayout(battleFleetLayout)

        scoutBattleLayout = QtWidgets.QVBoxLayout()
        scoutBattleLayout.addWidget(self.scoutFleetGroup)
        scoutBattleLayout.addWidget(self.battleFleetGroup)

        healthLayout = QtWidgets.QHBoxLayout()
        self.healthBar = QtWidgets.QProgressBar(self)
        self.healthBar.setOrientation(QtCore.Qt.Vertical)
        self.healthBar.setRange(0, 100)
        self.healthBar.setValue(100)
        self.healthBar.setFixedWidth(20)
        self.healthBar.setStyleSheet("QProgressBar::chunk { background-color: #00FF00; }")
        self.healthBar.setFormat(None)
        healthLayout.addWidget(self.healthBar)
        self.healthGroup = QtWidgets.QGroupBox(self.tr("Health"))
        self.healthGroup.setStyleSheet(GROUPBOX_STYLE)
        self.healthGroup.setAlignment(QtCore.Qt.AlignCenter)
        self.healthGroup.setLayout(healthLayout)
        self.healthGroup.setFixedWidth(60)
        healthLayout.setContentsMargins(5, 5, 5, 5)

        # Engine power: a bar that fills up towards the max. engine power
        engineLayout = QtWidgets.QHBoxLayout()
        self.engineBar = QtWidgets.QProgressBar(self)
        self.engineBar.setOrientation(QtCore.Qt.Vertical)
        self.engineBar.setRange(0, const.MAX_ENGINE_LEVEL)
        self.engineBar.setFixedWidth(20)
        self.engineBar.setStyleSheet("QProgressBar::chunk { background-color: %s; }" % ENGINE_BAR_COLOR)
        self.engineBar.setFormat(None)
        engineLayout.addWidget(self.engineBar)
        self.engineGroup = QtWidgets.QGroupBox(self.tr("Engine power"))
        self.engineGroup.setStyleSheet(GROUPBOX_STYLE)
        self.engineGroup.setAlignment(QtCore.Qt.AlignCenter)
        self.engineGroup.setLayout(engineLayout)
        engineLayout.setContentsMargins(5, 5, 5, 5)

        # Reputation: what the current planet thinks of you, coloured by level
        reputationLayout = QtWidgets.QHBoxLayout()
        self.reputationBar = ReputationBar(self)
        reputationLayout.addWidget(self.reputationBar)
        self.reputationGroup = QtWidgets.QGroupBox(self.tr("Reputation"))
        self.reputationGroup.setStyleSheet(GROUPBOX_STYLE)
        self.reputationGroup.setAlignment(QtCore.Qt.AlignCenter)
        self.reputationGroup.setLayout(reputationLayout)
        reputationLayout.setContentsMargins(5, 5, 5, 5)

        # Wide enough for the titles, which are longer than "Health" (especially when translated)
        for group in (self.engineGroup, self.reputationGroup):
            titleWidth = group.fontMetrics().horizontalAdvance(group.title())
            group.setFixedWidth(max(60, titleWidth + 20))

        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.mainLayout.addWidget(self.planetGroup)
        self.mainLayout.addLayout(moneyLayout)
        self.mainLayout.addLayout(purchasesWarehouseLayout)
        self.mainLayout.addLayout(scoutBattleLayout)
        self.mainLayout.addLayout(planetDayLayout)
        self.mainLayout.addWidget(self.reputationGroup)
        self.mainLayout.addWidget(self.engineGroup)
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
            self.planetGroup.setToolTip(self.tr("the planet you are currently on"))
            self.moneyGroup.setToolTip(self.tr("how much money you currently have"))
            self.planetCountGroup.setToolTip(self.tr("how many planets you have discovered since day 1"))
            # (Counts passed to translate() must be plain variables, or pylupdate5 skips the string)
            days = self.parent.state.max_days - self.parent.state.day
            purchases = self.parent.state.max_store_purchases_per_day - self.parent.state.store_purchases
            trips = self.parent.state.warehouse_trips_per_day - self.parent.state.warehouse_trips
            self.dayGroup.setToolTip(translate("InfoBar", "%Ln days remaining", None, days))
            self.purchasesGroup.setToolTip(translate("InfoBar", "%Ln store purchases remaining today", None, purchases))
            self.warehouseTripsGroup.setToolTip(translate("InfoBar", "%Ln warehouse trips remaining today", None, trips))

            if self.parent.state.scout_level > 0:
                lower, upper = self.parent.state.planet_discovery_range
                self.scoutFleetGroup.setToolTip(translate("InfoBar", "{0} - %Ln new planets per scout expedition",
                                                          "{0} is the smallest number of planets", upper).format(
                                                          formatNumber(lower)))
            else:
                self.scoutFleetGroup.setToolTip(self.tr("Scout expeditions are not possible"))

            self.battleFleetGroup.setToolTip(self.tr("{0} chance of winning battles", "{0} is a percentage").format(
                                             formatPercent(int(self.parent.state.battle_victory_chance_percentage()))))
            cost_per_ly = QtCore.QLocale().toString(self.parent.state.travel_cost_per_ly(), 'f', 2)
            self.engineGroup.setToolTip(self.tr("Engine power {0}/{1}. Travel costs {2} per light-year.").format(
                                        formatNumber(self.parent.state.engine_level),
                                        formatNumber(const.MAX_ENGINE_LEVEL), cost_per_ly))
            self.reputationGroup.setToolTip(self.reputationTooltip())
            self.healthGroup.setToolTip(formatPercent(self.parent.state.health))
            self.dailyCostGroup.setToolTip(self.tr("{0} per day is required to feed yourself and "
                                                   "maintain all purchased services").format(
                                                   formatNumber(self.parent.state.daily_cost)))
        else:
            self.planetGroup.setToolTip(None)
            self.moneyGroup.setToolTip(None)
            self.planetCountGroup.setToolTip(None)
            self.dayGroup.setToolTip(None)
            self.purchasesGroup.setToolTip(None)
            self.warehouseTripsGroup.setToolTip(None)
            self.scoutFleetGroup.setToolTip(None)
            self.battleFleetGroup.setToolTip(None)
            self.engineGroup.setToolTip(None)
            self.reputationGroup.setToolTip(None)
            self.healthGroup.setToolTip(None)
            self.dailyCostGroup.setToolTip(None)

    def reputationTooltip(self):
        planet = self.parent.state.current_planet
        value = self.parent.state.reputation_of(planet)
        description = reputation.describe(value)

        if not self.parent.state.trades_with_you(planet):
            return self.tr("Reputation here: {0}. {1} refuses to trade with you.",
                           "{0} is a reputation, e.g. Hostile (12), and {1} is a planet name").format(
                           description, planet.full_name)

        # How much more (or less) buying costs than normal; selling is the same amount the other way
        percent = int(round((reputation.buyPriceFactor(value) - 1.0) * 100))
        if percent > 0:
            return self.tr("Reputation here: {0}. Prices are {1} worse.",
                           "{0} is a reputation, e.g. Wary (58), and {1} is a percentage").format(
                           description, formatPercent(percent))
        if percent < 0:
            return self.tr("Reputation here: {0}. Prices are {1} better.",
                           "{0} is a reputation, e.g. Allied (90), and {1} is a percentage").format(
                           description, formatPercent(-percent))

        return self.tr("Reputation here: {0}. Prices are normal.",
                       "{0} is a reputation, e.g. Friendly (70)").format(description)

    def update(self):
        self.planetLabel.setText(self.parent.state.current_planet.full_name)
        self.planetImage.update()
        self.dayLabel.setText('%s/%s' % (formatNumber(self.parent.state.day), formatNumber(self.parent.state.max_days)))
        self.moneyLabel.setText(formatNumber(self.parent.state.money))
        self.planetCountLabel.setText(formatNumber(self.parent.state.planets_discovered))
        self.purchasesLabel.setText('%s/%s' % (formatNumber(self.parent.state.store_purchases),
                                               formatNumber(self.parent.state.max_store_purchases_per_day)))
        self.warehouseTripsLabel.setText('%s/%s' % (formatNumber(self.parent.state.warehouse_trips),
                                                    formatNumber(self.parent.state.warehouse_trips_per_day)))

        if self.parent.state.battle_level == 0:
            battle_label_txt = self.tr("No battle fleet")
        else:
            battle_label_txt = '%s/%s' % (formatNumber(self.parent.state.battle_level),
                                          formatNumber(self.parent.state.max_battle_level))

        self.battleFleetLabel.setText(battle_label_txt)

        if self.parent.state.scout_level == 0:
            scout_label_txt = self.tr("No scout fleet")
        else:
            scout_label_txt = '%s/%s' % (formatNumber(self.parent.state.scout_level),
                                         formatNumber(self.parent.state.max_scout_level))

        self.scoutFleetLabel.setText(scout_label_txt)
        self.engineBar.setValue(self.parent.state.engine_level)

        value = self.parent.state.reputation_of(self.parent.state.current_planet)
        self.reputationBar.setValue(reputation.shownNumber(value))
        self.reputationBar.setStyleSheet("QProgressBar::chunk { background-color: %s; }" %
                                         reputation.levelColor(value))

        self.dailyCostLabel.setText(formatNumber(self.parent.state.daily_cost))

        self.healthBar.setValue(self.parent.state.health)
        self.setHealthBarColor()

        self.setTooltips()

        super(InfoBar, self).update()
