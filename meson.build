project('nectar',
  version: '0.1.0',
  meson_version: '>= 0.62.0',
  license: 'GPL-3.0-or-later',
)

subdir('data')
subdir('src')

gnome = import('gnome')
# No icon cache update: nectar doesn't install any icons (yet), and
# gtk4-update-icon-cache fails on the missing hicolor directory.
gnome.post_install(
  update_desktop_database: true,
)
