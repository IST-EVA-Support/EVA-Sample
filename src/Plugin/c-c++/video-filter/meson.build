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
