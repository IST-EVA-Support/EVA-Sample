inc_meta = []
inc_meta += include_directories(join_paths('../src', 'plugins', 'common', 'meta'))
inc_meta += include_directories('../src')
gstmeta_dep = declare_dependency(link_with: [gstadmeta_lib], include_directories: inc_meta)

libs_ex = cc.find_library('pthread', required : false, dirs : [join_paths(eva_root, 'lib')])
ex_dep = declare_dependency(dependencies : libs_ex)

task_code = [
['ex_app',['ex_application.c'], [gst_dep]],
['appsrcsink', ['ex_appsrc_appsink.cpp'], [cv_dep, gst_dep]],
['appsrcsink_ad', ['ex_appsrc_appsink_advanced.cpp'], [cv_dep, gst_dep, ex_dep]],
['getAdMetadata', ['ex_getAdMetadata.cpp'], [cv_dep, gst_dep, ex_dep, gstmeta_dep]]
]

foreach task : task_code
    set_variable(task[0]+'_bin', executable(task[0], task[1], dependencies: task[2]))
endforeach

##### Python sample code #####

py_samples = [
  'classifier_sample.py',
  'segment_sample.py',
  'dummy_box_sample.py',
  'adyolo_sample.py',
  'pipeline_app.py',
  'pipeline_app_call_python_plugin.py',
  'plugin_sample.py'
]

foreach src : py_samples
  configure_file(input : src, output : src, install : true, copy: true,
                 install_dir : join_paths(plugins_install_dir, 'python'))
endforeach
