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

install_subdir(
  './',

      install_dir: moduledir,
    exclude_files: ['*.py', '*.ui', '*.css'],
  strip_directory: true,
)
