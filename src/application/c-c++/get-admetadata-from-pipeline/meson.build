## add gstadmeta.so
eva_root_dir = get_option('eva_root')
libs_meta = []
libs_meta += cc.find_library('gstadmeta',
                required : true,
                dirs : [join_paths(eva_root_dir, 'lib')])


inc_meta = include_directories(join_paths(eva_root_dir, 'include'))

gstmeta_dep = declare_dependency(
  dependencies : libs_meta,
  include_directories: inc_meta,
)
#### End to declare gstmeta dependency

subdir('object-detection')
