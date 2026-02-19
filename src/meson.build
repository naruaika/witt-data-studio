gnome = import('gnome')

gnome.compile_resources(
  'witt-data-studio',
  'witt-data-studio.gresource.xml',

  gresource_bundle: true,
        source_dir: [acticondir],
           install: true,
       install_dir: pkgdatadir,
)

configure_file(
          input: 'witt-data-studio.in',
         output: 'witt-data-studio',
  configuration: base_conf,
        install: true,
    install_dir: get_option('bindir'),
   install_mode: 'rwxr-xr-x',
)

root_sources = [
  '__init__.py',
  'application.py',
  'command_palette.py',
  'date_picker.py',
  'environment.py',
  'file_import_csv_view.py',
  'file_import_parquet_view.py',
  'file_import_window.py',
  'file_manager.py',
  'formula_editor_window.py',
  'main.py',
  'status_bar.py',
  'time_picker.py',
  'toolbar.py',
  'utils_color.py',
  'utils_uinterface.py',
  'utils.py',
  'window.py',
]
install_data(root_sources, install_dir: moduledir)

core_sources = [
  'core/__init__.py',
  'core/action.py',
  'core/arithmetic_evaluator.py',
  'core/context_evaluator.py',
  'core/datachart.py',
  'core/datatable.py',
  'core/document.py',
  'core/file_manager.py',
  'core/formula_evaluator.py',
  'core/history.py',
  'core/plugins.py',
  'core/utils_file.py',
  'core/utils_function.py',
  'core/utils_numeric.py',
  'core/utils_polars.py',
  'core/utils_sheet.py',
  'core/utils_string.py',
  'core/utils_temporal.py',
  'core/utils_type.py',
  'core/utils.py',
]
install_data(core_sources, install_dir: moduledir / 'core')

node_sources = [
  'node/__init__.py',
  'node/action.py',
  'node/canvas.py',
  'node/content.py',
  'node/context_menu.py',
  'node/data_type.py',
  'node/editor.py',
  'node/frame.py',
  'node/link.py',
  'node/minimap.py',
  'node/repository.py',
  'node/socket.py',
  'node/widget.py',
]
install_data(node_sources, install_dir: moduledir / 'node')

sheet_sources = [
  'sheet/__init__.py',
  'sheet/action.py',
  'sheet/canvas.py',
  'sheet/display.py',
  'sheet/document.py',
  'sheet/editor.py',
  'sheet/filter_rows_window.py',
  'sheet/formula_bar.py',
  'sheet/renderer.py',
  'sheet/selection.py',
  'sheet/transform_layout.py',
  'sheet/transform_window.py',
  'sheet/view.py',
  'sheet/widget.py',
]
install_data(sheet_sources, install_dir: moduledir / 'sheet')

chart_sources = [
  'chart/__init__.py',
  'chart/action.py',
  'chart/canvas.py',
  'chart/display.py',
  'chart/document.py',
  'chart/editor.py',
  'chart/renderer.py',
  'chart/view.py',
]
install_data(chart_sources, install_dir: moduledir / 'chart')
