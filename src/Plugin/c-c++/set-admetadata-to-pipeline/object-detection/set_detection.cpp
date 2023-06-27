//**
//   gst-launch-1.0 videotestsrc ! video/x-raw, width=640, height=480 ! adsetobjectdetection ! draw_roi ! videoconvert ! ximagesink
//**

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "adsetobjectdetection.h"

#include <gst/gst.h>
#include <gst/video/video.h>
#include <gst/video/gstvideofilter.h>
#include <glib/gstdio.h>

#include <iostream>
#include <vector>
#include <string>
#include <stdlib.h> // include random value function
#include <time.h>   // include time
#include <gstadroi_frame.h> // include gstadroi_frame.h for retrieving the inference results
#include <gstadroi_batch.h> // include gstadroi_batch.h for retrieving the inference results

#define PLUGIN_NAME "adsetobjectdetection"

#define AD_SET_OBJECT_DETECTION_LOCK(sample_filter) \
  (g_rec_mutex_lock(&((AdSetObjectDetection *)sample_filter)->priv->mutex))

#define AD_SET_OBJECT_DETECTION_UNLOCK(sample_filter) \
  (g_rec_mutex_unlock(&((AdSetObjectDetection *)sample_filter)->priv->mutex))

GST_DEBUG_CATEGORY_STATIC(ad_set_object_detection_debug_category);
#define GST_CAT_DEFAULT ad_set_object_detection_debug_category

enum
{
  PROP_0
};

struct _AdSetObjectDetectionPrivate
{
  GRecMutex mutex;
};

static GstStaticPadTemplate sink_factory = GST_STATIC_PAD_TEMPLATE("sink",
                                                                   GST_PAD_SINK,
                                                                   GST_PAD_ALWAYS,
                                                                   GST_STATIC_CAPS(GST_VIDEO_CAPS_MAKE("{ BGR }")));

static GstStaticPadTemplate src_factory = GST_STATIC_PAD_TEMPLATE("src",
                                                                  GST_PAD_SRC,
                                                                  GST_PAD_ALWAYS,
                                                                  GST_STATIC_CAPS(GST_VIDEO_CAPS_MAKE("{ BGR }")));

#define DEBUG_INIT \
  GST_DEBUG_CATEGORY_INIT(GST_CAT_DEFAULT, PLUGIN_NAME, 0, "debug category for set object detection element");

G_DEFINE_TYPE_WITH_CODE(AdSetObjectDetection, ad_set_object_detection, GST_TYPE_VIDEO_FILTER,
                        G_ADD_PRIVATE(AdSetObjectDetection)
                            DEBUG_INIT)

static void ad_set_object_detection_set_property(GObject *object, guint property_id, const GValue *value, GParamSpec *pspec);
static void ad_set_object_detection_get_property(GObject *object, guint property_id, GValue *value, GParamSpec *pspec);
static void ad_set_object_detection_dispose(GObject *object);
static void ad_set_object_detection_finalize(GObject *object);
static GstFlowReturn ad_set_object_detection_transform_frame_ip(GstVideoFilter *filter, GstVideoFrame *frame);
static void setObjectDetectionData(GstBuffer* buffer, GstPad *pad);

static void
ad_set_object_detection_class_init(AdSetObjectDetectionClass *klass)
{
  // Hierarchy
  GObjectClass *gobject_class;
  GstElementClass *gstelement_class;
  GstVideoFilterClass *gstvideofilter_class;

  gobject_class = (GObjectClass *)klass;
  gstvideofilter_class = (GstVideoFilterClass *)klass;
  gstelement_class = (GstElementClass *)klass;

  GST_DEBUG_CATEGORY_INIT(GST_CAT_DEFAULT, PLUGIN_NAME, 0, PLUGIN_NAME);

  // override method
  gobject_class->set_property = ad_set_object_detection_set_property;
  gobject_class->get_property = ad_set_object_detection_get_property;
  gobject_class->dispose = ad_set_object_detection_dispose;
  gobject_class->finalize = ad_set_object_detection_finalize;

  gst_element_class_set_static_metadata(gstelement_class,
                                        "Set object detection result element example", "Video/Filter",
                                        "Example of setting object detection result",
                                        "Jessie Huang <yun-chieh.huang@adlinktech.com>");

  // adding a pad
  gst_element_class_add_pad_template(gstelement_class,
                                     gst_static_pad_template_get(&src_factory));
  gst_element_class_add_pad_template(gstelement_class,
                                     gst_static_pad_template_get(&sink_factory));

  gstvideofilter_class->transform_frame_ip =
      GST_DEBUG_FUNCPTR(ad_set_object_detection_transform_frame_ip);
}

static void	// initialize instance
ad_set_object_detection_init(AdSetObjectDetection *
                            sample_filter)
{
  sample_filter->priv = (AdSetObjectDetectionPrivate *)ad_set_object_detection_get_instance_private(sample_filter);

  g_rec_mutex_init(&sample_filter->priv->mutex);
}

static void
ad_set_object_detection_set_property(GObject *object, guint property_id,
                                const GValue *value, GParamSpec *pspec)
{
  AdSetObjectDetection *sample_filter = AD_SET_OBJECT_DETECTION(object);

  AD_SET_OBJECT_DETECTION_LOCK(sample_filter);

  switch (property_id)
  {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID(object, property_id, pspec);
    break;
  }

  AD_SET_OBJECT_DETECTION_UNLOCK(sample_filter);
}

static void
ad_set_object_detection_get_property(GObject *object, guint property_id,
                                GValue *value, GParamSpec *pspec)
{
  AdSetObjectDetection *sample_filter = AD_SET_OBJECT_DETECTION(object);

  AD_SET_OBJECT_DETECTION_LOCK(sample_filter);

  switch (property_id)
  {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID(object, property_id, pspec);
    break;
  }

  AD_SET_OBJECT_DETECTION_UNLOCK(sample_filter);
}

static void
ad_set_object_detection_dispose(GObject *object)
{
}

static void
ad_set_object_detection_finalize(GObject *object)
{
  AdSetObjectDetection *sample_filter = AD_SET_OBJECT_DETECTION(object);

  g_rec_mutex_clear(&sample_filter->priv->mutex);
}

static GstFlowReturn
ad_set_object_detection_transform_frame_ip(GstVideoFilter *filter,
                                      GstVideoFrame *frame)
{
  GstMapInfo info;

  gst_buffer_map(frame->buffer, &info, GST_MAP_READ);
  
  // Set object detection
  setObjectDetectionData(frame->buffer, filter->element.sinkpad);

  gst_buffer_unmap(frame->buffer, &info);
  return GST_FLOW_OK;
}

static void 
setObjectDetectionData(GstBuffer* buffer, GstPad *pad)
{
    auto *f_meta = gst_buffer_acquire_adroi_frame_meta(buffer, pad);
    if (f_meta == nullptr) 
    {
        GST_ERROR("Can not get adlink ROI frame metadata");
        return;
    }
    
    auto *b_meta = gst_buffer_acquire_adroi_batch_meta(buffer);
    if (b_meta == nullptr)
    {
        GST_ERROR("Can not acquire adlink ROI batch metadata");
        return;
    }
    
    auto qrs = f_meta->frame->query("//");
    if(qrs[0].rois.size() > 0)
    {
        std::vector<std::string> labels = {"water bottle", "camera", "chair", "person", "slipper"};
        srand( time(NULL) );
        int index = rand() % labels.size();
        
        float prob = (float)( rand() % 1000 )/1000;
        float x1 = (float)( rand() % 3 + 1 )/10;	// 0.1~0.3
        float x2 = (float)( rand() % 3 + 7 )/10;	// 0.7~0.9
        float y1 = (float)( rand() % 3 + 1 )/10;	// 0.1~0.3
        float y2 = (float)( rand() % 3 + 7 )/10;	// 0.7~0.9
        
        std::shared_ptr<ROI> obj_box = adroi_new_box("sample-engine", "", prob, x1, y1, x2, y2);
        obj_box->add_classification("sample-engine", "", prob, labels[index], index);
        qrs[0].rois[0]->add_roi(obj_box);
    }
}

// plugin registration
gboolean
ad_set_object_detection_plugin_init(GstPlugin *plugin)
{
  return gst_element_register(plugin, PLUGIN_NAME, GST_RANK_NONE,
                              AD_TYPE_SET_OBJECT_DETECTION);
}

#ifndef PACKAGE
#define PACKAGE "SAMPLE"
#endif
#ifndef PACKAGE_VERSION
#define PACKAGE_VERSION "1.0"
#endif
#ifndef GST_PACKAGE_NAME
#define GST_PACKAGE_NAME "Sample Package"
#endif
#ifndef GST_LICENSE
#define GST_LICENSE "LGPL"
#endif
#ifndef GST_PACKAGE_ORIGIN
#define GST_PACKAGE_ORIGIN "https://www.adlink.com"
#endif

GST_PLUGIN_DEFINE(
    GST_VERSION_MAJOR,
    GST_VERSION_MINOR,
    adsetobjectdetection,
    "ADLINK set object detection results from admetadata plugin",
    ad_set_object_detection_plugin_init,
    PACKAGE_VERSION,
    GST_LICENSE,
    GST_PACKAGE_NAME,
    GST_PACKAGE_ORIGIN)
