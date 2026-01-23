project('witt-data-studio',
          version: '0.1.0',
    meson_version: '>= 1.0.0',
  default_options: [ 'warning_level=2', 'werror=false', ],
)

i18n   = import('i18n')
gnome  = import('gnome')
python = import('python')

if get_option('profile') == 'devel'
  profile = '.Devel'
else
  profile = ''
endif

base_application_id = 'com.macipra.witt'
application_id      = base_application_id + profile

pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir  = pkgdatadir / 'witt_data_studio'
icondir    = meson.project_source_root() / 'data' / 'icons' / 'hicolor'
acticondir = icondir / 'scalable' / 'actions'

base_conf = configuration_data()
base_conf.set(    'PYTHON', python.find_installation('python3').full_path())
base_conf.set(    'APP_ID', application_id)
base_conf.set(   'VERSION', meson.project_version())
base_conf.set( 'localedir', get_option('prefix') / get_option('localedir'))
base_conf.set('pkgdatadir', pkgdatadir)

subdir('data')
subdir('src')
subdir('po')

gnome.post_install(
     glib_compile_schemas: true,
    gtk_update_icon_cache: true,
  update_desktop_database: true,
)
