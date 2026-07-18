configure_file(
  input: 'land.rob.Nectar.desktop.in',
  output: 'land.rob.Nectar.desktop',
  copy: true,
  install: true,
  install_dir: get_option('datadir') / 'applications',
)

install_data(
  'icons/land.rob.Nectar.svg',
  install_dir: get_option('datadir') / 'icons' / 'hicolor' / 'scalable' / 'apps',
)

configure_file(
  input: 'land.rob.Nectar.metainfo.xml.in',
  output: 'land.rob.Nectar.metainfo.xml',
  copy: true,
  install: true,
  install_dir: get_option('datadir') / 'metainfo',
)
