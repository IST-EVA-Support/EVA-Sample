#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "adgetstreamdata.h"

#include <gst/gst.h>
#include <gst/video/video.h>
#include <gst/video/gstvideofilter.h>
#include <glib/gstdio.h>
#include <opencv2/opencv.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/highgui.hpp>

#define PLUGIN_NAME "adgetstreamdata"

using namespace cv;

#define AD_GET_STREAM_DATA_LOCK(sample_filter) \
  (g_rec_mutex_lock(&((AdGetStreamData *)sample_filter)->priv->mutex))

#define AD_GET_STREAM_DATA_UNLOCK(sample_filter) \
  (g_rec_mutex_unlock(&((AdGetStreamData *)sample_filter)->priv->mutex))

GST_DEBUG_CATEGORY_STATIC(ad_get_stream_data_debug_category);
#define GST_CAT_DEFAULT ad_get_stream_data_debug_category

enum
{
  PROP_0
};

struct _AdGetStreamDataPrivate
{
  Mat *cv_image;
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
  GST_DEBUG_CATEGORY_INIT(GST_CAT_DEFAULT, PLUGIN_NAME, 0, "debug category for get stream data element");

G_DEFINE_TYPE_WITH_CODE(AdGetStreamData, ad_get_stream_data, GST_TYPE_VIDEO_FILTER,
                        G_ADD_PRIVATE(AdGetStreamData)
                            DEBUG_INIT)

static void ad_get_stream_data_set_property(GObject *object, guint property_id, const GValue *value, GParamSpec *pspec);
static void ad_get_stream_data_get_property(GObject *object, guint property_id, GValue *value, GParamSpec *pspec);
static void ad_get_stream_data_dispose(GObject *object);
static void ad_get_stream_data_finalize(GObject *object);
static GstFlowReturn ad_get_stream_data_transform_frame_ip(GstVideoFilter *filter, GstVideoFrame *frame);
static void ad_get_stream_data_replace_stream_back(AdGetStreamData *sample_filter, Mat &mask);
static void ad_get_stream_data_initialize_images(AdGetStreamData *sample_filter, GstVideoFrame *frame, GstMapInfo &info);

static void
ad_get_stream_data_class_init(AdGetStreamDataClass *klass)
{
  GObjectClass *gobject_class;
  GstElementClass *gstelement_class;
  GstVideoFilterClass *gstvideofilter_class;

  gobject_class = (GObjectClass *)klass;
  gstvideofilter_class = (GstVideoFilterClass *)klass;
  gstelement_class = (GstElementClass *)klass;

  GST_DEBUG_CATEGORY_INIT(GST_CAT_DEFAULT, PLUGIN_NAME, 0, PLUGIN_NAME);

  gobject_class->set_property = ad_get_stream_data_set_property;
  gobject_class->get_property = ad_get_stream_data_get_property;
  gobject_class->dispose = ad_get_stream_data_dispose;
  gobject_class->finalize = ad_get_stream_data_finalize;

  gst_element_class_set_static_metadata(gstelement_class,
                                        "Get stream data element example", "Video/Filter",
                                        "Example of get stream data with OpenCV operations",
                                        "Dr. Paul Lin <paul.lin@adlinktech.com>");

  gst_element_class_add_pad_template(gstelement_class,
                                     gst_static_pad_template_get(&src_factory));
  gst_element_class_add_pad_template(gstelement_class,
                                     gst_static_pad_template_get(&sink_factory));

  gstvideofilter_class->transform_frame_ip =
      GST_DEBUG_FUNCPTR(ad_get_stream_data_transform_frame_ip);
}

static void
ad_get_stream_data_init(AdGetStreamData *
                            sample_filter)
{
  sample_filter->priv = (AdGetStreamDataPrivate *)ad_get_stream_data_get_instance_private(sample_filter);

  g_rec_mutex_init(&sample_filter->priv->mutex);
}

static void
ad_get_stream_data_set_property(GObject *object, guint property_id,
                                const GValue *value, GParamSpec *pspec)
{
  AdGetStreamData *sample_filter = AD_GET_STREAM_DATA(object);

  AD_GET_STREAM_DATA_LOCK(sample_filter);

  switch (property_id)
  {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID(object, property_id, pspec);
    break;
  }

  AD_GET_STREAM_DATA_UNLOCK(sample_filter);
}

static void
ad_get_stream_data_get_property(GObject *object, guint property_id,
                                GValue *value, GParamSpec *pspec)
{
  AdGetStreamData *sample_filter = AD_GET_STREAM_DATA(object);

  AD_GET_STREAM_DATA_LOCK(sample_filter);

  switch (property_id)
  {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID(object, property_id, pspec);
    break;
  }

  AD_GET_STREAM_DATA_UNLOCK(sample_filter);
}

static void
ad_get_stream_data_dispose(GObject *object)
{
}

static void
ad_get_stream_data_finalize(GObject *object)
{
  AdGetStreamData *sample_filter = AD_GET_STREAM_DATA(object);

  if (sample_filter->priv->cv_image != NULL)
  {
    delete sample_filter->priv->cv_image;
  }

  g_rec_mutex_clear(&sample_filter->priv->mutex);
}

static GstFlowReturn
ad_get_stream_data_transform_frame_ip(GstVideoFilter *filter,
                                      GstVideoFrame *frame)
{
  AdGetStreamData *sample_filter = AD_GET_STREAM_DATA(filter);
  GstMapInfo info;
  Mat output_image;

  gst_buffer_map(frame->buffer, &info, GST_MAP_READ);

  // Reference stream data tp cv::Mat
  ad_get_stream_data_initialize_images(sample_filter, frame, info);

  // After getting the stream data(image data), do the process you want. Here just simply assume doing text overlay by opencv.
  int x = (frame->info.width * 0.1);
  int y = (frame->info.width * 0.3);
  float size = frame->info.width / 640.0;
  putText((*sample_filter->priv->cv_image), "Do your algorithm or processing here.", Point(x, y), FONT_HERSHEY_SCRIPT_SIMPLEX, size, Scalar(32, 255, 64), 1.25, LINE_AA);

  // Peplace the reference stream data by result
  if (output_image.data != NULL)
    ad_get_stream_data_replace_stream_back(sample_filter, output_image);

  gst_buffer_unmap(frame->buffer, &info);
  return GST_FLOW_OK;
}

static void
ad_get_stream_data_replace_stream_back(AdGetStreamData *sample_filter, Mat &mask)
{
  int i, j;
  uchar *img_ptr, *mask_ptr;
  int n_rows_img = sample_filter->priv->cv_image->rows;
  int n_cols_img = sample_filter->priv->cv_image->cols;

  for (i = 0; i < n_rows_img; ++i)
  {
    img_ptr = sample_filter->priv->cv_image->ptr<uchar>(i);
    mask_ptr = mask.ptr<uchar>(i);

    for (j = 0; j < n_cols_img; ++j)
    {
      img_ptr[j * sample_filter->priv->cv_image->channels()] = mask_ptr[j];
      img_ptr[j * sample_filter->priv->cv_image->channels() + 1] = mask_ptr[j];
      img_ptr[j * sample_filter->priv->cv_image->channels() + 2] = mask_ptr[j];
    }
  }

  return;
}

static void
ad_get_stream_data_initialize_images(AdGetStreamData *sample_filter,
                                     GstVideoFrame *frame, GstMapInfo &info)
{
  if (sample_filter->priv->cv_image == NULL)
  {
    sample_filter->priv->cv_image = new Mat(frame->info.height,
                                            frame->info.width, CV_8UC3, info.data);
  }
  else if ((sample_filter->priv->cv_image->cols != frame->info.width) || (sample_filter->priv->cv_image->rows != frame->info.height))
  {
    delete sample_filter->priv->cv_image;
    sample_filter->priv->cv_image = new Mat(frame->info.height, frame->info.width,
                                            CV_8UC3, info.data);
  }
  else
  {
    sample_filter->priv->cv_image->data = info.data;
  }
}

gboolean
ad_get_stream_data_plugin_init(GstPlugin *plugin)
{
  return gst_element_register(plugin, PLUGIN_NAME, GST_RANK_NONE,
                              AD_TYPE_GET_STREAM_DATA);
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
    adgetstreamdata,
    "ADLINK get stream data plugin",
    ad_get_stream_data_plugin_init,
    PACKAGE_VERSION,
    GST_LICENSE,
    GST_PACKAGE_NAME,
    GST_PACKAGE_ORIGIN)
