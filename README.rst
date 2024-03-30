Deep Space Trader
-----------------

Deep Space Trader is a turn-based strategy game inspired by, and similar in gameplay to,
the old DOS game "Drugwars".

Install
=======

Pre-built windows binary
########################

Download the `Windows x64 installer <https://github.com/eriknyquist/deep_space_trader/releases/latest>`_

Python package
##############

Install as a python package:

::

    pip install deep_space_trader

Introduction
============

.. image:: readme_image.png

The player starts off on a planet within a system of 8 randomly-generated planets.
Each planet has various raw materials available for trading (13 types of raw material in total),
all with prices that differ from planet to planet, and fluctuate over time. The goal of the game
is to make as much money as possible by buying and selling raw materials between planets.

The player has an item inventory for raw materials, with a fixed (but upgradeable) capacity.
Only items in the inventory can be bought or sold. The player also has a warehouse with unlimited
capacity. Items can be transferred between the item inventory and the warehouse, but only
a certain number of transfers between item inventory and warehouse can be made per day.

Travelling between planets always incurs a risk of encountering pirates, who may
kill the player or rob them of their money / raw materials. The greater the value that the
player is travelling with (combined value of player's money and items in the player's inventory,
but not the warehouse), the greater the chance of encountering pirates.

The player can use any earned money to buy "upgrades" from a store. Only a certain number of
store purchases can be made per day. Some of the upgrades
allow the player to:

* Destroy planets altogether and acquire all their raw materials
  (Destroying a planet incurs a risk that the planet may fight to resist, which may kill the player)

* Buy and upgrade a battle fleet, which increases chances of winning fights against pirates,
  and against planets that resist destruction

* Buy and upgrade a scout fleet, which allows the player to discover thousands of
  new planets

* Upgrade the player's inventory capacity, which increases the number of items that can
  be bought or sold at once.

* Increment the number of warehouse trips allowed per day

Complete Game Reference
=======================

This following section describes the functionality of all sections of all game windows
in detail. Each game window has its own section in the document, with further document subsections
for sections within the game window.

**Main window**
###############

This section describes the functionality of all sections on the main game window
(the largest window, which opens on game startup). Each section in the main game window
has its own section in this document.

**"Information" section**
+++++++++++++++++++++++++

This section describes the functionality of the "Information" section of the main game window.
The "Information" section stretches across the entire top of the main game window, and
shows useful information about the current state of the game.

* **"Current Planet"**: Shows the name of, and an image of, the current planet the player is on.
* **"Current Day"**: Shows the current day number, against the total number of days before the game ends.
* **"Money"**: Shows the amount of money currently held by the player.
* **"Purchases"**: Shows the number of store purchases made by the player so far on the current day, against
  the total number of store purchases allowed on the current day.
* **"Planets discovered"**: Shows the total number of planets that have been discovered by the player.
  This number includes planets that have not been visited by the player, and planets that have been
  destroyed by the player.
* **"Scout fleet level"**: Shows the current upgrade level of the players scout fleet, against the
  maximum possible upgrade level for the players scout fleet.
* **"Battle fleet"**: Shows the current upgrade level of the players battle fleet, against the
  maximum possible upgrade level for the players battle fleet. Also shows the chance (percentage) of
  the player winning a battle, based on current battle fleet upgrade level.

**Global buttons section**
++++++++++++++++++++++++++

This section describes the functionality of the 3 large buttons at the top of the
main game window, directly underneath the "Information" section.

* **"Reset" button**: Aborts the current game and starts a new game (Warning: player will lose
  all progress in the current game. When clicked, this button will first show a prompt,
  asking the player to confirm that they want to reset the game).

* **"Go to store" button**: Opens the Store window. See "Store window" reference section in this
  document for more details.

* **"Go to next day" button**: Advances the current day by 1. Often, the next day is reached by
  travelling to another planet, but this button advances to the next day without travelling.

**"Planets" section**
+++++++++++++++++++++

This section describes the functionlity of the "Planets" section of the main game
window. The "Planets" section is used for travelling between planets, and allows the player
to select the planet they want to travel to. The "Planets" section is displayed in the middle
left area of the main game window.

* **"Travel..." button**: Causes the player to travel to the selected planet. The player can also
  travel to a planet by double-clicking on the planet name in the "Planets" section. Travelling
  to a planet costs 100 of the player's money, and advances the current day by 1.

* **"Travel to previous" button**: Causes the player to travel to the planet that they were on
  directly before the current planet. Travelling to a planet costs 100 of the player's money,
  and advances the current day by 1.

* **Planet display table**: shows a list of all planets available to the player. Constsist of two
  columns: The rightmost column, labelled "visited?", shows "yes" or "no" indicating whether
  the player has travelled to the planet. The leftmost column, labelled "Planet", shows the
  name of the planet. The player can travel to a planet by double-clicking on the planet name
  within the planet display table.


**"Items on current planet" section**
+++++++++++++++++++++++++++++++++++++

This section describes the functionality of the "Items on current planet" section of the main
game window. The "Items on current planet" section is used for browsing & buying items from
the planet that the player is currently on. The "Items on current planet" section is displayed
in the bottom left area of the main game window.

* **"Buy item" button**: Allows the player to purchase 1 or more of the selected items in the
  item display table. When clicked, this button will open a new window that allows the player to
  select the quantity they wish to purchase of the selected item (See "Buy item window" reference
  section in this document for more details about this window).

* **Item display table**: Displays all items available for purchase on the current planet.
  Consists of three columns: The rightmost column, labelled "Cost", displays the cost of 1
  item. The middle column, labelled "Quantity available", shows the number of items available
  for purchase on the current planet. The leftmost column, labelled "Item type", shows the
  item name. Double-clicking the item name will display a new window showing the item price
  over time (from day 1 until the current day).


**"Items on your ship" section**
++++++++++++++++++++++++++++++++

This section describes the functionality of the "Items on your ship" section of the main
game window. The "Items on your ship" section is used for browsing / managing items that
reside on the players ship, that have either been purchased from a planet or that have been
retrieved from the warehouse. The "Items on your ship" section is displayed in the middle
right area of the main game window.

* **"Sell items" button**: Allows the player to attempt to sell 1 or more of the selected
  item to the current planet. When clicked, this button will open a new window that allows
  the player to select the quantity they wish to sell of the selected item. If the current
  planet does not already hold any of the selected item, then the player will be asked if
  they want to provide a free (small quantity) sample of the item. If the player does not
  provide a free sample, then the item cannot be sold to the current planet. If the player
  does provide a free sample, then the planet may or may not decide to begin trading in
  the selected item. Only one free sample of a given item may be given to the same planet
  in the same day.

* **"Sell all" button**: Allows the player to attempt to sell all items on the ship to
  the current planet. Only items that the current planet already holds will be sold
  (free samples can only be provided via the "Sell items" button).


