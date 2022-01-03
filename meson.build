project('eva-samples', 'c', 'cpp', version: '0.2', meson_version: '>= 0.56.2')

# project dep
gst_dep = dependency('gstreamer-1.0')

# compiler resource object
cc = meson.get_compiler('c')

opencv_dir = get_option('opencv_dir')

subdir('src')
