pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'avvie')
gnome = import('gnome')

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'avvie.in',
  output: 'avvie',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

avvie_sources = [
  '__init__.py',
  'main.py',
  'res/image-crop.svg',
  'res/pinku.css',
]

install_data(avvie_sources, install_dir: moduledir)
