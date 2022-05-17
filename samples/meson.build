project('eva-samples', 'c', 'cpp', version: '0.1')

gst_dep = dependency('gstreamer-1.0')

## Declare OpenCV4 dependency
cc = meson.get_compiler('c')

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
  inc_cv = [include_directories(join_paths(opencv_dir, 'include'))]
  if run_command('[', '-d', join_paths(opencv_dir, 'include', 'opencv4'), ']').returncode() == 0
    inc_cv += include_directories(join_paths(opencv_dir, 'include', 'opencv4'))
  endif
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

lib_pthread = cc.find_library('pthread', required: false)
pthread_dep = declare_dependency(dependencies : lib_pthread.found() ? lib_pthread : [])

task_code = [
['ex_app', 'ex_application.c', [gst_dep]],
['appsrcsink', ['ex_appsrc_appsink.cpp'], [cv_dep, gst_dep]],
['appsrcsink_ad', ['ex_appsrc_appsink_advanced.cpp'], [cv_dep, gst_dep, pthread_dep]],
['getAdMetadata', ['ex_getAdMetadata.cpp'], [cv_dep, gst_dep, pthread_dep, gstmeta_dep]]
]

foreach task : task_code
    executable(task[0], task[1], dependencies: task[2])
endforeach

#### adfiltertemplate
inc_gst_video = ''
lib_gst_video = []
if target_machine.system() == 'linux'
	lib_gst_video += cc.find_library('gstvideo-1.0', required : true)
	inc_gst_video = include_directories('/usr/include/gstreamer-1.0')
elif target_machine.system() == 'windows'
	lib_gst_video += cc.find_library('gstvideo-1.0', required : true, dirs: 'C:\ADLINK\gstreamer\lib')
	inc_gst_video = include_directories(join_paths(eva_root_dir, '..', 'gstreamer', 'include', 'gstreamer-1.0'))
endif

gst_video = declare_dependency(
	dependencies : lib_gst_video,
	include_directories : inc_gst_video,
	)
plugin_sources = ['adfiltertemplate/adfiltertemplate.cpp']
adfiltertemplate = library('adfiltertemplate', 
  plugin_sources, 
  cpp_args : [],
  dependencies : [gst_dep, cv_dep, gst_video, gstmeta_dep])
#### End to declare adfiltertemplate
