# toolbar.py
#
# Copyright 2025 Naufan Rusyda Faikar
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from gi.repository import Gio
from gi.repository import GLib
from gi.repository import Gtk

from .node.editor import NodeEditor
from .chart.editor import ChartEditor
from .sheet.editor import SheetEditor

@Gtk.Template(resource_path = '/com/macipra/witt/toolbar.ui')
class Toolbar(Gtk.Box):

    __gtype_name__ = 'Toolbar'

    ViewSwitcher             = Gtk.Template.Child()
    ViewStack                = Gtk.Template.Child()

    HomePage                 = Gtk.Template.Child()

    InputOutputSection       = Gtk.Template.Child()
    ReadFileButton           = Gtk.Template.Child()
    OpenFileButton           = Gtk.Template.Child()
    QueryDatabaseButton      = Gtk.Template.Child()
    RecentSourcesButton      = Gtk.Template.Child()
    FileUtilitiesButton      = Gtk.Template.Child()

    ManageColumnsSection     = Gtk.Template.Child()
    ChooseColumnsButton      = Gtk.Template.Child()
    RemoveColumnsButton      = Gtk.Template.Child()

    ReduceRowsSection        = Gtk.Template.Child()
    KeepRowsButton           = Gtk.Template.Child()
    RemoveRowsButton         = Gtk.Template.Child()

    SortSection              = Gtk.Template.Child()
    SortRowsButton           = Gtk.Template.Child()

    TransformSection         = Gtk.Template.Child()
    SplitColumnQButton       = Gtk.Template.Child()
    GroupByQButton           = Gtk.Template.Child()
    ChangeDataTypeQButton    = Gtk.Template.Child()
    ReplaceValuesQButton     = Gtk.Template.Child()

    WorkflowSection          = Gtk.Template.Child()
    NewSheetButton           = Gtk.Template.Child()
    NewChartButton           = Gtk.Template.Child()
    NewStoryButton           = Gtk.Template.Child()
    NewViewerButton          = Gtk.Template.Child()
    NewConstantsButton       = Gtk.Template.Child()

    ClipboardSection         = Gtk.Template.Child()
    PasteButton              = Gtk.Template.Child()
    CutButton                = Gtk.Template.Child()
    CopyButton               = Gtk.Template.Child()

#   ExecutionSection         = Gtk.Template.Child()
#   AutoRunButton            = Gtk.Template.Child()
#   RunButton                = Gtk.Template.Child()
#   AutoUpdateButton         = Gtk.Template.Child()
#   UpdateButton             = Gtk.Template.Child()
#   UseCacheButton           = Gtk.Template.Child()
#   RecacheButton            = Gtk.Template.Child()
#   UseSampleButton          = Gtk.Template.Child()
#   ResampleButton           = Gtk.Template.Child()

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
    PivotColumnsButton       = Gtk.Template.Child()
    MoveColumnsButton        = Gtk.Template.Child()

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

    AnalyticsPage            = Gtk.Template.Child()

    ViewPage                 = Gtk.Template.Child()

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
                    (
                        self.InputOutputSection,
                        (
                            NodeEditor,
                            ChartEditor,
                            SheetEditor,
                        ),
                        [
                            (
                                self.ReadFileButton,
                                (
                                    NodeEditor,
                                ),
                            ),
                            (
                                self.OpenFileButton,
                                (
                                    ChartEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.QueryDatabaseButton,
                                (
                                    NodeEditor,
                                    ChartEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.RecentSourcesButton,
                                (
                                    NodeEditor,
                                    ChartEditor,
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
                        self.SortSection,
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
                                self.SplitColumnQButton,
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
                                self.NewSheetButton,
                                (
                                    NodeEditor,
                                    ChartEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.NewChartButton,
                                (
                                    NodeEditor,
                                    ChartEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.NewStoryButton,
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
                    (
                        self.ClipboardSection,
                        (
                            NodeEditor,
                            ChartEditor,
                            SheetEditor,
                        ),
                        [
                            (
                                self.PasteButton,
                                (
                                    NodeEditor,
                                    ChartEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.CutButton,
                                (
                                    NodeEditor,
                                    ChartEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.CopyButton,
                                (
                                    NodeEditor,
                                    ChartEditor,
                                    SheetEditor,
                                ),
                            ),
                        ],
                    ),

#                   (
#                       self.ExecutionSection,
#                       (
#                           NodeEditor,
#                           ChartEditor,
#                       ),
#                       [
#                           (
#                               self.AutoRunButton,
#                               (
#                                   NodeEditor,
#                               ),
#                           ),
#                           (
#                               self.RunButton,
#                               (
#                                   NodeEditor,
#                               ),
#                           ),
#                           (
#                               self.AutoUpdateButton,
#                               (
#                                   ChartEditor,
#                               ),
#                           ),
#                           (
#                               self.UpdateButton,
#                               (
#                                   ChartEditor,
#                               ),
#                           ),
#                           (
#                               self.UseCacheButton,
#                               (
#                                   NodeEditor,
#                               ),
#                           ),
#                           (
#                               self.RecacheButton,
#                               (
#                                   NodeEditor,
#                               ),
#                           ),
#                           (
#                               self.UseSampleButton,
#                               (
#                                   NodeEditor,
#                                   ChartEditor,
#                               ),
#                           ),
#                           (
#                               self.ResampleButton,
#                               (
#                                   NodeEditor,
#                                   ChartEditor,
#                               ),
#                           ),
#                       ],
#                   ),
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
                            (
                                self.PivotColumnsButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
                            (
                                self.MoveColumnsButton,
                                (
                                    NodeEditor,
                                    SheetEditor,
                                ),
                            ),
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

            (
                self.AnalyticsPage,
                (
                    NodeEditor,
                    SheetEditor,
                ),
                [],
            ),

            (
                self.ViewPage,
                (
                    NodeEditor,
                    ChartEditor,
                    SheetEditor,
                ),
                [],
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

    def populate(self) -> None:
        """"""
        window = self.get_root()
        editor = window.get_selected_editor()

        names = [cmd['name'] for cmd in editor.get_command_list()]

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
                    widget.set_sensitive(widget.get_name() in names)
                    widget.set_visible(True)

        menu = self.SplitColumnButton.get_menu_model()
        self._update_menu(menu, names)

        menu = self.FormatColumnButton.get_menu_model()
        self._update_menu(menu, names)

        menu = self.ColumnStatisticsButton.get_menu_model()
        self._update_menu(menu, names)

    def _update_menu(self,
                     menu:    Gio.MenuModel,
                     targets: list[str],
                     ) ->     None:
        """"""
        BASE_ACTION = 'win.toolbar'
        INSENSITIVE = f'{BASE_ACTION}.disabled'

        def do_update(menu:    Gio.MenuModel,
                      index:   int,
                      targets: list[str],
                      ) ->     None:
            """"""
            action = menu.get_item_attribute_value(index, 'action', None)

            if not action:
                return

            action = action.get_string()
            action = action.removesuffix('.disabled')

            if action != BASE_ACTION:
                return

            target = menu.get_item_attribute_value(index, 'target', None)
            target = target.get_string()

            if target not in targets:
                action = INSENSITIVE

            item = Gio.MenuItem.new_from_model(menu, index)
            item.set_attribute_value('action', GLib.Variant.new_string(action))

            menu.remove(index)
            menu.insert_item(index, item)

        for i in range(menu.get_n_items()):
            do_update(menu, i, targets)

            for link in {Gio.MENU_LINK_SECTION,
                         Gio.MENU_LINK_SUBMENU}:
                if link := menu.get_item_link(i, link):
                    self._update_menu(link, targets)

#   @Gtk.Template.Callback()
#   def _on_auto_run_toggled(self,
#                            button: Gtk.CheckButton,
#                            ) ->    None:
#       """"""
#       ...

#   @Gtk.Template.Callback()
#   def _on_auto_update_toggled(self,
#                               button: Gtk.CheckButton,
#                               ) ->    None:
#       """"""
#       ...

#   @Gtk.Template.Callback()
#   def _on_auto_cache_toggled(self,
#                              button: Gtk.CheckButton,
#                              ) ->    None:
#       """"""
#       ...

#   @Gtk.Template.Callback()
#   def _on_auto_sample_toggled(self,
#                               button: Gtk.CheckButton,
#                               ) ->    None:
#       """"""
#       ...
