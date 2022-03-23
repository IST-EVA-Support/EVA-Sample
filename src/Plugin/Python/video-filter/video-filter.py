import cv2
import gst_cv_helper
# import ctypes
import numpy as np
#import gst_helper
#import gst_admeta as admeta
from gi.repository import Gst, GObject, GLib, GstVideo


def gst_video_caps_make(fmt):
  return  "video/x-raw, "\
    "format = (string) " + fmt + " , "\
    "width = " + GstVideo.VIDEO_SIZE_RANGE + ", "\
    "height = " + GstVideo.VIDEO_SIZE_RANGE + ", "\
    "framerate = " + GstVideo.VIDEO_FPS_RANGE
                                                                                                                       

class VideoFilter(Gst.Element):
    # MODIFIED - Gstreamer plugin name
    GST_PLUGIN_NAME = 'video_filter'

    __gstmetadata__ = ("Video Filter",
                       "GstElement",
                       "Python based GStreamer videofilter example",
                       "Dr. Paul Lin <paul.lin@adlinktech.com>")

    __gsttemplates__ = (Gst.PadTemplate.new("src",
                                            Gst.PadDirection.SRC,
                                            Gst.PadPresence.ALWAYS,
                                            Gst.Caps.from_string(gst_video_caps_make("{ BGR }"))),
                        Gst.PadTemplate.new("sink",
                                            Gst.PadDirection.SINK,
                                            Gst.PadPresence.ALWAYS,
                                            Gst.Caps.from_string(gst_video_caps_make("{ BGR }"))))

    _sinkpadtemplate = __gsttemplates__[1]
    _srcpadtemplate = __gsttemplates__[0]

    # MODIFIED - Gstreamer plugin properties
    __gproperties__ = {
      "type": (int,                         # type
               "Type",                      # nick
               "Filter type 0.Edge 1.Gray", # blurb
               0,                           # min
               1,                           # max
               0,                           # default
               GObject.ParamFlags.READWRITE # flags
              ),
      "edge-value": (int,                               # type
                     "Edge-Value",                      # nick
                     "Threshold value for edge image",  # blurb
                     0,                                 # min
                     255,                               # max
                     125,                               # default
                     GObject.ParamFlags.READWRITE       # flags
                    )
    }

    def __init__(self):
      # MODIFIED - Setting gstreamer plugin properties default value
      # Note - Initialize properties before Base Class initialization
      self.edge_value = 125
      self.filter_type = 0

      super(VideoFilter, self).__init__()

      self.sinkpad = Gst.Pad.new_from_template(self._sinkpadtemplate, 'sink')

      self.sinkpad.set_chain_function_full(self.chainfunc, None)

      self.sinkpad.set_chain_list_function_full(self.chainlistfunc, None)

      self.sinkpad.set_event_function_full(self.eventfunc, None)

      self.add_pad(self.sinkpad)
      

      self.srcpad = Gst.Pad.new_from_template(self._srcpadtemplate, 'src')

      self.add_pad(self.srcpad)


    def do_get_property(self, prop: GObject.GParamSpec):
      # MODIFIED - Gstreamer plugin properties getting
      if prop.name == 'type':
        return self.filter_type
      elif prop.name == 'edge-value':
        return self.edge_value
      else:
        raise AttributeError('unknown property %s' % prop.name)
    
    def do_set_property(self, prop: GObject.GParamSpec, value):
      # MODIFIED - Gstreamer plugin properties setting
      if prop.name == 'type':
        self.filter_type = int(value)
      elif prop.name == 'edge-value':
        self.edge_value = int(value)
      else:
        raise AttributeError('unknown property %s' % prop.name)
    
    def chainfunc(self, pad: Gst.Pad, parent, buff: Gst.Buffer) -> Gst.FlowReturn:
      # get image stream data
      img = gst_cv_helper.pad_and_buffer_to_numpy(pad, buff, ro=False)

      # do processing by filter type
      if self.filter_type == 0:
        result_img = np.int8(cv2.cvtColor(cv2.Canny(np.uint8(img), self.edge_value, 255), cv2.COLOR_GRAY2BGR))
      elif self.filter_type == 1:
        result_img = np.int8(cv2.cvtColor(cv2.cvtColor(np.uint8(img), cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR))
      
      # Copy back to referenced buffer
      img[:] = result_img[:]
      
      return self.srcpad.push(buff)
    
    def chainlistfunc(self, pad: Gst.Pad, parent, list: Gst.BufferList) -> Gst.FlowReturn:
      return self.srcpad.push(list.get(0))
    
    def eventfunc(self, pad: Gst.Pad, parent, event: Gst.Event) -> bool:
      return self.srcpad.push_event(event)



# Register plugin to use it from command line
GObject.type_register(VideoFilter)
__gstelementfactory__ = (VideoFilter.GST_PLUGIN_NAME,
                         Gst.Rank.NONE, VideoFilter)
