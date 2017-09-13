import hou
from PySide2 import QtWidgets
from PySide2 import QtGui
from PySide2 import QtCore
Qt = QtCore.Qt

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

        self.auto_del_bkm_act = QtWidgets.QAction("Auto Delete Bookmarks", self)
        self.auto_del_bkm_act.setCheckable(True)
        self.auto_del_bkm_act.setChecked(ConfigFile.get_ui_prefs("auto_delete_bookmark"))
        self.auto_del_bkm_act.triggered.connect(lambda: self.update_opts("auto_delete_bookmark"))

        options_menu.addAction(self.auto_del_bkm_act)

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

        elif opt == "auto_delete_bookmark":
            val = str(self.auto_del_bkm_act.isChecked()).lower()

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

