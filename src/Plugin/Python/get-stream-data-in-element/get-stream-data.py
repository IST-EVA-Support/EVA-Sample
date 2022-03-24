import cv2
import gst_cv_helper
import numpy as np
from gi.repository import Gst, GObject, GLib, GstVideo


def gst_video_caps_make(fmt):
  return  "video/x-raw, "\
    "format = (string) " + fmt + " , "\
    "width = " + GstVideo.VIDEO_SIZE_RANGE + ", "\
    "height = " + GstVideo.VIDEO_SIZE_RANGE + ", "\
    "framerate = " + GstVideo.VIDEO_FPS_RANGE
                                                                                                                       

class GetStreamData(Gst.Element):
    # MODIFIED - Gstreamer plugin name
    GST_PLUGIN_NAME = 'get_stream_data'

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
      "output-text": (str,                                      # type
                      "output-text",                            # nick
                      "Text content overlay on the frame",      # blurb
                      "",                                       # default
                      GObject.ParamFlags.READWRITE              # flags
                     )
    }

    def __init__(self):
      # MODIFIED - Setting gstreamer plugin properties default value
      # Note - Initialize properties before Base Class initialization
      self.text = "Do your algorithm or processing here."

      super(GetStreamData, self).__init__()

      self.sinkpad = Gst.Pad.new_from_template(self._sinkpadtemplate, 'sink')

      self.sinkpad.set_chain_function_full(self.chainfunc, None)

      self.sinkpad.set_chain_list_function_full(self.chainlistfunc, None)

      self.sinkpad.set_event_function_full(self.eventfunc, None)

      self.add_pad(self.sinkpad)
      

      self.srcpad = Gst.Pad.new_from_template(self._srcpadtemplate, 'src')

      self.add_pad(self.srcpad)


    def do_get_property(self, prop: GObject.GParamSpec):
      # MODIFIED - Gstreamer plugin properties getting
      if prop.name == 'output-text':
        return self.text
      else:
        raise AttributeError('unknown property %s' % prop.name)
    
    def do_set_property(self, prop: GObject.GParamSpec, value):
      # MODIFIED - Gstreamer plugin properties setting
      if prop.name == 'output-text':
        self.text = int(value)
      else:
        raise AttributeError('unknown property %s' % prop.name)
    
    def chainfunc(self, pad: Gst.Pad, parent, buff: Gst.Buffer) -> Gst.FlowReturn:
      # Implement your frame operate logical here
      # get image stream data
      img = gst_cv_helper.pad_and_buffer_to_numpy(pad, buff, ro=False)

      # After getting the stream data(image data), do the process you want. Here just simply assume doing edge detection by opencv.
      h, w, c = img.shape
      x = int((w * 0.1));
      y = int((h * 0.3));
      size = w / 640.0;
      cv2.putText(img, self.text, (x, y), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, size, (32, 255, 64), 1, cv2.LINE_AA);
      
      return self.srcpad.push(buff)
    
    def chainlistfunc(self, pad: Gst.Pad, parent, list: Gst.BufferList) -> Gst.FlowReturn:
      return self.srcpad.push(list.get(0))
    
    def eventfunc(self, pad: Gst.Pad, parent, event: Gst.Event) -> bool:
      return self.srcpad.push_event(event)



# Register plugin to use it from command line
GObject.type_register(GetStreamData)
__gstelementfactory__ = (GetStreamData.GST_PLUGIN_NAME,
                         Gst.Rank.NONE, GetStreamData)
