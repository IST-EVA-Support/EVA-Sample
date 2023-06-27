// **
// Demo senario: 
// gst-launch-1.0 videotestsrc ! video/x-raw, format=BGR, width=320, height=240, framerate=30/1 ! adsetclassification ! appsink

// This example only show how to get adlink metadata version 2 from appsink.
// So this example does not deal with any other detail concern about snchronize or other tasks.
// Only show how to retrieve the adlink metdata for user who is interested with them.
// **
#include "opencv2/opencv.hpp"
#include <iostream>
#include <stdio.h>
#include <thread>
#include <chrono>
#include <vector>
#include <gst/gst.h>

#include <gstadroi_frame.h>

using namespace cv;
using namespace std;

static GMainLoop *loop;
GstElement *pipeline, *videotestsrc, *filtercaps, *adsetclassification, *appsink;
vector<Mat> pipeLineOutputVec;
cv::Mat img(cv::Size(320, 240), CV_8UC3);

static GstFlowReturn new_sample(GstElement *sink, gpointer *udata) 
{
    GstSample *sample;

    g_signal_emit_by_name (sink, "pull-sample", &sample);
    if (sample) 
    {
        GstMapInfo map;
        guint size = 320 * 240 * 3;
        GstBuffer *buffer = gst_buffer_new_allocate (NULL, size, NULL);
        
        buffer = gst_sample_get_buffer (sample);
        
        gst_buffer_map(buffer, &map, GST_MAP_READ);
        
        std::vector<QueryResult> results = gst_buffer_adroi_query(buffer, "//");
        for(unsigned int i = 0; i < results.size(); ++i)
        {
            QueryResult queryResult = results[i];
            for(auto roi: queryResult.rois)
            {
                if(roi->category == "box")
                {
                    auto box = std::static_pointer_cast<Box>(roi);
                    auto labelInfo = std::static_pointer_cast<Classification>(roi->datas.at(0));
                    
                    cout << "===== metadata version 2 in application =====\n";
                    cout << "Label ID = " << labelInfo->labelID << endl;
                    cout << "Label = " << labelInfo->label << endl;
                    cout << "Prob =  " << labelInfo->confidence << endl;
                    cout << "=============================================\n";
                }
                
            }
        }
        
        memcpy(img.data, (guchar *)map.data, gst_buffer_get_size(buffer));
        pipeLineOutputVec.push_back(img.clone());
        
        gst_buffer_unmap(buffer, &map);
        
        gst_sample_unref (sample);
        this_thread::sleep_for(chrono::milliseconds(1));
        return GST_FLOW_OK;
    }
    
    return GST_FLOW_ERROR;
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
    videotestsrc = gst_element_factory_make ("videotestsrc", "source");
    filtercaps = gst_element_factory_make ("capsfilter", "filtercaps");
    adsetclassification = gst_element_factory_make("adsetclassification", "setclassification");
    appsink = gst_element_factory_make ("appsink", "appsink");

    /* setup filtercaps*/
    g_object_set (G_OBJECT (filtercaps), "caps",
                  gst_caps_new_simple ("video/x-raw", "format", G_TYPE_STRING, "BGR",
                                       "width", G_TYPE_INT, 320, "height", G_TYPE_INT, 240,
                                       "framerate", GST_TYPE_FRACTION, 30, 1, NULL), NULL);
    gst_bin_add_many (GST_BIN (pipeline), videotestsrc, filtercaps, adsetclassification, appsink, NULL);
    gst_element_link_many (videotestsrc, filtercaps, adsetclassification, appsink, NULL);

    /* setup appsink */
    g_object_set (G_OBJECT(appsink), "emit-signals", TRUE, NULL);
    g_signal_connect (appsink, "new-sample", G_CALLBACK (new_sample), NULL);
    
    /* play */
    gst_element_set_state (pipeline, GST_STATE_PLAYING);
    g_main_loop_run (loop);
    
    free_pipeline();
}


int main(int, char**)
{
    thread pipethread(establish_thread_pipeline);
    cv::Mat img_show(cv::Size(320, 240), CV_8UC3);
    while(true)
    {
        if(pipeLineOutputVec.size() > 0)
        {
            img_show = pipeLineOutputVec[0].clone();
            imwrite("a.bmp", img_show);
            pipeLineOutputVec.erase(pipeLineOutputVec.begin());
        }
        this_thread::sleep_for(chrono::milliseconds(1));
    }
    
    return 0;
}
