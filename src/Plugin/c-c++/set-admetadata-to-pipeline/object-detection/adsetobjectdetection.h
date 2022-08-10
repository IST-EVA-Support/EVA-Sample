#ifndef __AD_SET_OBJECT_DETECTION_H__
#define __AD_SET_OBJECT_DETECTION_H__

#include <gst/gst.h>
#include <gst/video/gstvideofilter.h>

G_BEGIN_DECLS

#define AD_TYPE_SET_OBJECT_DETECTION \
  (ad_set_object_detection_get_type())
#define AD_SET_OBJECT_DETECTION(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST((obj), AD_TYPE_SET_OBJECT_DETECTION, AdSetObjectDetection))
#define AD_SET_OBJECT_DETECTION_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST((klass), AD_TYPE_SET_OBJECT_DETECTION, AdSetObjectDetectionClass))
#define AD_IS_SET_OBJECT_DETECTION(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE((obj), AD_TYPE_SET_OBJECT_DETECTION))
#define AD_IS_SET_OBJECT_DETECTION_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE((klass), AD_TYPE_SET_OBJECT_DETECTION))

typedef struct _AdSetObjectDetection AdSetObjectDetection;
typedef struct _AdSetObjectDetectionClass AdSetObjectDetectionClass;
typedef struct _AdSetObjectDetectionPrivate AdSetObjectDetectionPrivate;

struct _AdSetObjectDetection
{
  GstVideoFilter base;
  AdSetObjectDetectionPrivate *priv;
};

struct _AdSetObjectDetectionClass
{
  GstVideoFilterClass base_ad_set_object_detection_class;
};

GType ad_set_object_detection_get_type(void);

gboolean ad_set_object_detection_plugin_init(GstPlugin *plugin);

G_END_DECLS

#endif /* __AD_SET_OBJECT_DETECTION_H__ */
