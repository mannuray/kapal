import sys
import PyQt4
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import kapal
import kapal.algo
import kapal.state
import kapal.world
import kapal.tools
import copy
import os

class WorldCanvas(object):
    STATE_OPEN = 0x01
    STATE_CLOSED = 0x02
    STATE_EXPANDED = 0x04
    STATE_START = 0x10
    STATE_GOAL = 0x20
    STATE_PATH = 0x80

    COLOR_RED = (255, 0, 0, 255)
    COLOR_REDTRAN = (255, 0, 0, 128)
    COLOR_BLUE = (0, 80, 255, 255)
    COLOR_DARKBLUE = (0, 0, 128, 255)
    COLOR_GREEN = (0, 255, 0, 255)
    COLOR_YELLOW = (255, 255, 0, 255)
    COLOR_TRANSPARENT = (0, 0, 0, 0)

    def __init__(self):
        self.painter = QtGui.QPainter()

    def draw_image(self, image, x=0, y=0):
        point = QtCore.QPoint(x*self.cell_size, y*self.cell_size)

        try:
            if not self.painter.begin(self):
                raise Exception("painter failed to begin().")
            self.painter.drawImage(point, image)
        finally:
            self.painter.end()

    def draw_square(self, x=0, y=0, color=(0, 0, 0, 0),
            size=None, brush=None, image=None):
        if size is None:
            size = self.cell_size
        if brush is None:
            brush = QtGui.QBrush(QtCore.Qt.SolidPattern)
        brush.setColor(QtGui.QColor(*color))

        # to put square in center of cell
        padding = (self.cell_size-size)/2

        try:
            if not self.painter.begin(self):
                raise Exception("painter failed to begin().")
            self.painter.setBrush(brush)
            self.painter.drawRect(x*self.cell_size + padding, y*self.cell_size +
                    padding, size, size)
        finally:
            self.painter.end()

    def draw_line(self, x1=0, y1=0, x2=0, y2=0, pen=None):
        if pen is None:
            pen = QtGui.QPen(QtCore.Qt.black, 2, QtCore.Qt.DashLine)
            pen.setColor(QtGui.QColor(*WorldCanvas.COLOR_GREEN))

        # to put line in center of cell
        padding = self.cell_size/2

        try:
            if not self.painter.begin(self):
                raise Exception("painter failed to begin().")
            self.painter.setPen(pen)
            self.painter.drawLine(x1*self.cell_size+padding,
                    y1*self.cell_size+padding, x2*self.cell_size+padding,
                    y2*self.cell_size+padding)
        finally:
            self.painter.end()
        
    def draw_circle(self, x=0, y=0, radius=8, color=None):
        if color is None:
            color = WorldCanvas.COLOR_YELLOW
        brush = QtGui.QBrush(QtGui.QColor(*color))

        # to put circle in center of cell
        padding = self.cell_size/2
        center = QtCore.QPointF(x*self.cell_size+padding,
                y*self.cell_size+padding)

        try:
            if not self.painter.begin(self):
                raise Exception("painter failed to begin().")
            self.painter.setBrush(brush)
            self.painter.setRenderHint(QPainter.Antialiasing)
            self.painter.drawEllipse(center, radius, radius)
        finally:
            self.painter.end()

class World2dCanvas(QWidget, WorldCanvas):
    def __init__(self, parent=None, world_cost=None, world_cond=None,
            painter=None):
        QtGui.QWidget.__init__(self, parent)
        WorldCanvas.__init__(self)

        # cost of cells in the world
        if world_cost is None:
            self.world_cost = [[1]]
        self.world_cost = world_cost

        # world_cond is a 2d grid, where each cell holds
        # the condition of that cell
        if world_cond is None:
            self.world_cond = [[0]]
        self.world_cond = world_cond

        # size of each world cell drawn
        self.cell_size = 32

        if painter is None:
            painter = QtGui.QPainter()
        self.painter = painter

    def paintEvent(self, event):
        self.draw_world2d()
        self.update()

    def draw_world2d(self, x_start=0, y_start=0, x_goal=0,
            y_goal=0):

        # previous c, r values of the path, for drawing path lines
        c_prev = -1
        r_prev = -1

        for r in range(len(self.world_cost)):
            for c in range(len(self.world_cost[r])):
                if self.world_cost[r][c] == kapal.inf:
                    # obstacle
                    self.draw_square(c, r, color=WorldCanvas.COLOR_DARKBLUE)
                else:
                    # free space
                    self.draw_square(c, r, color=WorldCanvas.COLOR_BLUE)
                
                # show state of cell

                if self.world_cond[r][c] & WorldCanvas.STATE_PATH:
                    # current cell is part of path
                    if c_prev != -1:
                        self.draw_line(c, r, c_prev, r_prev)
                    c_prev = c
                    r_prev = r

                # draw start point
                if self.world_cond[r][c] & WorldCanvas.STATE_START:
                    #ship_img = QtGui.QImage("icons/ship.png")
                    #self.draw_image(ship_img, c, r)
                    self.draw_circle(r, c, radius=12)
                # draw goal points
                if self.world_cond[r][c] & WorldCanvas.STATE_GOAL:
                    self.draw_circle(r, c, radius=12,
                            color=WorldCanvas.COLOR_GREEN)

                if self.world_cond[r][c] & WorldCanvas.STATE_EXPANDED:
                    # current cell was expanded
                    self.draw_square(c, r, color=WorldCanvas.COLOR_RED,
                            size=8)

class World2dSettingsDock(QDockWidget):
    """Settings for World2d."""

    def __init__(self):
        QDockWidget.__init__(self)

        # size boxes
        self.size_y_box = QtGui.QSpinBox(self)
        self.size_y_box.setMinimum(1)
        self.size_y_box.setValue(10)
        self.size_x_box = QtGui.QSpinBox(self)
        self.size_x_box.setMinimum(1)
        self.size_x_box.setValue(10)

        # start/goal boxes
        self.start_y_box = QtGui.QSpinBox(self)
	self.start_y_box.setMinimum(1)
	self.start_y_box.setValue(2)
        self.start_x_box = QtGui.QSpinBox(self)
	self.start_x_box.setMinimum(1)
	self.start_x_box.setValue(2)
        self.goal_y_box = QtGui.QSpinBox(self)
	self.goal_y_box.setMinimum(1)
	self.goal_y_box.setValue(8)
        self.goal_x_box = QtGui.QSpinBox(self)
	self.goal_x_box.setMinimum(1)
	self.goal_x_box.setValue(8)

        # main box layout
        vbox = QtGui.QVBoxLayout()
        vbox.setAlignment(Qt.AlignTop|Qt.AlignLeft)

        self.randomize = QCheckBox("Randomize World")
        self.randomize.setCheckState(Qt.Checked)
        vbox.addWidget(self.randomize)
        vbox.addWidget(QCheckBox("Traversable Obstacles"))
        
        vbox.addWidget(QLabel("World Size"))
        hbox_world_size = QtGui.QHBoxLayout()
        hbox_world_size.addWidget(QLabel("Y"))
        hbox_world_size.addWidget(self.size_y_box)
        hbox_world_size.addWidget(QLabel("X"))
        hbox_world_size.addWidget(self.size_x_box)
        world_size_widget = QWidget()
        world_size_widget.setLayout(hbox_world_size)
        vbox.addWidget(world_size_widget)

        vbox.addWidget(QLabel("Start"))
        hbox_start = QtGui.QHBoxLayout()
        hbox_start.addWidget(QLabel("Y"))
        hbox_start.addWidget(self.start_y_box)
        hbox_start.addWidget(QLabel("X"))
        hbox_start.addWidget(self.start_x_box)
        start_widget = QtGui.QWidget()
        start_widget.setLayout(hbox_start)
        vbox.addWidget(start_widget)

        vbox.addWidget(QLabel("Goal"))
        hbox_goal = QtGui.QHBoxLayout()
        hbox_goal.addWidget(QLabel("Y"))
        hbox_goal.addWidget(self.goal_y_box)
        hbox_goal.addWidget(QLabel("X"))
        hbox_goal.addWidget(self.goal_x_box)
        goal_widget = QtGui.QWidget()
        goal_widget.setLayout(hbox_goal)
        vbox.addWidget(goal_widget)

        widget = QtGui.QWidget(self)
        widget.setLayout(vbox)
        self.setWidget(widget)

class MainSettingsDock(QDockWidget):
    """Dock for choosing algorithm and world."""

    world_list = ["2D 4 Neighbors", "2D 8 Neighbors"]
    algo_list = ["Dijkstra", "A*"]
    heuristic_list = ["Manhattan", "Euclidean"]

    def __init__(self):
        QDockWidget.__init__(self)
	base_path = os.path.dirname(__file__) + '/'

	self.neighbours = False
	self.algo = kapal.algo.Dijkstra

        # world chooser
        self.world_combo = QtGui.QComboBox()
        self.world_combo.addItems(MainSettingsDock.world_list)
        self.world_combo.setItemIcon(0, QtGui.QIcon(base_path +  'icons/2d_4neigh.png'))
        self.world_combo.setItemIcon(1, QtGui.QIcon(base_path + 'icons/2d_8neigh.png'))
        self.connect(self.world_combo, SIGNAL('currentIndexChanged(int)'),
	             self.update_neighbour)

        # algorithm chooser
        self.algo_combo = QtGui.QComboBox()
        self.algo_combo.addItems(MainSettingsDock.algo_list)
        self.connect(self.algo_combo, SIGNAL('currentIndexChanged(int)'),
                self.update_algo)

        # heuristic chooser
        self.heuristic_combo = QtGui.QComboBox()
        self.heuristic_combo.addItems(MainSettingsDock.heuristic_list)
        self.heuristic_combo.setItemIcon(0, QtGui.QIcon(base_path + 'icons/heur_manhattan.png'))
        self.heuristic_combo.setItemIcon(1, QtGui.QIcon(base_path + 'icons/heur_euclidean.png'))

        # algo settings
        vbox = QtGui.QVBoxLayout()
        vbox.setAlignment(Qt.AlignTop|Qt.AlignHCenter)
        vbox.addWidget(QLabel("World"))
        vbox.addWidget(self.world_combo)
        vbox.addWidget(QLabel("Algorithm"))
        vbox.addWidget(self.algo_combo)
        vbox.addWidget(QLabel("Heuristics"))
        vbox.addWidget(self.heuristic_combo)

        widget = QtGui.QWidget()
        widget.setLayout(vbox)
        self.setWidget(widget)


    def update_neighbour(self, index):
        self.neighbours = True if index == 1 else False
        

    def update_algo(self, index):
        print "algo updated to", index
	self.algo = kapal.algo.AStar if index == 1 else kapal.algo.Dijkstra

class SeashipMainWindow(QMainWindow):
    
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
	base_path = os.path.dirname(__file__) + '/'

        # set up planner
        self.algo_t = kapal.algo.Dijkstra
        self.world_t = kapal.world.World2d
        self.state_t = kapal.state.State2dAStar

        # general GUI settings
        self.setUnifiedTitleAndToolBarOnMac(True)

        # set up window
        self.setGeometry(100, 100, 600, 400)
        self.setWindowTitle('Seaship')
        self.painter = QtGui.QPainter()

        # main settings dock
        self.main_settings = MainSettingsDock()
        self.world_settings = World2dSettingsDock()

        # world canvas
        self.worldcanvas = World2dCanvas(parent=self)
        self.setCentralWidget(self.worldcanvas)
        self.addDockWidget(Qt.RightDockWidgetArea, self.main_settings)
        self.addDockWidget(Qt.RightDockWidgetArea, self.world_settings)

        # built tool bar
        # start button
        start_button = QtGui.QAction(QtGui.QIcon(base_path + 'icons/play.png'),
                'Start', self)
        start_button.setShortcut('Ctrl+R')
        start_button.setStatusTip('Start Planning')
        self.connect(start_button, QtCore.SIGNAL('triggered()'),
                self.plan)

        # stop button
        stop_button = QtGui.QAction(QtGui.QIcon(base_path + 'icons/stop.png'),
                'Stop', self)
        stop_button.setShortcut('Ctrl+T')
        stop_button.setStatusTip('Stop')
        self.connect(stop_button, QtCore.SIGNAL('triggered()'),
                self.reset_world)

        # reset button
        reset_button = QtGui.QAction(QtGui.QIcon(base_path + 'icons/reset.png'),
                'Random', self)
        reset_button.setShortcut('Ctrl+N')
        reset_button.setStatusTip('Randomize World')
        self.connect(reset_button, QtCore.SIGNAL('triggered()'),
                self.random_world_wid)

        toolbar = self.addToolBar('Control')
        toolbar.addAction(reset_button)
        toolbar.addAction(start_button)
        toolbar.addAction(stop_button)
        self.random_world(breath=10, width=10)

        # status bar
        self.statusBar()


    def random_world_wid(self):
        breath = self.world_settings.size_y_box.value()
	width = self.world_settings.size_x_box.value()
	self.random_world(breath, width)

    def random_world(self, breath=10, width=10):
        # set up world

        # World2d
        self.c = kapal.tools.rand_cost_map(breath, width, 1, kapal.inf,
                flip=True, flip_chance=.1)
        self.world_cond = [ [0]*len(self.c[0]) for i in range(len(self.c)) ]
        self.world = kapal.world.World2d(self.c, state_type = kapal.state.State2dAStar, diags=self.main_settings.neighbours)

    def reset_world(self):
        self.world_cond = [ [0]*len(self.c[0]) for i in range(len(self.c)) ]
        self.world.reset()

    def plan(self):
        self.algo_t = self.main_settings.algo
        if (self.algo_t is kapal.algo.Dijkstra or
                self.algo_t is kapal.algo.AStar):
            start_y = self.world_settings.start_y_box.value()
            start_x = self.world_settings.start_x_box.value()
            goal_y = self.world_settings.goal_y_box.value()
            goal_x = self.world_settings.goal_x_box.value()
            self.world_cond[start_y][start_x] |= WorldCanvas.STATE_START
            self.world_cond[goal_y][goal_x] |= WorldCanvas.STATE_GOAL
            astar = self.algo_t(self.world, self.world.state(start_y,start_x),
                    self.world.state(goal_y, goal_x))
            #astar.h = fake_h
            num_popped = 0
            #for s in astar.plan_gen():
            for s in astar.plan():
                self.world_cond[s.y][s.x] |= WorldCanvas.STATE_EXPANDED
                num_popped += 1
            print num_popped
            for s in astar.path():
                self.world_cond[s.y][s.x] |= WorldCanvas.STATE_PATH

    def paintEvent(self, event):
        self.worldcanvas.world_cost = copy.deepcopy(self.c)
        self.worldcanvas.world_cond = self.world_cond
        self.update()

app = QtGui.QApplication(sys.argv)
seawin = SeashipMainWindow()
seawin.show()
app.exec_()
