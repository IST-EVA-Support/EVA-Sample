#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "adgetobjectdetection.h"

#include <gst/gst.h>
#include <gst/video/video.h>
#include <gst/video/gstvideofilter.h>
#include <glib/gstdio.h>

#include <iostream>
#include "gstadmeta.h" // include gstadmeta.h for retrieving the inference results

#define PLUGIN_NAME "adgetobjectdetection"

#define AD_GET_OBJECT_DETECTION_LOCK(sample_filter) \
  (g_rec_mutex_lock(&((AdGetObjectDetection *)sample_filter)->priv->mutex))

#define AD_GET_OBJECT_DETECTION_UNLOCK(sample_filter) \
  (g_rec_mutex_unlock(&((AdGetObjectDetection *)sample_filter)->priv->mutex))

GST_DEBUG_CATEGORY_STATIC(ad_get_object_detection_debug_category);
#define GST_CAT_DEFAULT ad_get_object_detection_debug_category

enum
{
  PROP_0
};

struct _AdGetObjectDetectionPrivate
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
  GST_DEBUG_CATEGORY_INIT(GST_CAT_DEFAULT, PLUGIN_NAME, 0, "debug category for get object detection element");

G_DEFINE_TYPE_WITH_CODE(AdGetObjectDetection, ad_get_object_detection, GST_TYPE_VIDEO_FILTER,
                        G_ADD_PRIVATE(AdGetObjectDetection)
                            DEBUG_INIT)

// ************************************************************
// Required to add this gst_buffer_get_ad_batch_meta for retrieving 
// the GstAdBatchMeta from buffer
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
// ************************************************************

static void ad_get_object_detection_set_property(GObject *object, guint property_id, const GValue *value, GParamSpec *pspec);
static void ad_get_object_detection_get_property(GObject *object, guint property_id, GValue *value, GParamSpec *pspec);
static void ad_get_object_detection_dispose(GObject *object);
static void ad_get_object_detection_finalize(GObject *object);
static GstFlowReturn ad_get_object_detection_transform_frame_ip(GstVideoFilter *filter, GstVideoFrame *frame);
static void getObjectDetectionData(GstBuffer* buffer);

static void
ad_get_object_detection_class_init(AdGetObjectDetectionClass *klass)
{
  GObjectClass *gobject_class;
  GstElementClass *gstelement_class;
  GstVideoFilterClass *gstvideofilter_class;

  gobject_class = (GObjectClass *)klass;
  gstvideofilter_class = (GstVideoFilterClass *)klass;
  gstelement_class = (GstElementClass *)klass;

  GST_DEBUG_CATEGORY_INIT(GST_CAT_DEFAULT, PLUGIN_NAME, 0, PLUGIN_NAME);

  gobject_class->set_property = ad_get_object_detection_set_property;
  gobject_class->get_property = ad_get_object_detection_get_property;
  gobject_class->dispose = ad_get_object_detection_dispose;
  gobject_class->finalize = ad_get_object_detection_finalize;

  gst_element_class_set_static_metadata(gstelement_class,
                                        "Get object detection result from admetadata element example", "Video/Filter",
                                        "Example of get object detection result from admetadata",
                                        "Dr. Paul Lin <paul.lin@adlinktech.com>");

  gst_element_class_add_pad_template(gstelement_class,
                                     gst_static_pad_template_get(&src_factory));
  gst_element_class_add_pad_template(gstelement_class,
                                     gst_static_pad_template_get(&sink_factory));

  gstvideofilter_class->transform_frame_ip =
      GST_DEBUG_FUNCPTR(ad_get_object_detection_transform_frame_ip);
}

static void
ad_get_object_detection_init(AdGetObjectDetection *
                            sample_filter)
{
  sample_filter->priv = (AdGetObjectDetectionPrivate *)ad_get_object_detection_get_instance_private(sample_filter);

  g_rec_mutex_init(&sample_filter->priv->mutex);
}

static void
ad_get_object_detection_set_property(GObject *object, guint property_id,
                                const GValue *value, GParamSpec *pspec)
{
  AdGetObjectDetection *sample_filter = AD_GET_OBJECT_DETECTION(object);

  AD_GET_OBJECT_DETECTION_LOCK(sample_filter);

  switch (property_id)
  {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID(object, property_id, pspec);
    break;
  }

  AD_GET_OBJECT_DETECTION_UNLOCK(sample_filter);
}

static void
ad_get_object_detection_get_property(GObject *object, guint property_id,
                                GValue *value, GParamSpec *pspec)
{
  AdGetObjectDetection *sample_filter = AD_GET_OBJECT_DETECTION(object);

  AD_GET_OBJECT_DETECTION_LOCK(sample_filter);

  switch (property_id)
  {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID(object, property_id, pspec);
    break;
  }

  AD_GET_OBJECT_DETECTION_UNLOCK(sample_filter);
}

static void
ad_get_object_detection_dispose(GObject *object)
{
}

static void
ad_get_object_detection_finalize(GObject *object)
{
  AdGetObjectDetection *sample_filter = AD_GET_OBJECT_DETECTION(object);

  g_rec_mutex_clear(&sample_filter->priv->mutex);
}

static GstFlowReturn
ad_get_object_detection_transform_frame_ip(GstVideoFilter *filter,
                                      GstVideoFrame *frame)
{
  GstMapInfo info;

  gst_buffer_map(frame->buffer, &info, GST_MAP_READ);
  
  // Get object detection from admetadata
  getObjectDetectionData(frame->buffer);

  gst_buffer_unmap(frame->buffer, &info);
  return GST_FLOW_OK;
}

static void 
getObjectDetectionData(GstBuffer* buffer)
{
    GstAdBatchMeta *meta = gst_buffer_get_ad_batch_meta(buffer);
    if (meta == NULL)
        GST_MESSAGE("Adlink metadata is not exist!");
    else
    {
        AdBatch &batch = meta->batch;
        bool frame_exist = batch.frames.size() > 0 ? true : false;
        if(frame_exist)
        {
            VideoFrameData frame_info = batch.frames[0];
            int detectionResultNumber = frame_info.detection_results.size();
            std::cout << "detection result number = " << detectionResultNumber << std::endl;
            for(int i = 0 ; i < detectionResultNumber ; ++i)
            {
                std::cout << "========== metadata in application ==========\n";
                std::cout << "Class = " << frame_info.detection_results[i].obj_id << std::endl;
                std::cout << "Label = " << frame_info.detection_results[i].obj_label << std::endl;
                std::cout << "Prob =  " << frame_info.detection_results[i].prob << std::endl;
                std::cout << "(x1, y1, x2, y2) = (" 
                << frame_info.detection_results[i].x1 << ", " 
                << frame_info.detection_results[i].y1 << ", "
                << frame_info.detection_results[i].x2 << ", " 
                << frame_info.detection_results[i].y2 << ")" << std::endl;
                std::cout << "=============================================\n";
            }
        }
    }
}

gboolean
ad_get_object_detection_plugin_init(GstPlugin *plugin)
{
  return gst_element_register(plugin, PLUGIN_NAME, GST_RANK_NONE,
                              AD_TYPE_GET_OBJECT_DETECTION);
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
    adgetobjectdetection,
    "ADLINK get object detection results from admetadata plugin",
    ad_get_object_detection_plugin_init,
    PACKAGE_VERSION,
    GST_LICENSE,
    GST_PACKAGE_NAME,
    GST_PACKAGE_ORIGIN)
