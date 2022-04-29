project('avvie',
          version: '0.1.0',
    meson_version: '>= 0.59.0',
  default_options: [ 'warning_level=2',
                   ],
)

i18n = import('i18n')

gnome = import('gnome')

python = import('python')


message('Looking for dependencies')
python_bin = python.find_installation('python3')
if not python_bin.found()
    error('No valid python binary found')
else
    message('Found python binary')
endif

dependencies = [
	dependency('gtk4'),
	dependency('libadwaita-1'),
	dependency('libnotify'),
]

# Support Debian non-standard python paths
# Fallback to Meson python3 module if command fails
message('Getting python install path')
py3_purelib = ''
r = run_command(python_bin.full_path(), '-c', 'from distutils.sysconfig import get_python_lib; print(get_python_lib(prefix=""))', check: false)
if r.returncode() != 0
  py3_purelib = python.sysconfig_path('purelib')
  if not py3_purelib.endswith('site-packages')
    error('Cannot find python install path')  endif
  python_dir = py3_purelib
else
  python_dir = r.stdout().strip()
endif

python3_required_modules = ['piexif', 'cairo', 'PIL', 'gi']

foreach p : python3_required_modules
  # Source: https://docs.python.org/3/library/importlib.html#checking-if-a-module-can-be-imported
  script = 'import importlib.util; import sys; exit(1) if importlib.util.find_spec(\''+ p +'\') is None else exit(0)'
  if run_command(python_bin, '-c', script).returncode() != 0
    error('Required Python3 module \'' + p + '\' not found')
  endif
endforeach


subdir('data')
subdir('src')
subdir('po')

gnome.post_install(
  gtk_update_icon_cache: true,
  update_desktop_database: true,
)
