eva_root_dir = get_option('eva_root')
## add gstadmeta.so
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

## add gstadroimeta
libs_meta2 = []
libs_meta2 += cc.find_library('gstadroimeta',
                required : true,
                dirs : [join_paths(eva_root_dir, 'lib')])


inc_meta2 = include_directories(join_paths(eva_root_dir, 'include'))

gstmeta2_dep = declare_dependency(
  dependencies : libs_meta2,
  include_directories: inc_meta2,
)
#### End to declare gstmeta dependency

subdir('classification')
subdir('object-detection')
