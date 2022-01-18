#ifndef __AD_FILTER_TEMPLATE_H__
#define __AD_FILTER_TEMPLATE_H__

#include <gst/gst.h>
#include <gst/video/gstvideofilter.h>

G_BEGIN_DECLS

#define AD_TYPE_FILTER_TEMPLATE \
  (ad_filter_template_get_type())
#define AD_FILTER_TEMPLATE(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST((obj), AD_TYPE_FILTER_TEMPLATE, AdFilterTemplate))
#define AD_FILTER_TEMPLATE_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST((klass), AD_TYPE_FILTER_TEMPLATE, AdFilterTemplateClass))
#define AD_IS_FILTER_TEMPLATE(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE((obj), AD_TYPE_FILTER_TEMPLATE))
#define AD_IS_FILTER_TEMPLATE_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE((klass), AD_TYPE_FILTER_TEMPLATE))

typedef struct _AdFilterTemplate AdFilterTemplate;
typedef struct _AdFilterTemplateClass AdFilterTemplateClass;
typedef struct _AdFilterTemplatePrivate AdFilterTemplatePrivate;

struct _AdFilterTemplate
{
  GstVideoFilter base;
  AdFilterTemplatePrivate *priv;
};

struct _AdFilterTemplateClass
{
  GstVideoFilterClass base_ad_filter_template_class;
};

GType ad_filter_template_get_type(void);

gboolean ad_filter_template_plugin_init(GstPlugin *plugin);

G_END_DECLS

#endif /* __AD_FILTER_TEMPLATE_H__ */
