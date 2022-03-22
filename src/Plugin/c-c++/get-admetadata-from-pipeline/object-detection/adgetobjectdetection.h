#ifndef __AD_GET_OBJECT_DETECTION_H__
#define __AD_GET_OBJECT_DETECTION_H__

#include <gst/gst.h>
#include <gst/video/gstvideofilter.h>

G_BEGIN_DECLS

#define AD_TYPE_GET_OBJECT_DETECTION \
  (ad_get_object_detection_get_type())
#define AD_GET_OBJECT_DETECTION(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST((obj), AD_TYPE_GET_OBJECT_DETECTION, AdGetObjectDetection))
#define AD_GET_OBJECT_DETECTION_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST((klass), AD_TYPE_GET_OBJECT_DETECTION, AdGetObjectDetectionClass))
#define AD_IS_GET_OBJECT_DETECTION(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE((obj), AD_TYPE_GET_OBJECT_DETECTION))
#define AD_IS_GET_OBJECT_DETECTION_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE((klass), AD_TYPE_GET_OBJECT_DETECTION))

typedef struct _AdGetObjectDetection AdGetObjectDetection;
typedef struct _AdGetObjectDetectionClass AdGetObjectDetectionClass;
typedef struct _AdGetObjectDetectionPrivate AdGetObjectDetectionPrivate;

struct _AdGetObjectDetection
{
  GstVideoFilter base;
  AdGetObjectDetectionPrivate *priv;
};

struct _AdGetObjectDetectionClass
{
  GstVideoFilterClass base_ad_get_object_detection_class;
};

GType ad_get_object_detection_get_type(void);

gboolean ad_get_object_detection_plugin_init(GstPlugin *plugin);

G_END_DECLS

#endif /* __AD_GET_OBJECT_DETECTION_H__ */
