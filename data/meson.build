desktop_file = configure_file(
          input: '@0@.desktop.in'.format(base_application_id),
         output: '@0@.desktop.in'.format(base_application_id),
  configuration: base_conf,
)

desktop_file = i18n.merge_file(
        input: desktop_file,
       output: '@0@.desktop'.format(base_application_id),
         type: 'desktop',
       po_dir: '../po',
      install: true,
  install_dir: get_option('datadir') / 'applications'
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils, args: [desktop_file])
endif

appstream_file = i18n.merge_file(
        input: '@0@.metainfo.xml.in'.format(base_application_id),
       output: '@0@.metainfo.xml'.format(base_application_id),
       po_dir: '../po',
      install: true,
  install_dir: get_option('datadir') / 'metainfo'
)

appstreamcli = find_program('appstreamcli', required: false, disabler: true)
test('Validate appstream file',
     appstreamcli,
     args: ['validate', '--no-net', '--explain', appstream_file])

install_data(
  'com.wittara.studio.gschema.xml',
  install_dir: get_option('datadir') / 'glib-2.0' / 'schemas'
)

compile_schemas = find_program('glib-compile-schemas', required: false, disabler: true)
test('Validate schema file',
     compile_schemas,
     args: ['--strict', '--dry-run', meson.current_source_dir()])

service_conf = configuration_data()
service_conf.set('bindir', get_option('prefix') / get_option('bindir'))
service_conf.set('APP_ID', application_id)

configure_file(
          input: '@0@.service.in'.format(base_application_id),
         output: '@0@.service'.format(base_application_id),
  configuration: service_conf,
    install_dir: get_option('datadir') / 'dbus-1' / 'services'
)

subdir('icons')
