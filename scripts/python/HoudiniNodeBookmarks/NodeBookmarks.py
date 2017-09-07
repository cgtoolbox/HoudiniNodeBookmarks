import hashlib
import hou
import os
import time
import json
import tempfile
import ConfigParser
from PySide2 import QtWidgets
from PySide2 import QtGui
from PySide2 import QtCore
Qt = QtCore.Qt

import HoudiniNodeBookmarks
from HoudiniNodeBookmarks import PyPanelCache

ver = hou.applicationVersion()

TOOL_BAR_BUTTON_SIZE = QtCore.QSize(25, 25)
TOOL_BAR_BUTTON_ICON_SIZE = QtCore.QSize(22, 22)
_img = [hou.expandString("$HOME"), "houdini{}.{}".format(ver[0], ver[1]),
       "config", "Icons", r"HoudiniNodeBookmarks\checkmark.svg" ]
IDENT_NETWORK_IMG = os.path.join(*_img)

RECENTS_FILE = tempfile.gettempdir() + os.sep + "houdiniNodeBkm_recents.tmp"
CONFIG_FILE = os.path.dirname(__file__) + os.sep + "config.ini"

def init_bookmark_view():

    w = NodesBookmark()
    PyPanelCache.PYPANEL_CACHE["pypanel"] = w
    return w

def create_boormark(node):

    if hasattr(hou.session, "NODES_BOOKMARK"):
        w = hou.session.NODES_BOOKMARK

    else:
        hou.ui.displayMessage("Init Houdini Nodes Bookmark first.")
        

class Config():

    def __init__(self):

        self.config = ConfigParser.ConfigParser()
        self.config.read(CONFIG_FILE)

    def __set(self, section, entry, value):

        with open(CONFIG_FILE, 'w') as f:
            ConfigFile.config.set(section,
                                  entry,
                                  value)
            ConfigFile.config.write(f)

    def set_node_colors(self, entry, value):

        self.__set("bookmark_colors", entry, value)
    
    def get_node_colors(self, node_type):
        
        try:
            return eval(self.config.get("bookmark_colors", node_type))

        except ConfigParser.NoOptionError:
            hou.ui.displayMessage(("Error: color option '{}' "
                                    "not found in config.ini.".format(node_type)),
                                  severity = hou.severityType.Error)
            return [75, 75, 75]

        except:
            hou.ui.displayMessage(("Error: color option '{}' in "
                                   "config.ini invalid format, mst be: "
                                   "(int) [r, g, b].".format(node_type)),
                                  severity = hou.severityType.Error)
            return [75, 75, 75]

    def set_display_pref(self, entry, value):

        self.__set("display_prefs", entry, value)

    def get_display_pref(self, pref):

        try:
            return self.config.getboolean("display_prefs", pref)

        except ConfigParser.NoOptionError:
            hou.ui.displayMessage(("Error: display pref '{}'"
                                    " not found in config.ini.".format(pref)),
                                    severity = hou.severityType.Error)
            return True

    def set_ui_prefs(self, entry, value):

        self.__set("ui_prefs", entry, value)

    def get_ui_prefs(self, pref):
        
        try:
            return self.config.getboolean("ui_prefs", pref)

        except ConfigParser.NoOptionError:
            hou.ui.displayMessage(("Error: ui pref 'ask_for_name'"
                                    " not found in config.ini."),
                                    severity = hou.severityType.Error)
            return False

        except:
            hou.ui.displayMessage(("Error: ui pref 'ask_for_name'"
                                    " invalid format in config.ini, "
                                    "must be 'True' or 'False'."),
                                    severity = hou.severityType.Error)
            return False

ConfigFile = Config()

class CustomInput(QtWidgets.QDialog):

    def __init__(self, label, icon, defaul_value="", parent=None):
        super(CustomInput, self).__init__(parent=parent)
        
        self.setStyleSheet(hou.ui.qtStyleSheet())
        self.setWindowTitle("Input")
        self.valid_value = False
        main_layout = QtWidgets.QVBoxLayout()

        label_layout = QtWidgets.QHBoxLayout()
        icon_lbl = QtWidgets.QLabel("")
        icon_lbl.setFixedSize(QtCore.QSize(24, 24))
        icon_lbl.setPixmap(hou.ui.createQtIcon(icon).pixmap(20,20))
        label_layout.addWidget(icon_lbl)
        label_layout.addWidget(QtWidgets.QLabel(label))
        main_layout.addLayout(label_layout)

        self.input_text = QtWidgets.QLineEdit(defaul_value)
        main_layout.addWidget(self.input_text)

        main_layout.addWidget(HSep())

        buttons_layout = QtWidgets.QHBoxLayout()
        self.ok_btn = QtWidgets.QPushButton("Ok")
        self.ok_btn.clicked.connect(self.validate_input)
        buttons_layout.addWidget(self.ok_btn)

        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.close)
        buttons_layout.addWidget(self.cancel_btn)

        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)

    def validate_input(self):

        self.valid_value = True
        if self.input_text.text().strip() == "":
            self.valid_value = False
        self.close()

class VSep(QtWidgets.QFrame):

    def __init__(self, parent=None):
        super(VSep, self).__init__(parent=parent)
        self.setFrameShape(QtWidgets.QFrame.VLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.setFixedWidth(1)
        self.setStyleSheet("background-color: black")

class HSep(QtWidgets.QFrame):

    def __init__(self, parent=None):
        super(HSep, self).__init__(parent=parent)
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Plain)
        self.setFixedHeight(2)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Minimum)

class Separator(QtWidgets.QWidget):

    def __init__(self, label, id=0, parent=None):
        super(Separator, self).__init__(parent=parent)
        main_layout = QtWidgets.QHBoxLayout()
        self.setAutoFillBackground(True)
        self.setAcceptDrops(True)

        self.id = id
        self.bookmarkview = parent

        self.children_bg_color = None
        self.children_lbl_color = None

        self.collapsed = False
        self.collapsed_children = []
        self.collapse_btn = QtWidgets.QPushButton("")
        self.collapse_btn.setFlat(True)
        self.collapse_btn.setIcon(hou.ui.createQtIcon(r"HoudiniNodeBookmarks\down"))
        self.collapse_btn.setFixedSize(QtCore.QSize(22, 22))
        self.collapse_btn.setIconSize(QtCore.QSize(18, 18))
        self.collapse_btn.clicked.connect(self.collapse)
        main_layout.addWidget(self.collapse_btn)

        self.collapsed_label = QtWidgets.QLabel("")
        main_layout.addWidget(self.collapsed_label)

        main_layout.addWidget(HSep(self))

        self.label = QtWidgets.QLabel(label)
        main_layout.addWidget(self.label)

        main_layout.addWidget(HSep(self))

        self.setLayout(main_layout)
        
        # right click menu
        self.menu = QtWidgets.QMenu(self)
        self.menu.setStyleSheet(hou.ui.qtStyleSheet())

        edit_ico = hou.ui.createQtIcon(r"HoudiniNodeBookmarks\edit")
        self.edit_label_act = QtWidgets.QAction(edit_ico,
                                                "Edit Label", self)
        self.edit_label_act.triggered.connect(self.edit_label)
        self.menu.addAction(self.edit_label_act)

        color_ico = hou.ui.createQtIcon(r"HoudiniNodeBookmarks\color")
        self.edit_color_act = QtWidgets.QAction(color_ico,
                                                "Edit Children Background Color", self)
        self.edit_color_act.triggered.connect(self.pick_color)
        self.menu.addAction(self.edit_color_act)

        color_txt_ico = hou.ui.createQtIcon(r"HoudiniNodeBookmarks\text_color")
        self.edit_txt_color_act = QtWidgets.QAction(color_txt_ico,
                                                "Edit Children Label Color", self)
        self.edit_txt_color_act.triggered.connect(self.pick_txt_color)
        self.menu.addAction(self.edit_txt_color_act)

        self.menu.addSeparator()

        rem_ico = hou.ui.createQtIcon(r"HoudiniNodeBookmarks\remove")
        self.remove_act = QtWidgets.QAction(rem_ico,
                                            "Remove Bookmark", self)
        self.remove_act.triggered.connect(self.remove_me)
        self.menu.addAction(self.remove_act)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.pop_menu)

    def copy(self, parent):

        s = Separator(self.label.text(), self.id, parent=parent)
        return s

    def find_widgets_to_collapse(self):

        c = self.bookmarkview.bookmark_view_layout.count()

        widgets = []
        start = False

        for i in range(c):
            it = self.bookmarkview.bookmark_view_layout.itemAt(i)
            if it:

                w = it.widget()
                if not w: continue

                if start:
                    if  isinstance(w, Separator):
                        return widgets
                    widgets.append(w)
            
                if w.id == self.id:
                    start = True

        return widgets           

    def collapse(self):

        if self.collapsed:
            self.collapsed = False
            self.collapse_btn.setIcon(hou.ui.createQtIcon(r"HoudiniNodeBookmarks\down"))
            self.collapsed_label.setText("")

            for w in self.find_widgets_to_collapse():
                w.collapsed = False
                w.show()

        else:
            self.collapsed = True
            self.collapse_btn.setIcon(hou.ui.createQtIcon(r"HoudiniNodeBookmarks\right"))
            
            widgets = self.find_widgets_to_collapse()
            for w in widgets:
                w.collapsed = True
                w.hide()

            self.collapsed_label.setText("(" + str(len(widgets)) + ")")

    def data(self):

        return {"type":"separator",
                "name":self.label.text(),
                "id":self.id}

    def pop_menu(self):

        self.menu.popup(QtGui.QCursor.pos())

    def remove_me(self):

        self.setParent(None)
        self.deleteLater()
        self.bookmarkview.refresh_bookmark_ids()

    def edit_label(self):

        r, v = hou.ui.readInput("Separator name:",
                                buttons=["Ok", "Cancel"],
                                initial_contents=self.label.text())
        if r == 1: return

        self.label.setText(v)

    def pick_color(self):

        init_col = QtGui.QColor()
        opt = QtWidgets.QColorDialog.DontUseNativeDialog 
        c = QtWidgets.QColorDialog.getColor(init_col,
                                            None,
                                            "Pick a color",
                                            opt)
        if c.isValid():
            color = [c.red(), c.green(), c.blue()]
            for w in self.find_widgets_to_collapse():
                w.color = color
                w.set_colors()

    def pick_txt_color(self):

        init_col = QtGui.QColor()
        opt = QtWidgets.QColorDialog.DontUseNativeDialog 
        c = QtWidgets.QColorDialog.getColor(init_col,
                                            None,
                                            "Pick a color",
                                            opt)
        if c.isValid():
            color = [c.red(), c.green(), c.blue()]
            for w in self.find_widgets_to_collapse():
                w.text_color = color
                w.set_colors()

    def mouseMoveEvent(self, e):
        
        if e.buttons() != QtCore.Qt.LeftButton:
            return
        
        pixmap = self.grab()
        mimeData = QtCore.QMimeData()
        mimeData.setText("breaker|%|" + str(self.id))

        # if the separator is collapsed, save the collapsed children to move
        # them with the separator
        if self.collapsed:
            self.collapsed_children = self.find_widgets_to_collapse()
        else:
            self.collapsed_children = []

        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)
        drag.setPixmap(pixmap)
        drag.setHotSpot(e.pos())
        drag.exec_()

    def dragEnterEvent(self, e):
        e.acceptProposedAction()

    def dropEvent(self, e):

        e.acceptProposedAction()
        data = e.mimeData()
        node_path = data.text()

        if node_path == "%breaker%":
            self.bookmarkview.insert_breaker(self.id)
            return True

        if "|%|" in node_path:

            id = int(node_path.split("|%|")[-1])
            it = self.bookmarkview.bookmark_view_layout.itemAt(id)
            w = it.widget()
            if isinstance(w, Separator):
                print w.collapsed_children
            c = w.copy(self.bookmarkview)
            self.bookmarkview.bookmark_view_layout.removeItem(it)
            w.setParent(None)
            w.deleteLater()
            self.bookmarkview.bookmark_view_layout.insertWidget(self.id, c)
            
            self.bookmarkview.refresh_bookmark_ids()
            
        else:
            self.bookmarkview.insert_bookmark(node_path, self.id + 1)

        return True

class AddSeparator(QtWidgets.QLabel):

    def __init__(self, parent=None):
        super(AddSeparator, self).__init__(parent=parent)
        ico = hou.ui.createQtIcon(r"HoudiniNodeBookmarks\break")
        self.setPixmap(ico.pixmap(24, 24))
        self.setToolTip(("Add a separator line "
                         "by drag and drop."))

    def mouseMoveEvent(self, e):
        
        if e.buttons() != QtCore.Qt.LeftButton:
            return
        
        pixmap = self.grab()
        mimeData = QtCore.QMimeData()
        mimeData.setText("%breaker%")

        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)
        drag.setPixmap(pixmap)
        drag.setHotSpot(e.pos())
        drag.exec_()

class NetworkViewChooser(QtWidgets.QMainWindow):

    def __init__(self, network_linked=[], parent=None):
        super(NetworkViewChooser, self).__init__(parent=parent)

        cw = QtWidgets.QWidget()
        self.setProperty("houdiniStyle", True)

        self.bookmark_view = parent

        editors = [pane for pane in hou.ui.paneTabs() if \
                   isinstance(pane, hou.NetworkEditor)]

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setSpacing(5)

        main_layout.addWidget(QtWidgets.QLabel(("Choose Network view to"
                                                " be affected by bookmarks:")))
        self.editor_choosers = []

        for e in editors:
            checked = e in network_linked
            ntw = NetworkviewInfo(e, checked, self)
            self.editor_choosers.append(ntw)
            main_layout.addWidget(ntw)

        main_layout.addWidget(HSep())

        button_layout = QtWidgets.QHBoxLayout()

        ok_btn = QtWidgets.QPushButton("Ok")
        ok_btn.clicked.connect(self.valid_links)
        button_layout.addWidget(ok_btn)

        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(cancel_btn)

        main_layout.addLayout(button_layout)

        cw.setLayout(main_layout)
        self.setCentralWidget(cw)

    def valid_links(self):
        
        choices = []

        for e in self.editor_choosers:

            if e.enable_checkbox.isChecked():
                choices.append(e.networkview)

        if len(choices) == 0:
            r = hou.ui.displayMessage("No networkview selected, continue ?",
                                      buttons=["Ok", "Cancel"])
            if r == 1: return

        self.bookmark_view.update_network_linked(choices)

        self.close()

class NetworkviewInfo(QtWidgets.QWidget):

    def __init__(self, networkview, checked=False, parent=None):
        super(NetworkviewInfo, self).__init__(parent=parent)

        main_layout = QtWidgets.QHBoxLayout()
        main_layout.setAlignment(Qt.AlignLeft)

        self.networkview = networkview

        self.enable_checkbox = QtWidgets.QCheckBox()
        self.enable_checkbox.setChecked(checked)
        main_layout.addWidget(self.enable_checkbox)

        main_layout.addWidget(QtWidgets.QLabel(networkview.name()))

        self.identity_button = QtWidgets.QPushButton("Identify")
        self.identity_button.clicked.connect(self.identify_network)
        main_layout.addWidget(self.identity_button)

        self.setLayout(main_layout)

    def identify_network(self):

        img = IDENT_NETWORK_IMG
        
        if not os.path.exists(img):
            img = None

        p = self.networkview.pane()
        tab = p.currentTab()
        tab.setIsCurrentTab()

        self.networkview.flashMessage(img,
                                      self.networkview.name(),
                                      2)

class Bookmark(QtWidgets.QFrame):

    def __init__(self, **kwargs):
        super(Bookmark, self).__init__(parent=kwargs["parent"])

        self.setProperty("houdiniStyle", True)
        self.setFixedHeight(32)
        self.setAutoFillBackground(True)
        self.setObjectName("bookmark")
        self.setAcceptDrops(True)

        self.collapsed = False

        self.node = kwargs["node"]
        self.node_path = self.node.path()
        self.node_name = self.node.name()
        self.node_type = self.node.type()
        self.bookmark_name = kwargs["name"]

        cat = self.node.type().category()
        self.node_cat = cat.name()

        if not kwargs.get("color"):

            if self.node_cat == "Object":
                self.color = ConfigFile.get_node_colors("OBJ")
            elif self.node_cat == "Sop":
                self.color = ConfigFile.get_node_colors("SOP")
            elif self.node_cat == "Vop":
                self.color = ConfigFile.get_node_colors("VOP")
            elif self.node_cat == "Driver":
                self.color = ConfigFile.get_node_colors("OUT")
            elif self.node_cat == "Cop2":
                self.color = ConfigFile.get_node_colors("COP")
            elif self.node_cat == "Chop":
                self.color = ConfigFile.get_node_colors("CHL")
            elif self.node_cat == "Shop":
                self.color = ConfigFile.get_node_colors("SHP")
            else:
                self.color = ConfigFile.get_node_colors("OTH")
        else:
            self.color = kwargs["color"]

        if not kwargs.get("text_color"):
            self.text_color = [203, 203, 203]
        else:
            self.text_color = kwargs["text_color"]
        self.id = kwargs["id"]
        self.uid = kwargs["uid"]
        self.bookmarkview = kwargs["parent"]
        
        self.setToolTip(self.node_path)

        bookmark_layout = QtWidgets.QHBoxLayout()
        bookmark_layout.setSpacing(5)
        bookmark_layout.setAlignment(Qt.AlignLeft)

        try:
            icon = hou.ui.createQtIcon(self.node_type.icon())
        except hou.OperationFailed:
            icon = hou.ui.createQtIcon("SOP_subnet")
        self.icon_lbl = QtWidgets.QLabel("")
        self.icon_lbl.setStyleSheet("QLabel{border: 0px}")
        self.icon_lbl.setPixmap(icon.pixmap(22, 22))
        self.icon_lbl.setFixedHeight(22)
        self.icon_lbl.setFixedWidth(22)
        bookmark_layout.addWidget(self.icon_lbl)

        self.label = QtWidgets.QLabel(self.bookmark_name)
        self.label.setObjectName("bookmarkName")
        bookmark_layout.addWidget(self.label)
        
        self.type_name_label = QtWidgets.QLabel('(' + self.node_type.name() + ')')
        self.type_name_label.setObjectName("nodeTypeName")
        bookmark_layout.addWidget(self.type_name_label)

        # right click menu
        self.menu = QtWidgets.QMenu(self)
        self.menu.setStyleSheet(hou.ui.qtStyleSheet())

        edit_ico = hou.ui.createQtIcon(r"HoudiniNodeBookmarks\edit")
        self.edit_label_act = QtWidgets.QAction(edit_ico,
                                                "Edit Label", self)
        self.edit_label_act.triggered.connect(self.edit_name)
        self.menu.addAction(self.edit_label_act)

        color_ico = hou.ui.createQtIcon(r"HoudiniNodeBookmarks\color")
        self.edit_color_act = QtWidgets.QAction(color_ico,
                                                "Edit Background Color", self)
        self.edit_color_act.triggered.connect(self.pick_color)
        self.menu.addAction(self.edit_color_act)

        color_txt_ico = hou.ui.createQtIcon(r"HoudiniNodeBookmarks\text_color")
        self.edit_txt_color_act = QtWidgets.QAction(color_txt_ico,
                                                "Edit Label Color", self)
        self.edit_txt_color_act.triggered.connect(self.pick_txt_color)
        self.menu.addAction(self.edit_txt_color_act)

        default_bg_col_ico = hou.ui.createQtIcon(r"HoudiniNodeBookmarks\palette")
        self.setcol_as_default = QtWidgets.QAction(default_bg_col_ico,
                                                "Set Current BG color as default", self)
        self.setcol_as_default.triggered.connect(self.set_default_col)
        self.menu.addAction(self.setcol_as_default)

        self.menu.addSeparator()

        rem_ico = hou.ui.createQtIcon(r"HoudiniNodeBookmarks\remove")
        self.remove_act = QtWidgets.QAction(rem_ico,
                                            "Remove Bookmark", self)
        self.remove_act.triggered.connect(self.remove_me)
        self.menu.addAction(self.remove_act)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.pop_menu)

        self.setLayout(bookmark_layout)
        self.set_colors()
        
    def copy(self, parent):

        c = Bookmark(parent=parent,
                     id=self.id,
                     uid=self.uid,
                     name=self.bookmark_name,
                     node=self.node,
                     color=self.color,
                     text_color=self.text_color)
        return c

    def data(self):

        return {"type":"bookmark",
                "name":self.bookmark_name,
                "node_path":self.node_path,
                "color":self.color,
                "text_color":self.text_color,
                "id":self.id,
                "uid":self.uid}

    def pop_menu(self):

        self.menu.popup(QtGui.QCursor.pos())

    def remove_me(self, refresh_ids=True):

        self.setParent(None)
        self.deleteLater()
        if self.uid in self.bookmarkview.bookmarks.keys():
            del(self.bookmarkview.bookmarks[self.uid])

        if refresh_ids:
            self.bookmarkview.refresh_bookmark_ids()

    def edit_name(self):

        r, n = hou.ui.readInput("Enter a name:",
                                buttons=["Ok", "Cancel"],
                                initial_contents=self.bookmark_name)
        if r == 1: return
        self.bookmark_name = n
        self.label.setText(n)

    def set_default_col(self):

        ini_entry = ""
        if self.node_cat == "Object":
            ini_entry = "obj"
        elif self.node_cat == "Sop":
            ini_entry = "sop"
        elif self.node_cat == "Vop":
            ini_entry = "vop"
        elif self.node_cat == "Driver":
            ini_entry = "out"
        elif self.node_cat == "Cop2":
            ini_entry = "cop"
        elif self.node_cat == "Chop":
            ini_entry = "chl"
        elif self.node_cat == "Shop":
            ini_entry = "shp"
        else:
            ini_entry = "oth"

        if ini_entry == "": return
        
        ConfigFile.set_node_colors(ini_entry,
                                   ", ".join([str(c) for c in self.color]))

    def pick_color(self):

        init_col = QtGui.QColor(*self.color)
        opt = QtWidgets.QColorDialog.DontUseNativeDialog 
        c = QtWidgets.QColorDialog.getColor(init_col,
                                            None,
                                            "Pick a color",
                                            opt)
        if c.isValid():
            self.color = [c.red(), c.green(), c.blue()]
            self.set_colors()

    def pick_txt_color(self):

        init_col = QtGui.QColor(*self.text_color)
        opt = QtWidgets.QColorDialog.DontUseNativeDialog 
        c = QtWidgets.QColorDialog.getColor(init_col,
                                            None,
                                            "Pick a color",
                                            opt)
        if c.isValid():
            self.text_color = [c.red(), c.green(), c.blue()]
            self.set_colors()

    def set_colors(self):

        bg_color = "rgb({0}, {1}, {2})".format(*self.color)
        bg_hover_color = [c - 50 if c > 200 else c + 50 for c in self.color]
        bg_hover_color = "rgb({0}, {1}, {2})".format(*bg_hover_color)
        
        text_col = "rgb({0}, {1}, {2})".format(*self.text_color)
        text_type_col = [c - 50 if c > 60 else c for c in self.text_color]
        text_type_col = "rgb({0}, {1}, {2})".format(*text_type_col)
        
        
        self.setStyleSheet("""QFrame:QLabel #nodeTypeName{{color: {0};
                                                           border: 0px;
                                                           background-color: transparent}}

                              QFrame:QLabel #bookmarkName{{color: {1};
                                                           border: 0px;
                                                           background-color: transparent;
                                                           font-weight: bold}}

                              QFrame{{background-color: {2}}}
                              QFrame:hover{{border: 1px solid {3}}}
                              """.format(text_type_col,
                                         text_col,
                                         bg_color,
                                         bg_hover_color))

    def mouseDoubleClickEvent(self, e):

        n = hou.node(self.node_path)
        if not n:
            r = hou.ui.displayMessage(("Node doesn't exist anymore,"
                                       " delete bookmark ?"),
                                      buttons=["Ok", "Cancel"])
            if r == 0:
                self.remove_me()
            return
            
        # select the node and make it current
        n.setCurrent(True, True)
        n.setSelected(True, True)

        # get all the networkviews to be affected
        networks = self.bookmarkview.get_linked_network()
        for ntw in networks:
            
            ntw.setCurrentNode(n)
            rect = ntw.itemRect(n)
            ntw.frameSelection()
            ntw.homeToSelection()

    def mouseMoveEvent(self, e):
        
        if e.buttons() != QtCore.Qt.LeftButton:
            return
        
        pixmap = self.grab()
        mimeData = QtCore.QMimeData()
        mimeData.setText("bookmark|%|" + str(self.id))

        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)
        drag.setPixmap(pixmap)
        drag.setHotSpot(e.pos())
        drag.exec_()

    def dropEvent(self, e):
        
        e.accept()
        data = e.mimeData()
        node_path = data.text()

        if node_path == "%breaker%":
            self.bookmarkview.insert_breaker(self.id)

        elif "|%|" in node_path:

            id = int(node_path.split("|%|")[-1])
            it = self.bookmarkview.bookmark_view_layout.itemAt(id)
            w = it.widget()
            c = w.copy(self.bookmarkview)
            self.bookmarkview.bookmark_view_layout.removeItem(it)
            w.setParent(None)
            w.deleteLater()
            self.bookmarkview.bookmark_view_layout.insertWidget(self.id, c)
            self.bookmarkview.bookmark_view_layout.update()
            
            # if it is a separator, check if any collapsed widgets
            # need to be moved
            if isinstance(w, Separator):

                colw = w.collapsed_children
                w.collapsed_children = []
                w.collapsed = False

                for i, _w in enumerate(colw):
                    copyw = _w.copy(self.bookmarkview)
                    _w.remove_me(False)
                    self.bookmarkview.bookmark_view_layout.insertWidget(self.id,
                                                                        copyw)
            
            self.bookmarkview.refresh_bookmark_ids()

        else:
            self.bookmarkview.insert_bookmark(node_path, self.id)

        return True

class BookmarkView(QtWidgets.QWidget):

    def __init__(self, parent= None):
        super(BookmarkView, self).__init__(parent=parent)

        self.setProperty("houdiniStyle", True)
        self.setAcceptDrops(True)
        self.nodeBookmarks = parent

        self.bookmarks = {}

        self.bookmark_view_layout = QtWidgets.QVBoxLayout()
        self.bookmark_view_layout.setAlignment(Qt.AlignTop)
        
        self.setLayout(self.bookmark_view_layout)

    def reset_filter(self):

        for bkm in self.bookmarks.itervalues():

            if not bkm.collapsed:

                bkm.show()

    def update_filter(self, filter, mode):
        
        filter = str(filter)

        if filter.strip() == "":
            self.reset_filter()
            return

        for bkm in self.bookmarks.itervalues():

            if not bkm.collapsed:

                if mode == "bookmark":
                    if filter in bkm.bookmark_name:
                        bkm.show()
                    else:
                        bkm.hide()

                else:
                    if filter in bkm.node_name:
                        bkm.show()
                    else:
                        bkm.hide()

    def dragMoveEvent(self, e):
        
        e.acceptProposedAction()

    def dropEvent(self, e):
        
        e.acceptProposedAction()
        
        data = e.mimeData()
        node_path = data.text()
        
        if node_path == "%breaker%":
            self.insert_breaker(len(self.children()))
            return True

        self.insert_bookmark(node_path,
                             len(self.children()))  
        return True
              
    def insert_bookmark(self, node_path, idx=-1):

        h_node_path = hashlib.sha1(node_path)
        h_node_path = h_node_path.hexdigest()

        if h_node_path in self.bookmarks.keys():
            bname = self.bookmarks[h_node_path].bookmark_name
            r = hou.ui.displayMessage(("Bookmark for this node already exists: '{}'"
                                      "\nAdd a another one ?".format(bname)),
                                      buttons=["Yes", "No"])
            if r == 1: return

        node = hou.node(node_path)
        if node is None:
            return

        if ConfigFile.get_ui_prefs("ask_for_name"):
            r, bookmark_name = hou.ui.readInput("Enter a name:",
                                                initial_contents=node.name(),
                                                buttons=["Ok", "Cancel"])
            if r == 1: return
        else:
            bookmark_name = node.name()

        if idx == -1:
            idx = self.bookmark_view_layout.count()

        bookmark = Bookmark(node=node,
                            uid=h_node_path,
                            name=bookmark_name,
                            parent=self,
                            id=idx)

        self.bookmarks[h_node_path] = bookmark
        self.bookmark_view_layout.insertWidget(idx, bookmark)
        
        self.refresh_bookmark_ids()
        self.bookmark_view_layout.update()
        self.update()

    def insert_breaker(self, idx=0):
        
        r, breaker_name = hou.ui.readInput("Enter a name:",
                                            initial_contents="Separator",
                                            buttons=["Ok", "Cancel"])
        if r == 1: return

        b = Separator("Separator", idx, parent=self)
        self.bookmark_view_layout.insertWidget(idx, b)

        self.refresh_bookmark_ids()

    def refresh_bookmark_ids(self):

        c = self.bookmark_view_layout.count()
        for i in range(c):
            it = self.bookmark_view_layout.itemAt(i)
            if it:
                w = it.widget()
                if w:
                    w.id = i

    def get_linked_network(self):

        return self.nodeBookmarks.linked_network_views

    def get_bookmark(self, node_path):

        h_node_path = hashlib.sha1(node_path)
        h_node_path = h_node_path.hexdigest()

        return self.bookmarks.get(h_node_path)

    def get_data(self):
        
        data = []
        
        c = self.bookmark_view_layout.count()
        for i in range(c):
            it = self.bookmark_view_layout.itemAt(i)
            if it:
                data.append(it.widget().data())
        
        return data
        
class NodesBookmark(QtWidgets.QMainWindow):

    def __init__(self):
        super(NodesBookmark, self).__init__()

        cw = QtWidgets.QWidget()

        self.setProperty("houdiniStyle", True)
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)

        # menu
        menu_bar = QtWidgets.QMenuBar(self)

        main_menu = QtWidgets.QMenu("File", self)

        sav_ico = hou.ui.createQtIcon(r"HoudiniNodeBookmarks\save")
        save_act = QtWidgets.QAction(sav_ico,
                                     "Save to file",
                                     self)
        save_act.triggered.connect(self.save_bookmarks)
        main_menu.addAction(save_act)

        open_ico = hou.ui.createQtIcon(r"HoudiniNodeBookmarks\open")
        open_act = QtWidgets.QAction(open_ico,
                                     "Open from file",
                                     self)
        open_act.triggered.connect(self.open_bookmarks)
        main_menu.addAction(open_act)
        
        # recent menu
        self.recent_files = []
        self.recents_menu = QtWidgets.QMenu("Open Recent", self)
        main_menu.addMenu(self.recents_menu)

        main_menu.addSeparator()

        sav_hip_ico = hou.ui.createQtIcon(r"HoudiniNodeBookmarks\to_hip")
        save_to_hip_act = QtWidgets.QAction(sav_hip_ico,
                                     "Save to hip file",
                                     self)

        save_to_hip_act.triggered.connect(self.save_to_hip)
        main_menu.addAction(save_to_hip_act)

        open_hip_ico = hou.ui.createQtIcon(r"HoudiniNodeBookmarks\from_hip")
        open_from_hip_act = QtWidgets.QAction(open_hip_ico,
                                     "Open from hip file",
                                     self)
        open_from_hip_act.triggered.connect(lambda: self.check_hip_file_data(verbose=True))
        main_menu.addAction(open_from_hip_act)

        delete_hip_ico = hou.ui.createQtIcon(r"HoudiniNodeBookmarks\clear_hip")
        delete_hip_data_act = QtWidgets.QAction(delete_hip_ico,
                                     "Delete hip file data",
                                     self)
        delete_hip_data_act.triggered.connect(self.delete_hip_file_data)
        main_menu.addAction(delete_hip_data_act)

        main_menu.addSeparator()

        # clear
        clear_ico = hou.ui.createQtIcon(r"HoudiniNodeBookmarks\close")
        clear_act = QtWidgets.QAction(clear_ico,
                                     "Clear Bookmarks",
                                     self)
        clear_act.triggered.connect(self.clear_bookmarks)
        main_menu.addAction(clear_act)

        menu_bar.addMenu(main_menu)

        # options menu
        options_menu = QtWidgets.QMenu("Options", self)

        self.ask_name_act = QtWidgets.QAction("Ask for name on creation", self)
        self.ask_name_act.setCheckable(True)
        self.ask_name_act.setChecked(ConfigFile.get_ui_prefs("ask_for_name"))
        self.ask_name_act.triggered.connect(lambda: self.update_opts("ask_for_name"))

        options_menu.addAction(self.ask_name_act)

        self.display_options_act = QtWidgets.QAction("Display Options", self)
        self.display_options_act.setCheckable(True)
        self.display_options_act.setChecked(ConfigFile.get_ui_prefs("display_options"))
        self.display_options_act.triggered.connect(lambda: self.update_opts("display_options"))

        options_menu.addAction(self.display_options_act)

        self.display_filter_act = QtWidgets.QAction("Display Filter", self)
        self.display_filter_act.setCheckable(True)
        self.display_filter_act.setChecked(ConfigFile.get_ui_prefs("display_filter"))
        self.display_filter_act.triggered.connect(lambda: self.update_opts("display_filter"))

        options_menu.addAction(self.display_filter_act)

        menu_bar.addMenu(options_menu)

        # help menu
        help_menu = QtWidgets.QMenu("Help", self)

        help_ico = hou.ui.createQtIcon(r"HoudiniNodeBookmarks\help")
        help_act = QtWidgets.QAction(help_ico,
                                     "Show Online Help",
                                     self)
        help_act.triggered.connect(self.show_help)
        help_menu.addAction(help_act)

        about_ico = hou.ui.createQtIcon(r"HoudiniNodeBookmarks\about")
        about_act = QtWidgets.QAction(about_ico,
                                      "About",
                                      self)
        help_act.triggered.connect(self.show_about)
        help_menu.addAction(about_act)
        
        menu_bar.addMenu(help_menu)

        # apply menu
        self.setMenuBar(menu_bar)
        
        # toolbar
        toolbar_layout = QtWidgets.QHBoxLayout()
        toolbar_layout.setAlignment(Qt.AlignLeft)
        
        # show icon
        self.show_icon_btn = QtWidgets.QPushButton("")
        self.show_icon_btn.setFixedSize(TOOL_BAR_BUTTON_SIZE)
        self.show_icon_btn.setIcon(hou.ui.createQtIcon(r"HoudiniNodeBookmarks\ico"))
        self.show_icon_btn.setIconSize(TOOL_BAR_BUTTON_ICON_SIZE)
        self.show_icon_btn.setCheckable(True)
        self.show_icon_btn.setChecked(ConfigFile.get_display_pref("show_icon"))
        self.show_icon_btn.setToolTip("Show bookmark's icon")
        self.show_icon_btn.clicked.connect(self.update_icon)
        self.show_icon_btn.setVisible(ConfigFile.get_ui_prefs("display_options"))
        toolbar_layout.addWidget(self.show_icon_btn)

        # show labels
        self.show_label_btn = QtWidgets.QPushButton("")
        self.show_label_btn.setFixedSize(TOOL_BAR_BUTTON_SIZE)
        self.show_label_btn.setIcon(hou.ui.createQtIcon(r"HoudiniNodeBookmarks\label"))
        self.show_label_btn.setIconSize(TOOL_BAR_BUTTON_ICON_SIZE)
        self.show_label_btn.setCheckable(True)
        self.show_label_btn.setChecked(ConfigFile.get_display_pref("show_label"))
        self.show_label_btn.setToolTip("Show bookmark's label")
        self.show_label_btn.clicked.connect(self.update_label)
        self.show_label_btn.setVisible(ConfigFile.get_ui_prefs("display_options"))
        toolbar_layout.addWidget(self.show_label_btn)

        # show types
        self.show_type_btn = QtWidgets.QPushButton("")
        self.show_type_btn.setFixedSize(TOOL_BAR_BUTTON_SIZE)
        self.show_type_btn.setIcon(hou.ui.createQtIcon(r"HoudiniNodeBookmarks\type"))
        self.show_type_btn.setIconSize(TOOL_BAR_BUTTON_ICON_SIZE)
        self.show_type_btn.setCheckable(True)
        self.show_type_btn.setChecked(ConfigFile.get_display_pref("show_type"))
        self.show_type_btn.setToolTip("Show bookmark node's type")
        self.show_type_btn.clicked.connect(self.update_type)
        self.show_type_btn.setVisible(ConfigFile.get_ui_prefs("display_options"))
        toolbar_layout.addWidget(self.show_type_btn)

        # add a separator
        self.toolbar_sep = VSep(self)
        self.toolbar_sep.setVisible(ConfigFile.get_ui_prefs("display_options"))
        toolbar_layout.addWidget(self.toolbar_sep)

        # add separator ( by drag and drop )
        self.add_separator_btn = AddSeparator(self)
        self.add_separator_btn.setVisible(ConfigFile.get_ui_prefs("display_options"))
        toolbar_layout.addWidget(self.add_separator_btn)

        main_layout.addLayout(toolbar_layout)

        # search line
        filter_layout = QtWidgets.QHBoxLayout()
        filter_layout.setSpacing(5)
        filter_layout.setAlignment(Qt.AlignLeft)

        self.filter_lbl = QtWidgets.QLabel("Filter:")
        self.filter_lbl.setVisible(ConfigFile.get_ui_prefs("display_filter"))
        filter_layout.addWidget(self.filter_lbl)

        self.filter_mode = "bookmark"
        self.filter_btn = QtWidgets.QPushButton("")
        self.filter_btn.setFixedHeight(22)
        self.filter_btn.setFixedWidth(22)
        self.filter_btn.setFlat(True)
        self.filter_btn.setIcon(hou.ui.createQtIcon(r"HoudiniNodeBookmarks\book"))
        self.filter_btn.setIconSize(QtCore.QSize(20, 20))
        self.filter_btn.setToolTip("Filter by bookmark's names.")
        self.filter_btn.clicked.connect(self.update_filter_mode)
        self.filter_btn.setVisible(ConfigFile.get_ui_prefs("display_filter"))
        filter_layout.addWidget(self.filter_btn)

        self.filter_input = QtWidgets.QLineEdit()
        self.filter_input.setVisible(ConfigFile.get_ui_prefs("display_filter"))
        self.filter_input.textChanged.connect(self.update_filter)

        filter_layout.addWidget(self.filter_input)

        main_layout.addLayout(filter_layout)

        # scroll area ( where bookmark are added )
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setStyleSheet("background-color: transparent")
        scroll_area.setWidgetResizable(True)

        self.bookmark_view = BookmarkView(self)
        scroll_area.setWidget(self.bookmark_view)
        main_layout.addWidget(scroll_area)

        # network link
        network_link_layout = QtWidgets.QHBoxLayout()
        select_link_btn = QtWidgets.QPushButton("")
        select_link_btn.setFlat(True)
        select_link_btn.setFixedSize(TOOL_BAR_BUTTON_SIZE)
        select_link_btn.setIcon(hou.ui.createQtIcon(r"HoudiniNodeBookmarks\in"))
        select_link_btn.setIconSize(TOOL_BAR_BUTTON_ICON_SIZE)
        select_link_btn.setToolTip(("Select network view(s)"
                                    " to be affected by the bookmarks"))
        select_link_btn.clicked.connect(self.select_link)
        network_link_layout.addWidget(select_link_btn)

        self.link_labels = QtWidgets.QLabel("All network views linked")
        network_link_layout.addWidget(self.link_labels)

        # network view affected by bookmark
        self.linked_network_views = []

        main_layout.addLayout(network_link_layout)
        
        cw.setLayout(main_layout)
        self.setCentralWidget(cw)

        self.init_network_linked()
        self.update_recents()

        # check if any data are saved in the hip file and load them
        self.check_hip_file_data()

    def update_filter_mode(self):
        
        if self.filter_mode == "bookmark":
            self.filter_btn.setIcon(hou.ui.createQtIcon("SOP_subnet"))
            self.filter_btn.setToolTip("Filter by node's name.")
            self.filter_mode = "node"
        else:
            self.filter_btn.setIcon(hou.ui.createQtIcon(r"HoudiniNodeBookmarks\book"))
            self.filter_btn.setToolTip("Filter by bookmark's name.")
            self.filter_mode = "bookmark"

        self.update_filter()

    def update_filter(self):

        self.bookmark_view.update_filter(self.filter_input.text(),
                                         self.filter_mode)

    def select_link(self):

        w = NetworkViewChooser(self.linked_network_views,
                              self)
        w.show()

    def get_bookmarks(self):

        return [c for c in self.bookmark_view.children() if \
                isinstance(c, Bookmark)]

    def get_bookmark_file_data(self):

        if self.bookmark_view.bookmarks == {}:
            hou.ui.displayMessage("Bookmark list is empty.")
            return None

        bookmark_data = {}
        bookmark_data["version"] = HoudiniNodeBookmarks.__VERSION__

        bookmark_data["linked_networks"] = [ntw.name() for ntw in \
                                            self.linked_network_views]

        bookmark_data["bookmark_data"] = self.bookmark_view.get_data()

        bookmark_data["options"] = {"show_icons":self.show_icon_btn.isChecked(),
                                    "show_labels":self.show_label_btn.isChecked(),
                                    "show_types":self.show_type_btn.isChecked()}

        return bookmark_data

    def update_icon(self):

        state = self.show_icon_btn.isChecked()
        for w in self.get_bookmarks():
            
            if state:
                w.icon_lbl.show()
            else:
                w.icon_lbl.hide()

        self.update_display_options("show_icon")

    def update_label(self):

        state = self.show_label_btn.isChecked()
        for w in self.get_bookmarks():
            
            if state:
                w.label.show()
            else:
                w.label.hide()

        self.update_display_options("show_label")

    def update_type(self):

        state = self.show_type_btn.isChecked()
        for w in self.get_bookmarks():
            
            if state:
                w.type_name_label.show()
            else:
                w.type_name_label.hide()

        self.update_display_options("show_type")

    def update_network_linked(self, choices):

        self.linked_network_views = choices
        inf = "{} network view(s) linked".format(len(choices))
        self.link_labels.setText(inf)
        self.link_labels.setToolTip(", ".join([e.name() for e in choices]))

    def init_network_linked(self, default=[]):

        editors = [pane for pane in hou.ui.paneTabs() if \
                   isinstance(pane, hou.NetworkEditor) and \
                   pane.isCurrentTab()]

        if editors:
            editors = [editors[0]]

        self.linked_network_views = editors

        inf = "{} network view(s) linked".format(len(editors))
        self.link_labels.setText(inf)
        self.link_labels.setToolTip(", ".join([e.name() for e in editors]))

    def clear_bookmarks(self):

        if self.bookmark_view.bookmarks == {}:
            return

        r = hou.ui.displayMessage("Clear all bookmarks ?",
                                  buttons=["Ok", "Cancel"],
                                  severity=hou.severityType.Warning)
        if r == 1: return

        for i in range(self.bookmark_view.bookmark_view_layout.count())[::-1]:
            it = self.bookmark_view.bookmark_view_layout.itemAt(i)
            if it:
                w = it.widget()
                if w:
                    w.setParent(None)
                    w.deleteLater()

        self.bookmark_view.bookmarks = {}
        
        self.bookmark_view.bookmark_view_layout.update()
        self.bookmark_view.update()

    def open_bookmarks(self, bkm_file=""):

        if bkm_file == "":
            bkm_file = QtWidgets.QFileDialog.getOpenFileName(self, "Select a file",
                                                        filter = "Bookmark (*.bkm)")[0]
        else:
            if not os.path.exists(bkm_file):
                hou.ui.displayMessage("Invalid file: " + str(bkm_file),
                                      severity=hou.severityType.Error)
                return

        if bkm_file.strip() == '': return

        with open(bkm_file) as f:    
            data = json.load(f)
        
        self.set_bookmark_from_data(data)

        self.add_to_recents(bkm_file)

    def save_bookmarks(self):
        
        bkm = QtWidgets.QFileDialog.getSaveFileName(self, "Select a file",
                                                    filter = "Bookmark (*.bkm)")[0]
        if bkm.strip() == '': return

        if not bkm.endswith(".bkm"):
            bkm = bkm + ".bkm"

        bookmark_data = self.get_bookmark_file_data()
        if not data: return

        with open(bkm, 'w') as f:
            json.dump(bookmark_data, f,
                      ensure_ascii=False,
                      indent=4)

    def save_to_hip(self):

        bookmark_data = self.get_bookmark_file_data()
        if not bookmark_data: return

        r = hou.ui.displayMessage("Save current bookmarks to hip file ?",
                                  buttons=["Yes", "Cancel"])
        if r == 1: return

        self.delete_hip_file_data(verbose=False)

        code = ("# HOUDINI NODE BOOKMARKS START\n"
                "def get_node_bookmarks_data():\n"
                "    data = " + str(bookmark_data)+ "\n"
                "    return data\n"
                "# HOUDINI NODE BOOKMARKS END\n"
                )

        cur_data = hou.sessionModuleSource()
        hou.setSessionModuleSource(cur_data + '\n' + code)

    def check_hip_file_data(self, verbose=False):

        if "# HOUDINI NODE BOOKMARKS START\n" in hou.sessionModuleSource():
            data = hou.session.get_bookmark_file_data()
            self.load_from_hip_data(data)
        else:
            if verbose:
                hou.ui.displayMessage("No bookmarks data found in current hip file")

    def load_from_hip_data(self, data):

        try:
            print("Loading node bookmarks from hip file...")
            self.set_bookmark_from_data(data)
        except Exception as e:
            hou.ui.displayMessage("Invalid data: " + str(e),
                                  severity=hou.severityType.Error)
            return

    def delete_hip_file_data(self, verbose=True):

        data = hou.sessionModuleSource()
        if data.strip() == "" or not "# HOUDINI NODE BOOKMARKS START" in data:
            if verbose:
                hou.ui.displayMessage("No bookmarks data found in current hip file")
            return

        if verbose:
            r = hou.ui.displayMessage("Delete current bookmarks hip file data ?",
                                      buttons=["Yes", "Cancel"])
            if r == 1: return


        is_bkm_code = False
        data = data.split('\n')
        new_data = []
        for d in data:

            if d.startswith("# HOUDINI NODE BOOKMARKS START"):
                is_bkm_code = True
                continue

            if d.startswith("# HOUDINI NODE BOOKMARKS END"):
                is_bkm_code = False
                continue

            if not is_bkm_code:
                new_data.append(d)

        hou.setSessionModuleSource('\n'.join(new_data))


    def set_bookmark_from_data(self, data):

        bookmarks = data.get("bookmark_data")
        if not bookmarks:
            hou.ui.displayMessage(("Invalid file, 'bookmark_data' is empty"
                                   " or non-existent"))
            return

        for bkm in bookmarks:
            
            bkm_type = bkm.get("type")

            if not bkm_type:
                print("Invalid bkm, no type found")
                continue

            if bkm_type == "bookmark":

                name=bkm.get("name", "INVALID")
                node_path=bkm.get("node_path", "/obj")
                node = hou.node(node_path)
                if node is None:
                    print("Node '{}' not found in scene,"
                          " bookmark '{}' skipped".format(node_path,
                                                          name))
                    continue

                b = Bookmark(name=name,
                             node_path=node_path,
                             node=node,
                             color=bkm.get("color", [0,0,0]),
                             text_color=bkm.get("text_color", [0,0,0]),
                             id=bkm.get("id", -1),
                             uid=bkm.get("uid", "INVALID"),
                             parent=self.bookmark_view)

                self.bookmark_view.bookmark_view_layout.addWidget(b)
                self.bookmark_view.bookmarks[bkm.get("uid", "INVALID")] = b

            elif bkm_type == "separator":

                s = Separator(bkm.get("name", "INVALID"),
                              bkm.get("id", -1),
                              parent=self.bookmark_view)

                self.bookmark_view.bookmark_view_layout.addWidget(s)

        self.bookmark_view.bookmark_view_layout.update()
        self.bookmark_view.update()

    def get_recents(self):

        if not os.path.exists(RECENTS_FILE):
            with open(RECENTS_FILE, 'w') as f:
                f.write("")
            return []

        with open(RECENTS_FILE, 'r') as f:
            return [d for d in f.read().split('\n')\
                    if d.strip() != ""]

    def add_to_recents(self, bkm):

        cur_recents = self.get_recents()
        if bkm in cur_recents: return

        if len(cur_recents) == 10:
            cur_recents.pop(0)

        cur_recents.append(bkm)
        with open(RECENTS_FILE, 'w') as f:
            for cur in cur_recents:
                f.write(cur + '\n')

        self.recent_files = cur_recents

        self.update_recents()

    def update_recents(self):

        self.recents_menu.clear()

        recents = self.get_recents()
        if recents == []:
            none_act = QtWidgets.QAction("None", self)
            none_act.setDisabled(True)
            self.recents_menu.addAction(none_act)

        else:
            for r in recents:
                a = QtWidgets.QAction(r, self)
                a.triggered.connect(lambda r=r: self.open_bookmarks(r))
                self.recents_menu.addAction(a)

            self.recents_menu.addSeparator()
            del_rec_act = QtWidgets.QAction("Delete recents", self)
            del_rec_act.triggered.connect(self.delete_recent)
            self.recents_menu.addAction(del_rec_act)

            self.recent_files = recents

    def delete_recent(self):

        if os.path.exists(RECENTS_FILE):
            os.remove(RECENTS_FILE)

        self.update_recents()

    def update_opts(self, opt):

        val = "false"
        if opt == "ask_for_name":
            val = str(self.ask_name_act.isChecked()).lower()

        elif opt == "display_options":

            val = self.display_options_act.isChecked()

            self.show_icon_btn.setVisible(val)
            self.show_type_btn.setVisible(val)
            self.show_label_btn.setVisible(val)
            self.toolbar_sep.setVisible(val)
            self.add_separator_btn.setVisible(val)

            val = str(val).lower()

        elif opt == "display_filter":

            val = self.display_filter_act.isChecked()

            self.filter_lbl.setVisible(val)
            self.filter_btn.setVisible(val)
            self.filter_input.setVisible(val)

            val = str(val).lower()
        
        ConfigFile.set_ui_prefs(opt, val)

    def update_display_options(self, opt):

        if opt == "show_icon":
            val = self.show_icon_btn.isChecked()
        elif opt == "show_label":
            val = self.show_label_btn.isChecked()
        else:
            val = self.show_type_btn.isChecked()
        
        ConfigFile.set_display_pref(opt, str(val).lower())

    def show_help(self):

        return

    def show_about(self):

        return

