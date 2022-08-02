//**
//   gst-launch-1.0 videotestsrc ! video/x-raw, width=640, height=480 ! adsetclassification ! admetadrawer ! videoconvert ! ximagesink
//**

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "adsetclassification.h"

#include <gst/gst.h>
#include <gst/video/video.h>
#include <gst/video/gstvideofilter.h>
#include <glib/gstdio.h>

#include <iostream>
#include <vector>
#include <string>
#include <stdlib.h> // include random value function
#include <time.h>   // include time
#include "gstadmeta.h" // include gstadmeta.h for retrieving the inference results

#define PLUGIN_NAME "adsetclassification"

#define AD_SET_CLASSIFICATION_LOCK(sample_filter) \
  (g_rec_mutex_lock(&((AdSetClassification *)sample_filter)->priv->mutex))

#define AD_SET_CLASSIFICATION_UNLOCK(sample_filter) \
  (g_rec_mutex_unlock(&((AdSetClassification *)sample_filter)->priv->mutex))

GST_DEBUG_CATEGORY_STATIC(ad_set_classification_debug_category);
#define GST_CAT_DEFAULT ad_set_classification_debug_category

enum
{
  PROP_0
};

struct _AdSetClassificationPrivate
{
  GRecMutex mutex;
};

// pad definition
static GstStaticPadTemplate sink_factory = GST_STATIC_PAD_TEMPLATE("sink",
                                                                   GST_PAD_SINK,
                                                                   GST_PAD_ALWAYS,
                                                                   GST_STATIC_CAPS(GST_VIDEO_CAPS_MAKE("{ BGR }")));

static GstStaticPadTemplate src_factory = GST_STATIC_PAD_TEMPLATE("src",
                                                                  GST_PAD_SRC,
                                                                  GST_PAD_ALWAYS,
                                                                  GST_STATIC_CAPS(GST_VIDEO_CAPS_MAKE("{ BGR }")));

#define DEBUG_INIT \
  GST_DEBUG_CATEGORY_INIT(GST_CAT_DEFAULT, PLUGIN_NAME, 0, "debug category for set classification element");

G_DEFINE_TYPE_WITH_CODE(AdSetClassification, ad_set_classification, GST_TYPE_VIDEO_FILTER,
                        G_ADD_PRIVATE(AdSetClassification)
                            DEBUG_INIT)

static void ad_set_classification_set_property(GObject *object, guint property_id, const GValue *value, GParamSpec *pspec);
static void ad_set_classification_get_property(GObject *object, guint property_id, GValue *value, GParamSpec *pspec);
static void ad_set_classification_dispose(GObject *object);
static void ad_set_classification_finalize(GObject *object);
static GstFlowReturn ad_set_classification_transform_frame_ip(GstVideoFilter *filter, GstVideoFrame *frame);
static void setClassificationData(GstBuffer* buffer);

static void     // initialize metadata
ad_set_classification_class_init(AdSetClassificationClass *klass)
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
  gobject_class->set_property = ad_set_classification_set_property;
  gobject_class->get_property = ad_set_classification_get_property;
  gobject_class->dispose = ad_set_classification_dispose;
  gobject_class->finalize = ad_set_classification_finalize;

  gst_element_class_set_static_metadata(gstelement_class,
                                        "Set classification result to admetadata element example", "Video/Filter",
                                        "Example of setting classification result",
                                        "Jessie Huang <yun-chieh.huang@adlinktech.com>");

  // adding a pad
  gst_element_class_add_pad_template(gstelement_class,
                                     gst_static_pad_template_get(&src_factory));
  gst_element_class_add_pad_template(gstelement_class,
                                     gst_static_pad_template_get(&sink_factory));

  gstvideofilter_class->transform_frame_ip =
      GST_DEBUG_FUNCPTR(ad_set_classification_transform_frame_ip);
}

static void     // initialize instance
ad_set_classification_init(AdSetClassification *
                            sample_filter)
{
  sample_filter->priv = (AdSetClassificationPrivate *)ad_set_classification_get_instance_private(sample_filter);

  g_rec_mutex_init(&sample_filter->priv->mutex);
}

static void
ad_set_classification_set_property(GObject *object, guint property_id,
                                const GValue *value, GParamSpec *pspec)
{
  AdSetClassification *sample_filter = AD_SET_CLASSIFICATION(object);

  AD_SET_CLASSIFICATION_LOCK(sample_filter);

  switch (property_id)
  {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID(object, property_id, pspec);
    break;
  }

  AD_SET_CLASSIFICATION_UNLOCK(sample_filter);
}

static void
ad_set_classification_get_property(GObject *object, guint property_id,
                                GValue *value, GParamSpec *pspec)
{
  AdSetClassification *sample_filter = AD_SET_CLASSIFICATION(object);

  AD_SET_CLASSIFICATION_LOCK(sample_filter);

  switch (property_id)
  {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID(object, property_id, pspec);
    break;
  }

  AD_SET_CLASSIFICATION_UNLOCK(sample_filter);
}

static void
ad_set_classification_dispose(GObject *object)
{
}

static void
ad_set_classification_finalize(GObject *object)
{
  AdSetClassification *sample_filter = AD_SET_CLASSIFICATION(object);

  g_rec_mutex_clear(&sample_filter->priv->mutex);
}

static GstFlowReturn
ad_set_classification_transform_frame_ip(GstVideoFilter *filter,
                                      GstVideoFrame *frame)
{
  GstMapInfo info;

  gst_buffer_map(frame->buffer, &info, GST_MAP_READ);
  
  // Set classification
  setClassificationData(frame->buffer);

  gst_buffer_unmap(frame->buffer, &info);
  return GST_FLOW_OK;
}

static void 
setClassificationData(GstBuffer* buffer)
{
    gpointer state = NULL;
    GstAdBatchMeta* meta;
    const GstMetaInfo* info = GST_AD_BATCH_META_INFO;
    meta = (GstAdBatchMeta *)gst_buffer_add_meta(buffer, info, &state);
        
    bool frame_exist = meta->batch.frames.size() > 0 ? true : false;
    if(!frame_exist)
    {
        VideoFrameData frame_info;
	std::vector<std::string> labels = {"water bottle", "camera", "chair", "person", "slipper", "mouse", "Triceratops", "woodpecker"};
	srand( time(NULL) );
		
	// Create random labels
	adlink::ai::ClassificationResult classification;
	classification.index = (rand() % labels.size());
	classification.output = "";
	classification.label = labels[classification.index];
	classification.prob = (double)classification.index / labels.size();

        frame_info.stream_id = " ";
	frame_info.width = 640;
        frame_info.height = 480;
        frame_info.depth = 0;
        frame_info.channels = 3;
        frame_info.device_idx = 0;
        frame_info.class_results.push_back(classification);
	meta->batch.frames.push_back(frame_info);
    }
}

// plugin registration
gboolean      
ad_set_classification_plugin_init(GstPlugin *plugin)
{
  return gst_element_register(plugin, PLUGIN_NAME, GST_RANK_NONE,
                              AD_TYPE_SET_CLASSIFICATION);
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
    adsetclassification,
    "ADLINK set classification results from admetadata plugin",
    ad_set_classification_plugin_init,
    PACKAGE_VERSION,
    GST_LICENSE,
    GST_PACKAGE_NAME,
    GST_PACKAGE_ORIGIN)
