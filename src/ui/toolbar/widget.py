# toolbar.py
#
# Copyright 2025 Naufan Rusyda Faikar <hello@naruaika.me>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# 	http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

from gi.repository import Gio
from gi.repository import GLib
from gi.repository import Gtk

from ... import environment as env

from ...editors.node.editor  import NodeEditor
from ...editors.chart.editor import ChartEditor
from ...editors.sheet.editor import SheetEditor

@Gtk.Template(resource_path = '/com/wittara/studio/ui/toolbar/template.ui')
class Toolbar(Gtk.Box):

    __gtype_name__ = 'Toolbar'

    ViewSwitcher             = Gtk.Template.Child()
    ViewStack                = Gtk.Template.Child()

    HomePage                 = Gtk.Template.Child()

#   ClipboardSection         = Gtk.Template.Child()
#   PasteButton              = Gtk.Template.Child()
#   CutButton                = Gtk.Template.Child()
#   CopyButton               = Gtk.Template.Child()

    InputOutputSection       = Gtk.Template.Child()
    OpenSourceButton         = Gtk.Template.Child()
    ReadSourceButton         = Gtk.Template.Child()
    RecentFilesButton        = Gtk.Template.Child()
    ExportAsButton           = Gtk.Template.Child()
    FileUtilitiesButton      = Gtk.Template.Child()

    ManageColumnsSection     = Gtk.Template.Child()
    ChooseColumnsButton      = Gtk.Template.Child()
    RemoveColumnsButton      = Gtk.Template.Child()

    ReduceRowsSection        = Gtk.Template.Child()
    KeepRowsButton           = Gtk.Template.Child()
    RemoveRowsButton         = Gtk.Template.Child()

    SortAndFilterSection     = Gtk.Template.Child()
    SortRowsButton           = Gtk.Template.Child()
    FilterRowsButton         = Gtk.Template.Child()

    TransformSection         = Gtk.Template.Child()
    JoinTablesQButton        = Gtk.Template.Child()
    GroupByQButton           = Gtk.Template.Child()
    SplitColumnQButton       = Gtk.Template.Child()
    ChangeDataTypeQButton    = Gtk.Template.Child()
    ReplaceValuesQButton     = Gtk.Template.Child()
    CustomFormulaButton      = Gtk.Template.Child()

    WorkflowSection          = Gtk.Template.Child()
    NewWorkspaceButton       = Gtk.Template.Child()
    NewViewerButton          = Gtk.Template.Child()
    NewConstantsButton       = Gtk.Template.Child()

    TransformPage            = Gtk.Template.Child()

    TableSection             = Gtk.Template.Child()
    GroupByButton            = Gtk.Template.Child()
    TransposeTableButton     = Gtk.Template.Child()
    ReverseRowsButton        = Gtk.Template.Child()

    AnyColumnSection         = Gtk.Template.Child()
    ChangeDataTypeButton     = Gtk.Template.Child()
    RenameColumnsButton      = Gtk.Template.Child()
    ReplaceValuesButton      = Gtk.Template.Child()
    FillBlankCellsButton     = Gtk.Template.Child()
#   PivotColumnsButton       = Gtk.Template.Child()

    TextColumnSection        = Gtk.Template.Child()
    SplitColumnButton        = Gtk.Template.Child()
    FormatColumnButton       = Gtk.Template.Child()
    MergeColumnsButton       = Gtk.Template.Child()
    ExtractColumnButton      = Gtk.Template.Child()

    NumberColumnSection      = Gtk.Template.Child()
    ColumnStatisticsButton   = Gtk.Template.Child()
    ColumnStandardButton     = Gtk.Template.Child()
    ColumnScientificButton   = Gtk.Template.Child()
    ColumnTrigonometryButton = Gtk.Template.Child()
    RoundValueButton         = Gtk.Template.Child()
    ColumnInformationButton  = Gtk.Template.Child()

    DateTimeColumnSection    = Gtk.Template.Child()
    DateColumnButton         = Gtk.Template.Child()
    TimeColumnButton         = Gtk.Template.Child()
    DurationColumnButton     = Gtk.Template.Child()

#   AnalyticsPage            = Gtk.Template.Child()

    ViewPage                 = Gtk.Template.Child()

    ShowSection              = Gtk.Template.Child()
    ShowGridlinesButton      = Gtk.Template.Child()
    ShowLocatorsButton       = Gtk.Template.Child()
    ShowMinimapButton        = Gtk.Template.Child()
    ShowFormulaBarButton     = Gtk.Template.Child()
    ShowFocusCellButton      = Gtk.Template.Child()

    HelpPage                 = Gtk.Template.Child()

    HelpSection              = Gtk.Template.Child()
    GuidedLearningButton     = Gtk.Template.Child()
    DocumentationButton      = Gtk.Template.Child()
    TrainingVideosButton     = Gtk.Template.Child()
    CustomerSupportButton    = Gtk.Template.Child()

    CommunitySection         = Gtk.Template.Child()
    CommunityForumButton     = Gtk.Template.Child()
    CommunityGalleriesButton = Gtk.Template.Child()
    OfficialSamplesButton    = Gtk.Template.Child()
    SubmitIdeaButton         = Gtk.Template.Child()

    def __init__(self) -> None:
        """"""
        self._mapping = [
            (
                self.HomePage,
                (
                    NodeEditor,
                    ChartEditor,
                    SheetEditor,
                ),
                [
#                   (
#                       self.ClipboardSection,
#                       (
#                           NodeEditor,
#                           ChartEditor,
#                           SheetEditor,
#                       ),
#                       [
#                           (
#                               self.PasteButton,
#                               (
#                                   NodeEditor,
#                                   ChartEditor,
#                                   SheetEditor,
#                               ),
#                           ),
#                           (
#                               self.CutButton,
#                               (
#                                   NodeEditor,
#                                   ChartEditor,
#                                   SheetEditor,
#                               ),
#                           ),
#                           (
#                               self.CopyButton,
#                               (
#                                   NodeEditor,
#                                   ChartEditor,
#                                   SheetEditor,
#                               ),
#                           ),
#                       ],
#                   ),

                    (
                        self.InputOutputSection,
                        (
                            NodeEditor,
                            ChartEditor,
                            SheetEditor,
                        ),
                        [
                            (
                                self.OpenSourceButton,
                                (
                                    ChartEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.ReadSourceButton,
                                (
                                    NodeEditor,
                                ),
                            ),
                            (
                                self.RecentFilesButton,
                                (
                                    NodeEditor,
                                    ChartEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.ExportAsButton,
                                (
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.FileUtilitiesButton,
                                (
                                    NodeEditor,
                                ),
                            ),
                        ],
                    ),

                    (
                        self.ManageColumnsSection,
                        (
                            NodeEditor,
                            SheetEditor,
                        ),
                        [
                            (
                                self.ChooseColumnsButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.RemoveColumnsButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                        ],
                    ),

                    (
                        self.ReduceRowsSection,
                        (
                            NodeEditor,
                            SheetEditor,
                        ),
                        [
                            (
                                self.KeepRowsButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.RemoveRowsButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                        ],
                    ),

                    (
                        self.SortAndFilterSection,
                        (
                            NodeEditor,
                            SheetEditor,
                        ),
                        [
                            (
                                self.SortRowsButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.FilterRowsButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                        ],
                    ),

                    (
                        self.TransformSection,
                        (
                            NodeEditor,
                            SheetEditor,
                        ),
                        [
                            (
                                self.JoinTablesQButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.GroupByQButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.SplitColumnQButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.ChangeDataTypeQButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.ReplaceValuesQButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.CustomFormulaButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                        ],
                    ),

                    (
                        self.WorkflowSection,
                        (
                            NodeEditor,
                            SheetEditor,
                        ),
                        [
                            (
                                self.NewWorkspaceButton,
                                (
                                    NodeEditor,
                                    ChartEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.NewViewerButton,
                                (
                                    NodeEditor,
                                ),
                            ),
                            (
                                self.NewConstantsButton,
                                (
                                    NodeEditor,
                                ),
                            ),
                        ],
                    ),
                ],
            ),

            (
                self.TransformPage,
                (
                    NodeEditor,
                    SheetEditor,
                ),
                [
                    (
                        self.TableSection,
                        (
                            NodeEditor,
                            SheetEditor,
                        ),
                        [
                            (
                                self.GroupByButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.TransposeTableButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.ReverseRowsButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                        ],
                    ),
                    (
                        self.AnyColumnSection,
                        (
                            NodeEditor,
                            SheetEditor,
                        ),
                        [
                            (
                                self.ChangeDataTypeButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.RenameColumnsButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.ReplaceValuesButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.FillBlankCellsButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
#                           (
#                               self.PivotColumnsButton,
#                               (
#                                   NodeEditor,
#                                   SheetEditor,
#                               ),
#                           ),
                        ],
                    ),
                    (
                        self.TextColumnSection,
                        (
                            NodeEditor,
                            SheetEditor,
                        ),
                        [
                            (
                                self.SplitColumnButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.FormatColumnButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.MergeColumnsButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.ExtractColumnButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                        ],
                    ),
                    (
                        self.NumberColumnSection,
                        (
                            NodeEditor,
                            SheetEditor,
                        ),
                        [
                            (
                                self.ColumnStatisticsButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.ColumnStandardButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.ColumnScientificButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.ColumnTrigonometryButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.RoundValueButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.ColumnInformationButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                        ],
                    ),
                    (
                        self.DateTimeColumnSection,
                        (
                            NodeEditor,
                            SheetEditor,
                        ),
                        [
                            (
                                self.DateColumnButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.TimeColumnButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.DurationColumnButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                        ],
                    ),
                ],
            ),

#           (
#               self.AnalyticsPage,
#               (
#                   NodeEditor,
#                   SheetEditor,
#               ),
#               [],
#           ),

            (
                self.ViewPage,
                (
                    NodeEditor,
                    ChartEditor,
                    SheetEditor,
                ),
                [
                    (
                        self.ShowSection,
                        (
                            NodeEditor,
                            ChartEditor,
                            SheetEditor,
                        ),
                        [
                            (
                                self.ShowGridlinesButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.ShowLocatorsButton,
                                (
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.ShowMinimapButton,
                                (
                                    NodeEditor,
                                ),
                            ),
                            (
                                self.ShowFormulaBarButton,
                                (
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.ShowFocusCellButton,
                                (
                                    SheetEditor,
                                ),
                            ),
                        ],
                    ),
                ],
            ),

            (
                self.HelpPage,
                (
                    NodeEditor,
                    ChartEditor,
                    SheetEditor,
                ),
                [
                    (
                        self.HelpSection,
                        (
                            NodeEditor,
                            ChartEditor,
                            SheetEditor,
                        ),
                        [
                            (
                                self.GuidedLearningButton,
                                (
                                    NodeEditor,
                                    ChartEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.DocumentationButton,
                                (
                                    NodeEditor,
                                    ChartEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.TrainingVideosButton,
                                (
                                    NodeEditor,
                                    ChartEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.CustomerSupportButton,
                                (
                                    NodeEditor,
                                    ChartEditor,
                                    SheetEditor,
                                ),
                            ),
                        ],
                    ),
                    (
                        self.CommunitySection,
                        (
                            NodeEditor,
                            ChartEditor,
                            SheetEditor,
                        ),
                        [
                            (
                                self.CommunityForumButton,
                                (
                                    NodeEditor,
                                    ChartEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.CommunityGalleriesButton,
                                (
                                    NodeEditor,
                                    ChartEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.OfficialSamplesButton,
                                (
                                    NodeEditor,
                                    ChartEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.SubmitIdeaButton,
                                (
                                    NodeEditor,
                                    ChartEditor,
                                    SheetEditor,
                                ),
                            ),
                        ],
                    ),
                ],
            ),
        ]

        self.settings = Gio.Settings.new(env.APP_ID)

        self.is_refreshing_ui = False

        self._setup_recent_files_menu()
        self._setup_date_column_menu()

    def _setup_recent_files_menu(self) -> None:
        """"""
        from .popover_recent_files import RecentFilesPopover
        popover = RecentFilesPopover()
        self.RecentFilesButton.set_popover(popover)

    def _setup_date_column_menu(self) -> None:
        """"""
        popover = self.DateColumnButton.get_last_child()
        scrolled = popover.get_child()
        viewport = scrolled.get_first_child()
        stack = viewport.get_first_child()

        section = stack.get_first_child()
        section.set_orientation(Gtk.Orientation.HORIZONTAL)
        section.set_homogeneous(True)
        section.set_spacing(6)

        box1 = section.get_first_child()

        box2 = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        section.append(box2)

        for _ in range(3):
            box = box1.get_last_child()
            box.unparent()
            box2.prepend(box)

            separator = Gtk.Separator(orientation = Gtk.Orientation.HORIZONTAL)
            box.prepend(separator)

    def populate(self) -> None:
        """"""
        self.is_refreshing_ui = True

        window = self.get_root()
        editor = window.get_selected_editor()

        command_list = window.get_command_list()
        if hasattr(editor, 'get_command_list'):
            command_list += editor.get_command_list()
        names = [c['name'] for c in command_list]

        for page, owners, sections in self._mapping:
            if not isinstance(editor, owners):
                page.set_visible(False)
                continue
            page.set_visible(True)

            for section, owners, widgets in sections:
                if not isinstance(editor, owners):
                    section.set_visible(False)
                    continue
                section.set_visible(True)

                for widget, owners in widgets:
                    if not isinstance(editor, owners):
                        widget.set_visible(False)
                        continue

                    is_active = widget.get_name() in names

                    if isinstance(widget, Gtk.Actionable):
                        if action_name := widget.get_action_name():
                            action_name = action_name.removesuffix(':disabled')

                            if is_active:
                                widget.set_action_name(action_name)
                            else:
                                widget.set_action_name(action_name + ':disabled')

                    else:
                        widget.set_sensitive(is_active)

                    widget.set_visible(True)

        for button in [
            self.SplitColumnButton,
            self.FormatColumnButton,
            self.ColumnStatisticsButton,
        ]:
            menu = button.get_menu_model()
            self._update_action_names(menu, names)

        self._update_check_buttons()

        self.is_refreshing_ui = False

    def _update_action_names(self,
                             menu:    Gio.MenuModel,
                             targets: list[str],
                             ) ->     None:
        """"""
        def do_update(menu:    Gio.MenuModel,
                      index:   int,
                      targets: list[str],
                      ) ->     None:
            """"""
            action = menu.get_item_attribute_value(index, 'action', None)

            if not action:
                return

            action = action.get_string()
            action = action.removesuffix(':disabled')

            if action != 'win.toolbar':
                return

            target = menu.get_item_attribute_value(index, 'target', None)
            target = target.get_string()

            if target not in targets:
                action = action + ':disabled'

            item = Gio.MenuItem.new_from_model(menu, index)
            item.set_attribute_value('action', GLib.Variant.new_string(action))

            menu.remove(index)
            menu.insert_item(index, item)

        for i in range(menu.get_n_items()):
            do_update(menu, i, targets)

            for link in {Gio.MENU_LINK_SECTION,
                         Gio.MENU_LINK_SUBMENU}:
                if link := menu.get_item_link(i, link):
                    self._update_action_names(link, targets)

    def _update_check_buttons(self) -> None:
        """"""
        window = self.get_root()
        editor = window.get_selected_editor()

        if isinstance(editor, NodeEditor):
            active = self.settings.get_boolean('node-gridlines')
            self.ShowGridlinesButton.set_active(active)

            active = self.settings.get_boolean('node-minimap')
            self.ShowMinimapButton.set_active(active)

        if isinstance(editor, SheetEditor):
            active = self.settings.get_boolean('sheet-gridlines')
            self.ShowGridlinesButton.set_active(active)

            active = self.settings.get_boolean('sheet-locators')
            self.ShowLocatorsButton.set_active(active)

            active = self.settings.get_boolean('sheet-formula-bar')
            self.ShowFormulaBarButton.set_active(active)

            active = self.settings.get_boolean('sheet-focus-cell')
            self.ShowFocusCellButton.set_active(active)

    @Gtk.Template.Callback()
    def _on_gridlines_toggled(self,
                              button: Gtk.CheckButton,
                              ) ->    None:
        """"""
        if self.is_refreshing_ui:
            return

        active = button.get_active()
        window = self.get_root()
        editor = window.get_selected_editor()

        if isinstance(editor, NodeEditor):
            self.settings.set_boolean('node-gridlines', active)
        if isinstance(editor, SheetEditor):
            self.settings.set_boolean('sheet-gridlines', active)

        self._refresh_selected_editor()

    @Gtk.Template.Callback()
    def _on_minimap_toggled(self,
                            button: Gtk.CheckButton,
                            ) ->    None:
        """"""
        if self.is_refreshing_ui:
            return

        self.settings.set_boolean('node-minimap', button.get_active())

        self._refresh_selected_editor()

    @Gtk.Template.Callback()
    def _on_locators_toggled(self,
                             button: Gtk.CheckButton,
                             ) ->    None:
        """"""
        if self.is_refreshing_ui:
            return

        self.settings.set_boolean('sheet-locators', button.get_active())

        self._refresh_selected_editor()

        window = self.get_root()
        editor = window.get_selected_editor()
        editor.view.update_by_scroll()
        editor.reposition_sheet_widgets()

    @Gtk.Template.Callback()
    def _on_formula_bar_toggled(self,
                                button: Gtk.CheckButton,
                                ) ->    None:
        """"""
        if self.is_refreshing_ui:
            return

        self.settings.set_boolean('sheet-formula-bar', button.get_active())

        self._refresh_selected_editor()

    @Gtk.Template.Callback()
    def _on_focus_cell_toggled(self,
                               button: Gtk.CheckButton,
                               ) ->    None:
        """"""
        if self.is_refreshing_ui:
            return

        self.settings.set_boolean('sheet-focus-cell', button.get_active())

        self._refresh_selected_editor()

    def _refresh_selected_editor(self) -> None:
        """"""
        window = self.get_root()
        editor = window.get_selected_editor()

        if isinstance(editor, SheetEditor):
            for e in window.get_all_editors():
                if isinstance(e, SheetEditor):
                    e.queue_draw(refresh = True)

        else:
            editor.queue_draw(refresh = True)
