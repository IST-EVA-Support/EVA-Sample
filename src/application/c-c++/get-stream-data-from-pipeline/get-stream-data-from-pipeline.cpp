// **
// Demo senario: appsrc ! clockoverlay ! videoconvert ! appsink
// This example only show how to feed frame data to appsrc and get the frame data from appsink.
// So this example does not deal with any other detail concern about snchronize or other tasks.
// Only show how to use the appsink and appsrc for user who is interested with them.
// **
#include "opencv2/opencv.hpp"
#include <iostream>
#include <stdio.h>
#include <thread>
#include <chrono>
#include <vector>
#include <gst/gst.h>

using namespace cv;
using namespace std;

static GMainLoop *loop;
GstElement *pipeline, *appsrc, *clockoverlay, *conv, *appsink;
vector<Mat> grabVec;
vector<Mat> pipeLineOutputVec;
cv::Mat img(cv::Size(640, 480), CV_8UC3);

static void cb_need_data(GstElement *appsrc, guint unused_size, gpointer user_data)
{
    static GstClockTime timestamp = 0;
    GstBuffer *buffer;
    guint size;
    GstFlowReturn ret;
    GstMapInfo map;

    size = 640 * 480 * 3;

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

    g_signal_emit_by_name (appsrc, "push-buffer", buffer, &ret);
    gst_buffer_unref (buffer);

    if (ret != GST_FLOW_OK) 
        g_main_loop_quit (loop);
}

static GstFlowReturn new_sample(GstElement *sink, gpointer *udata) 
{
    GstSample *sample;

    g_signal_emit_by_name (sink, "pull-sample", &sample);
    if (sample) 
    {
        GstMapInfo map;
        guint size = 640 * 480 * 3;
        GstBuffer *buffer = gst_buffer_new_allocate (NULL, size, NULL);
        
        buffer = gst_sample_get_buffer (sample);
        
        gst_buffer_map(buffer, &map, GST_MAP_READ);
        
        memcpy(img.data, (guchar *)map.data, gst_buffer_get_size(buffer));
        pipeLineOutputVec.push_back(img.clone());
        
        gst_buffer_unmap(buffer, &map);
        gst_buffer_unref (buffer);
        
        gst_sample_unref (sample);
        return GST_FLOW_OK;
    }
    
    return GST_FLOW_ERROR;
}



static void free_appsrc_appsink_pipeline()
{
    gst_element_set_state (pipeline, GST_STATE_NULL);
    gst_object_unref (GST_OBJECT (pipeline));
    g_main_loop_unref (loop);
}

static void establish_appsrc_appsink_pipeline()
{
    /* init GStreamer */
    gst_init (NULL, NULL);
    loop = g_main_loop_new (NULL, FALSE);

    /* setup pipeline */
    pipeline = gst_pipeline_new ("pipeline");
    appsrc = gst_element_factory_make ("appsrc", "source");
    clockoverlay = gst_element_factory_make("clockoverlay", "clockoverlay");
    conv = gst_element_factory_make ("videoconvert", "conv");
    appsink = gst_element_factory_make ("appsink", "appsink");

    /* setup */
    g_object_set (G_OBJECT (appsrc), "caps",
                  gst_caps_new_simple ("video/x-raw", "format", G_TYPE_STRING, "BGR",
                                       "width", G_TYPE_INT, 640, "height", G_TYPE_INT, 480,
                                       "framerate", GST_TYPE_FRACTION, 30, 1,NULL), NULL);
    gst_bin_add_many (GST_BIN (pipeline), appsrc, clockoverlay, conv, appsink, NULL);
    gst_element_link_many (appsrc, clockoverlay, conv, appsink, NULL);

    /* setup appsrc */
    g_object_set (G_OBJECT (appsrc), "stream-type", 0, "format", GST_FORMAT_TIME, NULL);
    g_signal_connect (appsrc, "need-data", G_CALLBACK (cb_need_data), NULL);

    /* setup appsink */
    g_object_set (G_OBJECT(appsink), "emit-signals", TRUE, NULL);
    g_signal_connect (appsink, "new-sample", G_CALLBACK (new_sample), NULL);
    
    /* play */
    gst_element_set_state (pipeline, GST_STATE_PLAYING);
    
	//g_main_loop_run (loop); // for main loop
	while(true)
	{
		this_thread::sleep_for(chrono::milliseconds(10));
	}
    
    free_appsrc_appsink_pipeline();
}


int main(int, char**)
{
    thread pipethread(establish_appsrc_appsink_pipeline);
    
    Mat frame;
    Mat resize_frame;
 
#ifdef _WIN32
    VideoCapture cap("ksvideosrc ! videoscale ! video/x-raw, width=1024, height=768 ! videoconvert ! appsink", CAP_GSTREAMER);
#else
    VideoCapture cap("v4l2src ! videoscale ! video/x-raw, width=1024, height=768 ! videoconvert ! appsink", CAP_GSTREAMER);
#endif
    
    if (!cap.isOpened()) 
    {
        cerr << "ERROR! Unable to open camera\n";
        system("pause");
        return -1;
    }
    
    cv::VideoWriter writer;
#ifdef _WIN32
    writer.open("appsrc ! videoconvert ! video/x-raw, format=BGR, width=640, height=480, framerate=30/1 ! videoconvert ! d3dvideosink sync=false", CAP_GSTREAMER, 0, 30, cv::Size(640, 480), true);
#else
    writer.open("appsrc ! videoconvert ! video/x-raw, format=BGR, width=640, height=480, framerate=30/1 ! videoconvert ! ximagesink sync=false", CAP_GSTREAMER, 0, 30, cv::Size(640, 480), true);
#endif

    if (!writer.isOpened()) 
    {
        printf("=ERR= can't create writer\n");
        return -1;
    }
    
    //--- GRAB AND WRITE LOOP
    cout << "Start grabbing" << endl;
    
    for (;;)
    {
        cap.read(frame);
        if (frame.empty()) 
        {
            cerr << "ERROR! blank frame grabbed\n";
            break;
        }
        cv::resize(frame, resize_frame,Size(640,480));
        writer.write(resize_frame);
        
        grabVec.push_back(resize_frame.clone());
        imshow("OpenCV Live", frame);
        if(pipeLineOutputVec.size() > 0)
        {
            imwrite("a.bmp", pipeLineOutputVec[0]);
            pipeLineOutputVec.erase(pipeLineOutputVec.begin());
        }

        if (waitKey(5) >= 0)
            break;
        
        this_thread::sleep_for(chrono::milliseconds(10));
    }
    cap.release();
    frame.release();
    resize_frame.release();
    return 0;
}
