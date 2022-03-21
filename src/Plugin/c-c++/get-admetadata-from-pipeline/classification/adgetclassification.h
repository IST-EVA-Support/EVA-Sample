#ifndef __AD_GET_CLASSIFICATION_H__
#define __AD_GET_CLASSIFICATION_H__

#include <gst/gst.h>
#include <gst/video/gstvideofilter.h>

G_BEGIN_DECLS

#define AD_TYPE_GET_CLASSIFICATION \
  (ad_get_classification_get_type())
#define AD_GET_CLASSIFICATION(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST((obj), AD_TYPE_GET_CLASSIFICATION, AdGetClassification))
#define AD_GET_CLASSIFICATION_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST((klass), AD_TYPE_GET_CLASSIFICATION, AdGetClassificationClass))
#define AD_IS_GET_CLASSIFICATION(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE((obj), AD_TYPE_GET_CLASSIFICATION))
#define AD_IS_GET_CLASSIFICATION_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE((klass), AD_TYPE_GET_CLASSIFICATION))

typedef struct _AdGetClassification AdGetClassification;
typedef struct _AdGetClassificationClass AdGetClassificationClass;
typedef struct _AdGetClassificationPrivate AdGetClassificationPrivate;

struct _AdGetClassification
{
  GstVideoFilter base;
  AdGetClassificationPrivate *priv;
};

struct _AdGetClassificationClass
{
  GstVideoFilterClass base_ad_get_classification_class;
};

GType ad_get_classification_get_type(void);

gboolean ad_get_classification_plugin_init(GstPlugin *plugin);

G_END_DECLS

#endif /* __AD_GET_CLASSIFICATION_H__ */
