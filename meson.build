project('avvie',
          version: '2.1',
    meson_version: '>= 0.59.0',
  default_options: [ 'warning_level=2',
                   ],
)

i18n = import('i18n')

gnome = import('gnome')

python = import('python')


message('Looking for dependencies')

python3_required_modules = ['piexif', 'cairo', 'PIL', 'gi']

python_bin = python.find_installation('python3', modules: python3_required_modules)

dependencies = [
	dependency('gtk4'),
	dependency('libadwaita-1'),
	dependency('libnotify'),
]


subdir('data')
subdir('src')
subdir('po')

gnome.post_install(
  gtk_update_icon_cache: true,
  update_desktop_database: true,
)
