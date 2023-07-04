'''
    gst-launch-1.0 videotestsrc ! video/x-raw, format=BGR, width=320, height=240, framerate=30/1 ! classifier_sample ! get_classification ! fakesink
'''

import cv2
import gst_cv_helper
import adroi
import numpy as np
from gi.repository import Gst, GObject, GLib, GstVideo


def gst_video_caps_make(fmt):
  return  "video/x-raw, "\
    "format = (string) " + fmt + " , "\
    "width = " + GstVideo.VIDEO_SIZE_RANGE + ", "\
    "height = " + GstVideo.VIDEO_SIZE_RANGE + ", "\
    "framerate = " + GstVideo.VIDEO_FPS_RANGE
                                                                                                                       

class GetClassification(Gst.Element):
    GST_PLUGIN_NAME = 'get_classification'

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

    def __init__(self):

      super(GetClassification, self).__init__()

      self.sinkpad = Gst.Pad.new_from_template(self._sinkpadtemplate, 'sink')

      self.sinkpad.set_chain_function_full(self.chainfunc, None)

      self.sinkpad.set_chain_list_function_full(self.chainlistfunc, None)

      self.sinkpad.set_event_function_full(self.eventfunc, None)

      self.add_pad(self.sinkpad)
      

      self.srcpad = Gst.Pad.new_from_template(self._srcpadtemplate, 'src')

      self.add_pad(self.srcpad)


    def do_get_property(self, prop: GObject.GParamSpec):
        return
    
    def do_set_property(self, prop: GObject.GParamSpec, value):
        return
    
    def chainfunc(self, pad: Gst.Pad, parent, buff: Gst.Buffer) -> Gst.FlowReturn:
      qrs = adroi.gst_buffer_adroi_query(hash(buff), '//')
      if qrs is None or len(qrs) == 0:
          print("query is empty from frame meta in get classification.")
          return self.srcpad.push(buff)
      
      for roi in qrs[0].rois:
          if roi.category == 'box':
              box = roi.to_box()
              labelInfo = box.datas[0].to_classification()
              
              print("===== metadata version 2 in application =====")
              print("Label ID = ", labelInfo.label_id)
              print("Label = ", labelInfo.label)
              print("Prob =  ", labelInfo.confidence)
              print("=============================================")
      
      return self.srcpad.push(buff)
    
    def chainlistfunc(self, pad: Gst.Pad, parent, list: Gst.BufferList) -> Gst.FlowReturn:
      return self.srcpad.push(list.get(0))
    
    def eventfunc(self, pad: Gst.Pad, parent, event: Gst.Event) -> bool:
      return self.srcpad.push_event(event)


GObject.type_register(GetClassification)
__gstelementfactory__ = (GetClassification.GST_PLUGIN_NAME,
                         Gst.Rank.NONE, GetClassification)
