#ifndef __AD_GET_STREAM_DATA_H__
#define __AD_GET_STREAM_DATA_H__

#include <gst/gst.h>
#include <gst/video/gstvideofilter.h>

G_BEGIN_DECLS

#define AD_TYPE_GET_STREAM_DATA \
  (ad_get_stream_data_get_type())
#define AD_GET_STREAM_DATA(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST((obj), AD_TYPE_GET_STREAM_DATA, AdGetStreamData))
#define AD_GET_STREAM_DATA_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST((klass), AD_TYPE_GET_STREAM_DATA, AdGetStreamDataClass))
#define AD_IS_GET_STREAM_DATA(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE((obj), AD_TYPE_GET_STREAM_DATA))
#define AD_IS_GET_STREAM_DATA_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE((klass), AD_TYPE_GET_STREAM_DATA))

typedef struct _AdGetStreamData AdGetStreamData;
typedef struct _AdGetStreamDataClass AdGetStreamDataClass;
typedef struct _AdGetStreamDataPrivate AdGetStreamDataPrivate;

struct _AdGetStreamData
{
  GstVideoFilter base;
  AdGetStreamDataPrivate *priv;
};

struct _AdGetStreamDataClass
{
  GstVideoFilterClass base_ad_get_stream_data_class;
};

GType ad_get_stream_data_get_type(void);

gboolean ad_get_stream_data_plugin_init(GstPlugin *plugin);

G_END_DECLS

#endif /* __AD_GET_STREAM_DATA_H__ */
