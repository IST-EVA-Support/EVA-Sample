lib_pthread = cc.find_library('pthread', required: false)
pthread_dep = declare_dependency(dependencies : lib_pthread.found() ? lib_pthread : [])

executable('get-stream-data-from-pipeline', ['get-stream-data-from-pipeline.cpp'], dependencies: [cv_dep, gst_dep, pthread_dep])
