pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'nectar'

python = import('python')
conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('app_id', 'land.rob.Nectar')
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'nectar.in',
  output: 'nectar',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x',
)

install_data(
  ['__init__.py', 'main.py', 'window.py', 'game.py', 'store.py'],
  install_dir: moduledir,
)

install_data(
  ['../data/wordlists/valid.txt', '../data/wordlists/pangrams.txt'],
  install_dir: moduledir / 'wordlists',
)
