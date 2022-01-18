#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "adfiltertemplate.h"

#include <gst/gst.h>
#include <gst/video/video.h>
#include <gst/video/gstvideofilter.h>
#include <glib/gstdio.h>
#include <opencv2/opencv.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/highgui.hpp>

#define PLUGIN_NAME "adfiltertemplate"
#define DEFAULT_FILTER_TYPE 0
#define DEFAULT_EDGE_VALUE 125
#define GST_TYPE_SAMPLE_FILTER_TYPE 1

using namespace cv;

#define AD_FILTER_TEMPLATE_LOCK(sample_filter) \
  (g_rec_mutex_lock(&((AdFilterTemplate *)sample_filter)->priv->mutex))

#define AD_FILTER_TEMPLATE_UNLOCK(sample_filter) \
  (g_rec_mutex_unlock(&((AdFilterTemplate *)sample_filter)->priv->mutex))

GST_DEBUG_CATEGORY_STATIC(ad_filter_template_debug_category);
#define GST_CAT_DEFAULT ad_filter_template_debug_category

/*#define AD_FILTER_TEMPLATE_GET_PRIVATE(obj) ( \
    G_TYPE_INSTANCE_GET_PRIVATE(              \
        (obj),                                \
        AD_TYPE_FILTER_TEMPLATE,              \
        AdFilterTemplatePrivate))
*/
enum
{
  PROP_0,
  PROP_FILTER_TYPE,
  PROP_EDGE_VALUE,
  N_PROPERTIES
};

struct _AdFilterTemplatePrivate
{
  Mat *cv_image;
  int edge_value;
  int filter_type;
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
  GST_DEBUG_CATEGORY_INIT(GST_CAT_DEFAULT, PLUGIN_NAME, 0, "debug category for filter template element");

//G_DEFINE_TYPE_WITH_CODE(AdFilterTemplate, ad_filter_template, GST_TYPE_VIDEO_FILTER, DEBUG_INIT)
G_DEFINE_TYPE_WITH_CODE(AdFilterTemplate, ad_filter_template, GST_TYPE_VIDEO_FILTER,
                        G_ADD_PRIVATE(AdFilterTemplate)
                            DEBUG_INIT)

static void ad_filter_template_set_property(GObject *object, guint property_id, const GValue *value, GParamSpec *pspec);
static void ad_filter_template_get_property(GObject *object, guint property_id, GValue *value, GParamSpec *pspec);
static void ad_filter_template_dispose(GObject *object);
static void ad_filter_template_finalize(GObject *object);
static GstFlowReturn ad_filter_template_transform_frame_ip(GstVideoFilter *filter, GstVideoFrame *frame);
static void ad_filter_template_display_background(AdFilterTemplate *sample_filter, Mat &mask);
static void ad_filter_template_initialize_images(AdFilterTemplate *sample_filter, GstVideoFrame *frame, GstMapInfo &info);

static void
ad_filter_template_class_init(AdFilterTemplateClass *klass)
{
  GObjectClass *gobject_class;
  GstElementClass *gstelement_class;
  GstVideoFilterClass *gstvideofilter_class;

  gobject_class = (GObjectClass *)klass;
  gstvideofilter_class = (GstVideoFilterClass *)klass;
  gstelement_class = (GstElementClass *)klass;

  GST_DEBUG_CATEGORY_INIT(GST_CAT_DEFAULT, PLUGIN_NAME, 0, PLUGIN_NAME);

  gobject_class->set_property = ad_filter_template_set_property;
  gobject_class->get_property = ad_filter_template_get_property;
  gobject_class->dispose = ad_filter_template_dispose;
  gobject_class->finalize = ad_filter_template_finalize;

  g_object_class_install_property(gobject_class, PROP_FILTER_TYPE,
                                  g_param_spec_int("type", "Type",
                                                   "Filter type 1.Edge 2.Gray", 0, 1,
                                                   DEFAULT_FILTER_TYPE, (GParamFlags)G_PARAM_READWRITE));

  g_object_class_install_property(gobject_class, PROP_EDGE_VALUE,
                                  g_param_spec_int("edge-value", "edge value",
                                                   "Threshold value for edge image", 0, 255,
                                                   DEFAULT_EDGE_VALUE, (GParamFlags)G_PARAM_READWRITE));

  gst_element_class_set_static_metadata(gstelement_class,
                                        "filter template element", "Video/Filter",
                                        "Example of filter with OpenCV operations",
                                        "Steven.Tu <steven.tu@adlinktech.com>");

  gst_element_class_add_pad_template(gstelement_class,
                                     gst_static_pad_template_get(&src_factory));
  gst_element_class_add_pad_template(gstelement_class,
                                     gst_static_pad_template_get(&sink_factory));

  gstvideofilter_class->transform_frame_ip =
      GST_DEBUG_FUNCPTR(ad_filter_template_transform_frame_ip);

  //g_type_class_add_private(klass, sizeof(AdFilterTemplatePrivate));
}

static void
ad_filter_template_init(AdFilterTemplate *
                            sample_filter)
{
  sample_filter->priv = (AdFilterTemplatePrivate *)ad_filter_template_get_instance_private(sample_filter);
  //sample_filter->priv = AD_FILTER_TEMPLATE_GET_PRIVATE(sample_filter);
  sample_filter->priv->edge_value = 125;
  g_rec_mutex_init(&sample_filter->priv->mutex);
}

static void
ad_filter_template_set_property(GObject *object, guint property_id,
                                const GValue *value, GParamSpec *pspec)
{
  AdFilterTemplate *sample_filter = AD_FILTER_TEMPLATE(object);

  AD_FILTER_TEMPLATE_LOCK(sample_filter);

  switch (property_id)
  {
  case PROP_FILTER_TYPE:
    sample_filter->priv->filter_type = g_value_get_int(value);
    break;

  case PROP_EDGE_VALUE:
    sample_filter->priv->edge_value = g_value_get_int(value);
    break;

  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID(object, property_id, pspec);
    break;
  }

  AD_FILTER_TEMPLATE_UNLOCK(sample_filter);
}

static void
ad_filter_template_get_property(GObject *object, guint property_id,
                                GValue *value, GParamSpec *pspec)
{
  AdFilterTemplate *sample_filter = AD_FILTER_TEMPLATE(object);

  AD_FILTER_TEMPLATE_LOCK(sample_filter);

  switch (property_id)
  {
  case PROP_FILTER_TYPE:
    g_value_set_int(value, sample_filter->priv->filter_type);
    break;

  case PROP_EDGE_VALUE:
    g_value_set_int(value, sample_filter->priv->edge_value);
    break;

  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID(object, property_id, pspec);
    break;
  }

  AD_FILTER_TEMPLATE_UNLOCK(sample_filter);
}

static void
ad_filter_template_dispose(GObject *object)
{
  /* In dispose(), you are supposed to free all types referenced from this
   * object which might themselves hold a reference to self. Generally,
   * the most simple solution is to unref all members on which you own a 
   * reference.
   */

  /* dispose() might be called multiple times, so we must guard against
   * calling g_object_unref() on an invalid GObject by setting the member
   * NULL; g_clear_object() does this for us.
   */
}

static void
ad_filter_template_finalize(GObject *object)
{
  AdFilterTemplate *sample_filter = AD_FILTER_TEMPLATE(object);

  if (sample_filter->priv->cv_image != NULL)
  {
    delete sample_filter->priv->cv_image;
  }

  g_rec_mutex_clear(&sample_filter->priv->mutex);
}

static GstFlowReturn
ad_filter_template_transform_frame_ip(GstVideoFilter *filter,
                                      GstVideoFrame *frame)
{
  AdFilterTemplate *sample_filter = AD_FILTER_TEMPLATE(filter);
  GstMapInfo info;
  Mat output_image;
  int filter_type;
  int edge_threshold;

  gst_buffer_map(frame->buffer, &info, GST_MAP_READ);

  ad_filter_template_initialize_images(sample_filter, frame, info);

  AD_FILTER_TEMPLATE_LOCK(sample_filter);
  filter_type = sample_filter->priv->filter_type;
  edge_threshold = sample_filter->priv->edge_value;
  AD_FILTER_TEMPLATE_UNLOCK(sample_filter);

  if (filter_type == 0)
  {
    GST_DEBUG("Calculating edges");
    Canny((*sample_filter->priv->cv_image), output_image,
          edge_threshold, 255);
  }
  else if (filter_type == 1)
  {
    GST_DEBUG("Calculating black&white image");
    //cvtColor((*sample_filter->priv->cv_image), output_image, COLOR_YUV2BGR_I420);
    cvtColor((*sample_filter->priv->cv_image), output_image, COLOR_BGR2GRAY);
  }

  if (output_image.data != NULL)
  {
    GST_DEBUG("Updating output image");
    ad_filter_template_display_background(sample_filter, output_image);
  }

  gst_buffer_unmap(frame->buffer, &info);
  return GST_FLOW_OK;
}

static void
ad_filter_template_display_background(AdFilterTemplate *sample_filter, Mat &mask)
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
ad_filter_template_initialize_images(AdFilterTemplate *sample_filter,
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
ad_filter_template_plugin_init(GstPlugin *plugin)
{
  return gst_element_register(plugin, PLUGIN_NAME, GST_RANK_NONE,
                              AD_TYPE_FILTER_TEMPLATE);
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
    adfiltertemplate,
    "ADLINK filter template plugin",
    ad_filter_template_plugin_init,
    PACKAGE_VERSION,
    GST_LICENSE,
    GST_PACKAGE_NAME,
    GST_PACKAGE_ORIGIN)
