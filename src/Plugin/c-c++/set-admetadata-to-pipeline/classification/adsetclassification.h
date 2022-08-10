#ifndef __AD_SET_CLASSIFICATION_H__
#define __AD_SET_CLASSIFICATION_H__

#include <gst/gst.h>
#include <gst/video/gstvideofilter.h>

G_BEGIN_DECLS

#define AD_TYPE_SET_CLASSIFICATION \
  (ad_set_classification_get_type())
#define AD_SET_CLASSIFICATION(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST((obj), AD_TYPE_SET_CLASSIFICATION, AdSetClassification))
#define AD_SET_CLASSIFICATION_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST((klass), AD_TYPE_SET_CLASSIFICATION, AdSetClassificationClass))
#define AD_IS_SET_CLASSIFICATION(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE((obj), AD_TYPE_SET_CLASSIFICATION))
#define AD_IS_SET_CLASSIFICATION_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE((klass), AD_TYPE_SET_CLASSIFICATION))

typedef struct _AdSetClassification AdSetClassification;
typedef struct _AdSetClassificationClass AdSetClassificationClass;
typedef struct _AdSetClassificationPrivate AdSetClassificationPrivate;

struct _AdSetClassification
{
  GstVideoFilter base;
  AdSetClassificationPrivate *priv;
};

struct _AdSetClassificationClass
{
  GstVideoFilterClass base_ad_set_classification_class;
};

GType ad_set_classification_get_type(void);

gboolean ad_set_classification_plugin_init(GstPlugin *plugin);

G_END_DECLS

#endif /* __AD_SET_CLASSIFICATION_H__ */
