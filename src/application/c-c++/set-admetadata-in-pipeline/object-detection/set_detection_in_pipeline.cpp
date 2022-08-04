// **
// Demo senario: appsrc ! admetadrawer ! videoconvert ! ximagesink
// 
// This example only show how to feed frame data to appsrc and set object detections to adlink metadata.
// So this example does not deal with any other detail concern about snchronize or other tasks.
// Only show how to set the adlink metdata through appsrc for user who is interested with them.
// **
#include "opencv2/opencv.hpp"
#include <iostream>
#include <stdio.h>
#include <thread>
#include <chrono>
#include <vector>
#include <gst/gst.h>

#include "gstadmeta.h"

using namespace cv;
using namespace std;

static GMainLoop *loop;
GstElement *pipeline, *videotestsrc, *filtercaps, *appsink, *appsrc, *drawer, *videoconvert, *ximagesink;
vector<Mat> grabVec;
int cols, rows, depth, channels;

static void cb_need_data(GstElement *appsrc, guint unused_size, gpointer user_data)
{
    static GstClockTime timestamp = 0;
    gpointer state = NULL;
    GstBuffer *buffer;
    GstAdBatchMeta* meta;
    const GstMetaInfo* info = GST_AD_BATCH_META_INFO;
    guint size;
    GstFlowReturn ret;
    GstMapInfo map;

    size = cols * rows * channels;

    buffer = gst_buffer_new_allocate (NULL, size, NULL);
    gst_buffer_map(buffer, &map, GST_MAP_WRITE);

    if( grabVec.size() > 0 )
    {
        memcpy((guchar *)map.data, grabVec[0].data, gst_buffer_get_size(buffer));
        grabVec.erase(grabVec.begin());
    }
    gst_buffer_unmap(buffer, &map);
    
    GST_BUFFER_PTS (buffer) = timestamp;
    GST_BUFFER_DURATION (buffer) = gst_util_uint64_scale_int (1, GST_SECOND, 2);

    timestamp += GST_BUFFER_DURATION (buffer);

    meta = (GstAdBatchMeta *)gst_buffer_add_meta(buffer, info, &state);
        
    bool frame_exist = meta->batch.frames.size() > 0 ? true : false;
    if(!frame_exist)
    {
        VideoFrameData frame_info;
        std::vector<std::string> labels = {"water bottle", "camera", "chair", "person", "slipper"};
	std::vector<adlink::ai::DetectionBoxResult> random_boxes;
        srand( time(NULL) );

	// Generate random dummy box here
	adlink::ai::DetectionBoxResult random_box;
	int i = rand() % 5;
	random_box.obj_id = i;
	random_box.obj_label = labels[i];
	random_box.prob = (double)( rand() % 1000 )/1000;
	random_box.x1 = (double)( rand() % 3 + 1 )/10;	// 0.1~0.3
	random_box.x2 = (double)( rand() % 3 + 7 )/10;	// 0.7~0.9
	random_box.y1 = (double)( rand() % 3 + 1 )/10;	// 0.1~0.3
	random_box.y2 = (double)( rand() % 3 + 7 )/10;	// 0.7~0.9

	frame_info.stream_id = " ";
	frame_info.width = cols;
	frame_info.height = rows;
	frame_info.depth = depth;
	frame_info.channels = channels;
	frame_info.device_idx = 0;
        frame_info.detection_results.push_back(random_box);
	meta->batch.frames.push_back(frame_info);
    }

    g_signal_emit_by_name (appsrc, "push-buffer", buffer, &ret);
    gst_buffer_unref (buffer);

    if (ret != GST_FLOW_OK) 
        g_main_loop_quit (loop);
}

static void free_pipeline()
{
    gst_element_set_state (pipeline, GST_STATE_NULL);
    gst_object_unref (GST_OBJECT (pipeline));
    g_main_loop_unref (loop);
}

static void establish_thread_pipeline()
{
    /* init GStreamer */
    gst_init (NULL, NULL);
    loop = g_main_loop_new (NULL, FALSE);

    /* setup pipeline */
    pipeline = gst_pipeline_new ("pipeline");
    appsrc = gst_element_factory_make ("appsrc", "appsrc");
    drawer = gst_element_factory_make("admetadrawer", "drawer");
    videoconvert = gst_element_factory_make("videoconvert", "videoconvert");
    ximagesink = gst_element_factory_make("ximagesink", "ximagesink");

    /* setup appsrc*/
    g_object_set (G_OBJECT (appsrc), "caps",
                  gst_caps_new_simple ("video/x-raw", "format", G_TYPE_STRING, "BGR",
                                       "width", G_TYPE_INT, 640, "height", G_TYPE_INT, 480,
                                       "framerate", GST_TYPE_FRACTION, 30, 1,NULL), NULL);
    g_object_set (G_OBJECT (appsrc), "stream-type", 0, "format", GST_FORMAT_TIME, NULL);
    g_signal_connect (appsrc, "need-data", G_CALLBACK (cb_need_data), NULL);

    gst_bin_add_many (GST_BIN (pipeline), appsrc,drawer, videoconvert, ximagesink, NULL);
    gst_element_link_many (appsrc, drawer, videoconvert, ximagesink, NULL);
 
    /* play */
    gst_element_set_state (pipeline, GST_STATE_PLAYING);
    
    while(true)
    {
        this_thread::sleep_for(chrono::milliseconds(10));
    }
    free_pipeline();
}

int main(int, char**)
{
    Mat frame;
 
    VideoCapture cap("videotestsrc ! video/x-raw, width=640, height=480, framerate=30/1 ! videoconvert ! appsink", CAP_GSTREAMER);
    
    if (!cap.isOpened()) 
    {
        cerr << "ERROR! Unable to open camera\n";
        system("pause");
        return -1;
    }

    cout << "Start grabbing" << endl;

    /* get frame size */
    cap.read(frame);
    cols = frame.cols;
    rows = frame.rows;
    depth = frame.depth();
    channels = frame.channels();
    thread pipethread(establish_thread_pipeline);
    
    while (true)
    {
        if (frame.empty()) 
        {
            cerr << "ERROR! blank frame grabbed\n";
            break;
        }
        
        grabVec.push_back(frame.clone());
        
        this_thread::sleep_for(chrono::milliseconds(10));

        cap.read(frame);
    }

    cap.release();
    frame.release();
    return 0;
}
