# application projects
#basic_pipeline = subproject('application/c-c++/generate-a-basic-pipeline')

lib_pthread = cc.find_library('pthread', required: false)
pthread_dep = declare_dependency(dependencies : lib_pthread.found() ? lib_pthread : [])

## Declare OpenCV4 dependency
opencv_dir = get_option('opencv_dir')
libs_cv = []
req_cv_libs = ['core', 'imgproc', 'video', 'videoio', 'imgcodecs', 'highgui']
inc_cv = ''

if target_machine.system() == 'linux'
  foreach lib_name : req_cv_libs
    libs_cv += cc.find_library('opencv_' + lib_name,
                   required : true,
                   dirs : [join_paths(opencv_dir, 'lib'),
                   join_paths(opencv_dir, 'lib', '@0@-linux-gnu'.format(target_machine.cpu()))])
  endforeach
  inc_cv = include_directories(join_paths(opencv_dir, 'include', 'opencv4'))
elif target_machine.system() == 'windows'
  foreach lib_name : req_cv_libs
    libs_cv += cc.find_library('opencv_' + lib_name + (get_option('buildtype') == 'release' ? '450' : '450d'),
                   required : true,
                   dirs : [join_paths(opencv_dir, 'lib')])
  endforeach
  inc_cv = include_directories(join_paths(opencv_dir, 'include'))
endif

cv_dep = declare_dependency(
  dependencies : libs_cv,
  include_directories: inc_cv,
)
#### End to declare OpenCV4 dependency

subdir('application')
