# Sample Code and It's Compilation Process

This file describes how to build the sample codes and the meaning of each example.

## Build Process

### Step 1. Install require packages

* gstreamer-1.0 >= 1.14.1
* opencv >= 4.5.0 for windows and Linux x86_x64; opencv >= 4.1.1 for Linux ARM

### Step 2. [Windows] Open Visual Studio Prompt

For windows compiler, open windows vs prompt. Take vs2019 as example:

Menu > Visual Studio 2019 > x64 Native Tools Command Prompt for VS 2019

In windows, use this tool to run the commands below.

### Step 3. Install build tool

```
$ pip3 install meson ninja boto3
```

### Step 4. Set environment variable

Run the script file described in Installation Guide in INSTALLING THE ADLINK EVA SDK - Set Environment Variables.

Linux version, assume installed default path to EVA SDK is /opt/adlink/eva, run:

```
$ source /opt/adlink/eva/scripts/setup_eva_envs.sh
```

For windows, assume installed default path to EVA SDK is C:\ADLINK\eva, run gstreamer and EVA bat file:

```
> C:\ADLINK\gstreamer\setupvars.bat
> C:\ADLINK\eva\scripts\setup_eva_envs.bat
```

Set gstreamer and opencv required path to system path, if you had installed EVA. Add those path to system variables, "Path":

C:\ADLINK\gstreamer\bin
C:\ADLINK\gstreamer\lib
C:\ADLINK\gstreamer\lib\gstreamer-1.0
PATH_TO_OPENCV\bin

If you don't want to set opencv path to system variables, remember copy the opencv dependencies besides the built binary.

**<u>Note: The samples used OpenCV GStreamer Wrapper, so it is required to use OpenCV which build with GStreamer.</u>**

### Step 5. Go to sample folder

Assume EVA is installed in EVA_ROOT:

Linux:

Make sure you have the permission to samples folder first.

```
$ cd <EVA_ROOT>
$ sudo chmod +447 samples/
$ cd samples
```

windows:

```
> cd C:\<EVA_ROOT>\samples
```

### Step 6. Build binary

For Linux, use meson to configure the source code and use ninja to build for linux.

```
$ meson build
$ ninja -C build
```

If opencv was installed at other directory location, assign target directory to opencv_dir option like below commands.

```
$ meson build -Dopencv_dir=PATH_TO_OPENCV
$ ninja -C build
```

Remind that the opencv_dir is depends on where user installed. If not provide -Dopencv_dir in command, the default path will used where it can be found set in meson_options.txt. Besides, check 2 parameters "libs_cv"(for libraries) and "inc_cv"(for include files) relative to opencv_dir used in meson.build for the opencv. Check join_paths to where your opencv relative files located is important both in Linux and windows. 

If samples are built in **windows**, meson can set build backend to vs. Also set the opencv_dir option. One more path need to set is eva_root to EVA installed path. Here we assumed EVA is installed in C:\ADLINK\eva. Then build it using meson:

```
$ meson --buildtype=release --backend=vs build -Dopencv_dir=PATH_TO_OPENCV -Deva_root=C:\ADLINK\eva
$ meson compile -C build
```

Then following binary/library will generated in build folder

* ex_app
* appsrcsink
* appsrcsink_ad
* getAdMetadata
* libadfiltertemplate.so (for Linux)/adfiltertemplate.dll (for windows)

Remind copy libadfiltertemplate.so (for Linux)/adfiltertemplate.dll (for windows) to plugins folder under <EVA_ROOT> for convenient use it.

## Sample Codes Introduction

There are twelve sample codes in this folder. 

1. ex_application.c
2. ex_appsrc_appsink.cpp
3. ex_appsrc_appsink_advanced.cpp
4. ex_getAdMetadata.cpp
5. adfiltertemplate.cpp and adfiltertemplate.h in adfiltertemplate folder
6. classifier_sample.py
7. dummy_box_sample.py
8. adyolo_sample.py
9. segment_sample.py
10. plugin_sample.py
11. pipeline_app.py
12. pipeline_app_call_python_plugin.py

### ex_application.c

Example *ex_application.c* demonstrates how to write a GSTREAMER applications. 

Run ex_app binary in terminal or cmd, you will see the moving ball windows displayed.

There are seven main steps to form the application of *ex_application.c*:
• Step 1: Initialize GStreamer
• Step 2: Create the elements
• Step 3: Create the empty pipeline and then build it
• Step 4: Modify the source's properties
• Step 5: Start playing the pipeline
• Step 6: Message handling
• Step 7: Free resources
Here, we will take *ex_application.c* for explanation.

#### Step 1: Initialize GStreamer

In this step, it is required and must to initialize the GStreamer by init for the application. 

```
	/* Initialize GStreamer */
	gst_init (&argc, &argv);
```

#### Step 2: Create the elements

Create the elements by factory.

```
	/* Create the elements */
	source = gst_element_factory_make ("videotestsrc", "source");
	sink = gst_element_factory_make ("autovideoconvert", "sink");
```

#### Step 3: Create the empty pipeline and then build it

Generate a pipe line in order to put all element in it and then playing it later.

```
	/* Create the empty pipeline */
	pipeline = gst_pipeline_new ("test-pipeline");
	
	/* Build the pipeline */
	gst_bin_add_many (GST_BIN (pipeline), source, sink, NULL);
```

#### Step 4: Modify the source's properties

This step is optional if you are going to set some properties to each element. In *ex_application.c*, we required to set properties, pattern, for switch the pattern images we are going to use:

```
	/* Modify the source's properties */
	g_object_set (source, "pattern", 18, NULL);
```

#### Step 5: Start playing the pipeline

Playing the pipeline we created:

```
	/* Start playing */
	ret = gst_element_set_state (pipeline, GST_STATE_PLAYING);
```

#### Step 6: Message handling

This step makes sure the message be thrown by the pipeline we created through the GstBus. This message handling could customize based on different event thrown.

```
	/* Wait until error or EOS */
	bus = gst_element_get_bus (pipeline);
	msg = gst_bus_timed_pop_filtered (bus, GST_CLOCK_TIME_NONE, GST_MESSAGE_ERROR | GST_MESSAGE_EOS);
	
	/* Parse message */
	if (msg != NULL) 
	{
		GError *err;
		gchar *debug_info;

		switch (GST_MESSAGE_TYPE (msg)) 
		{
		    case GST_MESSAGE_ERROR:
		    gst_message_parse_error (msg, &err, &debug_info);
		    g_printerr ("Error received from element %s: %s\n", GST_OBJECT_NAME (msg->src), err->message);
		    g_printerr ("Debugging information: %s\n", debug_info ? debug_info : "none");
		    g_clear_error (&err);
		    g_free (debug_info);
		    break;
		    case GST_MESSAGE_EOS:
		    g_print ("End-Of-Stream reached.\n");
		    break;
		    default:
		    /* We should not reach here because we only asked for ERRORs and EOS */
		    g_printerr ("Unexpected message received.\n");
		    break;
		}
		gst_message_unref (msg);
	}
```


#### Step 7: Free resources

Finally, release all used GStreamer instances:

```
	/* Free resources */
	gst_object_unref (bus);
	gst_element_set_state (pipeline, GST_STATE_NULL);
	gst_object_unref (pipeline);
```

### ex_appsrc_appsink.cpp and ex_appsrc_appsink_advanced.cpp

The example codes *ex_appsrc_appsink.cpp* and *ex_appsrc_appsink_advanced.cpp* were detailed described in "Integrating the GStreamer Plugin" in the Programming Guide. More details could be referenced in the document, ***Edge Vision Analytics SDK Programming Guide*** in Chapter 6.

### ex_getAdMetadata.cpp

This sample shows you how to retrieve the adlink metadata from the application. This sample is alike ex_appsrc_appsink_advanced.cpp. First, include the *gstadmeta.h*:

```
#include "gstadmeta.h"
```

 Second, Add the subfunction for retrieving the GstAdBatchMeta pointer from GstBuffer:

```
GstAdBatchMeta* gst_buffer_get_ad_batch_meta(GstBuffer* buffer)
{
    gpointer state = NULL;
    GstMeta* meta;
    const GstMetaInfo* info = GST_AD_BATCH_META_INFO;
    
    while ((meta = gst_buffer_iterate_meta (buffer, &state))) 
    {
        if (meta->info->api == info->api) 
        {
            GstAdMeta *admeta = (GstAdMeta *) meta;
            if (admeta->type == AdBatchMeta)
                return (GstAdBatchMeta*)meta;
        }
    }
    return NULL;
}
```

Third, in the callback function, new_sample, of appsink has an extra code block which is going to get the detection metadata:

```
GstAdBatchMeta *meta = gst_buffer_get_ad_batch_meta(buffer);
if(meta != NULL)
{
    AdBatch &batch = meta->batch; 
    VideoFrameData frame_info = batch.frames[0];
    int detectionResultNumber = frame_info.detection_results.size();
    cout << "detection result number = " << detectionResultNumber << endl;
    for(int i = 0 ; i < detectionResultNumber ; ++i)
    {
        cout << "========== metadata in application ==========\n";
        cout << "Class = " << frame_info.detection_results[i].obj_id << endl;
        cout << "Label = " << frame_info.detection_results[i].obj_label << endl;
        cout << "Prob =  " << frame_info.detection_results[i].prob << endl;
        cout << "(x1, y1, x2, y2) = (" 
        << frame_info.detection_results[i].x1 << ", " 
        << frame_info.detection_results[i].y1 << ", "
        << frame_info.detection_results[i].x2 << ", " 
        << frame_info.detection_results[i].y2 << ")" << endl;
        cout << "=============================================\n";
    }
}
```

The metadata structure could be find in ***Edge Vision Analytics SDK Programming Guide : How to Use ADLINK Metadata*** in Chapter 5. Based on the structure, AdBatch can get the frame in vector and the inference data are stored in each frame based on the inference type: classification, detection, segmentation. Here, the sample use detection to illustrate get the metadata and print out obj_id,  obj_label, prob and the box coordination to the terminal or cmd.

### adfiltertemplate

This sample illustrate how to get the image data and metadata inside the plugin. More details could be referenced in the document, ***Edge Vision Analytics SDK Programming Guide*** in Chapter 2.

### classifier_sample.py

This is a gstreamer plugin sample that wrote in python. Used to interpret classification inference result into human readable format and save in gstreamer metadata. Then you can using inference information in stream flow.

##### Pipeline sample

```
$ gst-launch-1.0 filesrc ! decodebin ! videoconvert ! advino model=YOUR_MODEL  ! classifier_sample label=YOUR_LABEL class-num=1000 ! admetadrawer ! videoconvert ! ximagesink
```

### dummy_box_sample.py

This is a gstreamer plugin sample that wrote in python. It will generate five dummy boxs and randomly move in every frame. And boxs information will save in gstreamer metadata. Then you can using inference information in stream flow. This plugin was used for generate fake box to debug detection in other plugin.

##### Pipeline sample

```
$ gst-launch-1.0 filesrc ! decodebin ! videoconvert ! advino model=YOUR_MODEL  ! dummy_box_sample ! admetadrawer ! videoconvert ! ximagesink
```

###  adyolo_sample.py

This is yolo interpret python sample, it will draw yolo's detection box and class.
User can inspect plugin to list configurable inference attribute like output blob 
size, input width and height or anchor box.

Plugin design defaul to support YoloV3, however user can set other mask and anchor.
There is one YoloV3-tiny pipeline example at following.

##### How to convert yolov3 model to OpenVINO

Please reference to below link.
https://docs.openvinotoolkit.org/latest/openvino_docs_MO_DG_prepare_model_convert_model_tf_specific_Convert_YOLO_From_Tensorflow.html

##### Pipeline sample

```
$ gst-launch-1.0 filesrc ! decodebin ! videoconvert ! advino model=YOUR_YOLO_MODEL ! adsample_yolo_py blob-size=26,52,13 threshold=0.8 input-width=416 input-height=416 label-file=YOUR_LABEL  ! videoconvert ! ximagesink
```

##### YoloV3-tiny sample

```
$ gst-launch-1.0 filesrc ! decodebin ! videoconvert ! advino model=YOUR_YOLO_MODEL ! adsample_yolo_py threshold=0.4 input-width=416 input-height=416 label-file=YOUR_LABEL mask='(0,1,2),(3,4,5)' anchor='(10, 14),(23, 27),(37, 58),(81,82),(135,169),(344,319)' blob-size="26,13"  ! videoconvert ! ximagesink
```

### segment_sample.py

This is segmentation python translator sample, it will parse the segmentation result into adlink metadata.
User can inspect plugin to list configurable inference attribute like output blob size, input width and height or label id and label name.

##### Pipeline sample

```
filesrc ! decodebin ! videoconvert ! advino device=CPU model=YOUR_SEGMENTATION_MODEL ! segment_sample ! admetadrawer ! videoconvert ! ximagesink
```

### plugin_sample.py

Demonstrate how to write a plugin which can handle metadata and image buffer.
The main task of this sample is :
- Read inference result ( Boxes ) from adlink metadata
- Draw the box inference result in image.

In this sample, the detail comment on the section with !!!ADLINK!!!' is included (but not exclusive) to guide user step-by-step from :
- Understand metadata structure for detection box ( which included box and pose identification )
- Set the name of your plugin which will use in pipeline 
- Set/Get the properties of plugin
- Get the metadata from image stream
- Get the image buffer from image stream and draw to it

There is one pipeline example as following which will read detection box result from a YOLO model then draw result on image stream :
gst-launch-1.0 filesrc location=YOUR_VIDEO_FILE ! decodebin ! videoconvert ! adrt model=YOUR_YOLO_MODEL ! adsample_yolo_py input-width=416 input-height=416 label-file=YOUR_LABEL blob-size="52,26,13" ! adlink_plugin_sample ! videoconvert ! ximagesink

### pipeline_app.py and pipeline_app_call_python_plugin.py

More details could be referenced in the document, ***Edge Vision Analytics SDK Programming Guide*** in Chapter 6.