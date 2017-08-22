import hashlib
import hou
import os
import json
from PySide2 import QtWidgets
from PySide2 import QtGui
from PySide2 import QtCore
Qt = QtCore.Qt

__VERSION__ = "1.0.0"

ver = hou.applicationVersion()

TOOL_BAR_BUTTON_SIZE = QtCore.QSize(25, 25)
TOOL_BAR_BUTTON_ICON_SIZE = QtCore.QSize(22, 22)
_img = [hou.expandString("$HOME"), "houdini{}.{}".format(ver[0], ver[1]),
       "config", "Icons", "houdiniNodeBookmarks_checkmark.svg" ]
IDENT_NETWORK_IMG = os.path.join(*_img)

def init_bookmark_view():

    """if hasattr(hou.session, "NODES_BOOKMARK"):
        return hou.session.NODES_BOOKMARK"""

    w = NodesBookmark()
    hou.session.NODES_BOOKMARK = w
    return w

def create_boormark(node):

    if hasattr(hou.session, "NODES_BOOKMARK"):
        w = hou.session.NODES_BOOKMARK

    else:
        hou.ui.displayMessage("Init Houdini Nodes Bookmark first.")

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

        self.collapsed = False
        self.collapsed_children = []
        self.collapse_btn = QtWidgets.QPushButton("")
        self.collapse_btn.setFlat(True)
        self.collapse_btn.setIcon(hou.ui.createQtIcon("houdiniNodeBookmarks_down"))
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

        edit_ico = hou.ui.createQtIcon("houdiniNodeBookmarks_edit")
        self.edit_label_act = QtWidgets.QAction(edit_ico,
                                                "Edit Label", self)
        self.edit_label_act.triggered.connect(self.edit_label)
        self.menu.addAction(self.edit_label_act)

        rem_ico = hou.ui.createQtIcon("houdiniNodeBookmarks_remove")
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
            self.collapse_btn.setIcon(hou.ui.createQtIcon("houdiniNodeBookmarks_down"))
            self.collapsed_label.setText("")

            for w in self.find_widgets_to_collapse():
                w.collapsed = False
                w.show()

        else:
            self.collapsed = True
            self.collapse_btn.setIcon(hou.ui.createQtIcon("houdiniNodeBookmarks_right"))
            
            widgets = self.find_widgets_to_collapse()
            for w in widgets:
                w.collapsed = True
                w.hide()

            self.collapsed_label.setText("(" + str(len(widgets)) + ")")

    def data(self):

        return {"type":"breaker",
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
            return

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
            self.bookmarkview.bookmark_view_layout.update()
            return

class AddSeparator(QtWidgets.QLabel):

    def __init__(self, parent=None):
        super(AddSeparator, self).__init__(parent=parent)
        ico = hou.ui.createQtIcon("houdiniNodeBookmarks_break")
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
        self.setFixedHeight(40)
        self.setAutoFillBackground(True)
        self.setObjectName("bookmark")
        self.setAcceptDrops(True)

        self.collapsed = False

        if not kwargs.get("color"):
            self.color = [60, 70, 140]
        else:
            self.color = kwargs["color"]
        if not kwargs.get("text_color"):
            self.text_color = [203, 203, 203]
        else:
            self.text_color = kwargs["text_color"]
        self.id = kwargs["id"]
        self.uid = kwargs["uid"]
        self.bookmarkview = kwargs["parent"]

        self.node = kwargs["node"]
        self.node_path = self.node.path()
        self.node_name = self.node.name()
        self.node_type = self.node.type()
        self.bookmark_name = kwargs["name"]
        
        self.setToolTip(self.node_path)

        bookmark_layout = QtWidgets.QHBoxLayout()
        bookmark_layout.setSpacing(5)
        bookmark_layout.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)

        try:
            icon = hou.ui.createQtIcon(self.node_type.icon())
        except hou.OperationFailed:
            icon = hou.ui.createQtIcon("SOP_subnet")
        self.icon_lbl = QtWidgets.QLabel("")
        self.icon_lbl.setStyleSheet("QLabel{border: 0px}")
        self.icon_lbl.setPixmap(icon.pixmap(28, 28))
        self.icon_lbl.setFixedHeight(28)
        self.icon_lbl.setFixedWidth(28)
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

        edit_ico = hou.ui.createQtIcon("houdiniNodeBookmarks_edit")
        self.edit_label_act = QtWidgets.QAction(edit_ico,
                                                "Edit Label", self)
        self.edit_label_act.triggered.connect(self.edit_name)
        self.menu.addAction(self.edit_label_act)

        color_ico = hou.ui.createQtIcon("houdiniNodeBookmarks_color")
        self.edit_color_act = QtWidgets.QAction(color_ico,
                                                "Edit Background Color", self)
        self.edit_color_act.triggered.connect(self.pick_color)
        self.menu.addAction(self.edit_color_act)

        color_txt_ico = hou.ui.createQtIcon("houdiniNodeBookmarks_text_color")
        self.edit_txt_color_act = QtWidgets.QAction(color_txt_ico,
                                                "Edit Label Color", self)
        self.edit_txt_color_act.triggered.connect(self.pick_txt_color)
        self.menu.addAction(self.edit_txt_color_act)

        self.menu.addSeparator()

        rem_ico = hou.ui.createQtIcon("houdiniNodeBookmarks_remove")
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
                              QFrame:hover{{border: 2px solid {3}}}
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

        e.accept()
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
            
            # if it is a separator, check if any collapsed widgets
            # need to be moved
            if isinstance(w, Separator):

                colw = w.collapsed_children
                w.collapsed_children = []
                w.collapsed = False

                for i, _w in enumerate(colw):
                    copyw = _w.copy(self.bookmarkview)
                    _w.remove_me(False)
                    self.bookmarkview.bookmark_view_layout.insertWidget(self.id + i + 1,
                                                                        copyw)
            
            self.bookmarkview.refresh_bookmark_ids()

        else:
            self.bookmarkview.insert_bookmark(node_path, self.id)

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
        
              
    def insert_bookmark(self, node_path, idx=0):

        h_node_path = hashlib.sha1(node_path)
        h_node_path = h_node_path.hexdigest()

        if h_node_path in self.bookmarks.keys():
            return

        node = hou.node(node_path)
        if node is None:
            return
        
        bookmark_name = node.name()
        bookmark = Bookmark(node=node,
                            uid=h_node_path,
                            name=bookmark_name,
                            parent=self,
                            id=idx)

        self.bookmarks[h_node_path] = bookmark
        self.bookmark_view_layout.insertWidget(idx, bookmark)
        
        self.refresh_bookmark_ids()

    def insert_breaker(self, idx=0):
        
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

    def get_data(self):
        
        data = []
        
        c = self.bookmark_view_layout.count()
        for i in range(c):
            it = self.bookmark_view_layout.itemAt(i)
            if it:
                data.append(it.widget().data())
        
        return data
        
class NodesBookmark(QtWidgets.QWidget):

    def __init__(self):
        super(NodesBookmark, self).__init__()

        self.setProperty("houdiniStyle", True)
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)

        # menu
        main_menu = QtWidgets.QMenu(self)


        # toolbar
        toolbar_layout = QtWidgets.QHBoxLayout()
        toolbar_layout.setAlignment(Qt.AlignLeft)

        # load button
        load_btn = QtWidgets.QPushButton("")
        load_btn.setFixedSize(TOOL_BAR_BUTTON_SIZE)
        load_btn.setIcon(hou.ui.createQtIcon("houdiniNodeBookmarks_open"))
        load_btn.setIconSize(TOOL_BAR_BUTTON_ICON_SIZE)
        load_btn.setToolTip("Load bookmark from file")
        toolbar_layout.addWidget(load_btn)

        # save button
        save_btn = QtWidgets.QPushButton("")
        save_btn.setFixedSize(TOOL_BAR_BUTTON_SIZE)
        save_btn.setIcon(hou.ui.createQtIcon("houdiniNodeBookmarks_save"))
        save_btn.setIconSize(TOOL_BAR_BUTTON_ICON_SIZE)
        save_btn.setToolTip("Save bookmark to file")
        save_btn.clicked.connect(self.save_bookmark)
        toolbar_layout.addWidget(save_btn)

        # add a separator
        toolbar_layout.addWidget(VSep(self))
        
        # show icon
        self.show_icon_btn = QtWidgets.QPushButton("")
        self.show_icon_btn.setFixedSize(TOOL_BAR_BUTTON_SIZE)
        self.show_icon_btn.setIcon(hou.ui.createQtIcon("houdiniNodeBookmarks_ico"))
        self.show_icon_btn.setIconSize(TOOL_BAR_BUTTON_ICON_SIZE)
        self.show_icon_btn.setCheckable(True)
        self.show_icon_btn.setChecked(True)
        self.show_icon_btn.setToolTip("Show bookmark's icon")
        self.show_icon_btn.clicked.connect(self.update_icon)
        toolbar_layout.addWidget(self.show_icon_btn)

        # show labels
        self.show_label_btn = QtWidgets.QPushButton("")
        self.show_label_btn.setFixedSize(TOOL_BAR_BUTTON_SIZE)
        self.show_label_btn.setIcon(hou.ui.createQtIcon("houdiniNodeBookmarks_label"))
        self.show_label_btn.setIconSize(TOOL_BAR_BUTTON_ICON_SIZE)
        self.show_label_btn.setCheckable(True)
        self.show_label_btn.setChecked(True)
        self.show_label_btn.setToolTip("Show bookmark's label")
        self.show_label_btn.clicked.connect(self.update_label)
        toolbar_layout.addWidget(self.show_label_btn)

        # show types
        self.show_type_btn = QtWidgets.QPushButton("")
        self.show_type_btn.setFixedSize(TOOL_BAR_BUTTON_SIZE)
        self.show_type_btn.setIcon(hou.ui.createQtIcon("houdiniNodeBookmarks_type"))
        self.show_type_btn.setIconSize(TOOL_BAR_BUTTON_ICON_SIZE)
        self.show_type_btn.setCheckable(True)
        self.show_type_btn.setChecked(True)
        self.show_type_btn.setToolTip("Show bookmark node's type")
        self.show_type_btn.clicked.connect(self.update_type)
        toolbar_layout.addWidget(self.show_type_btn)

        # add a separator
        toolbar_layout.addWidget(VSep(self))

        # add breaker ( by drag and drop )
        self.add_breaker_btn = AddSeparator(self)
        toolbar_layout.addWidget(self.add_breaker_btn)

        # add a separator
        toolbar_layout.addWidget(VSep(self))

        # help button
        help_btn = QtWidgets.QPushButton("")
        help_btn.setFixedSize(TOOL_BAR_BUTTON_SIZE)
        help_btn.setIcon(hou.ui.createQtIcon("houdiniNodeBookmarks_help"))
        help_btn.setIconSize(TOOL_BAR_BUTTON_ICON_SIZE)
        help_btn.setToolTip("Show help")
        toolbar_layout.addWidget(help_btn)

        main_layout.addLayout(toolbar_layout)

        # search line
        self.search_line = QtWidgets.QLineEdit()
        self.search_line.textChanged.connect(self.update_search)
        main_layout.addWidget(self.search_line)

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
        select_link_btn.setIcon(hou.ui.createQtIcon("houdiniNodeBookmarks_in"))
        select_link_btn.setIconSize(TOOL_BAR_BUTTON_ICON_SIZE)
        select_link_btn.setToolTip(("Select network view(s)"
                                    " to be affected by the bookmarks"))
        select_link_btn.clicked.connect(self.select_link)
        network_link_layout.addWidget(select_link_btn)

        self.link_labels = QtWidgets.QLabel("All network views linked")
        network_link_layout.addWidget(self.link_labels)

        # network view affected by bookmark
        self.linked_network_views = []
        self.init_network_linked()

        main_layout.addLayout(network_link_layout)
        
        self.setLayout(main_layout)

    def select_link(self):

        w = NetworkViewChooser(self.linked_network_views,
                              self)
        w.show()

    def get_bookmarks(self):

        return [c for c in self.bookmark_view.children() if \
                isinstance(c, Bookmark)]

    def update_search(self, txt):

        if txt.strip() == '':
            for w in self.get_bookmarks():
                w.show()
            return

        for w in self.get_bookmarks():
            if txt in w.label.text():
                w.show()
            else:
                w.hide()

    def update_icon(self):

        state = self.show_icon_btn.isChecked()
        for w in self.get_bookmarks():
            
            if state:
                w.icon_lbl.show()
            else:
                w.icon_lbl.hide()

    def update_label(self):

        state = self.show_label_btn.isChecked()
        for w in self.get_bookmarks():
            
            if state:
                w.label.show()
            else:
                w.label.hide()

    def update_type(self):

        state = self.show_type_btn.isChecked()
        for w in self.get_bookmarks():
            
            if state:
                w.type_name_label.show()
            else:
                w.type_name_label.hide()

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

    def save_bookmark(self):

        bookmark_data = {}
        bookmark_data["version"] = __VERSION__

        bookmark_data["linked_networks"] = [ntw.name() for ntw in \
                                            self.linked_network_views]

        bookmark_data["bookmark_data"] = self.bookmark_view.get_data()

        bookmark_data["options"] = {"show_icons":self.show_icon_btn.isChecked(),
                                    "show_labels":self.show_label_btn.isChecked(),
                                    "show_types":self.show_type_btn.isChecked()}
        
        bkm = QtWidgets.QFileDialog.getSaveFileName(self, "Select a file",
                                                    filter = "Bookmark (.*bkm)")[0]
        if bkm.strip() == '': return

        if not bkm.endswith(".bkm"):
            bkm = bkm + ".bkm"

        with open(bkm, 'w') as f:
            json.dump(bookmark_data, f,
                      ensure_ascii=False,
                      indent=4)

