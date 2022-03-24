import cv2
import gst_cv_helper
import gst_admeta as admeta # Required to import to get ADLINK inference metadata
import numpy as np
from gi.repository import Gst, GObject, GLib, GstVideo


def gst_video_caps_make(fmt):
  return  "video/x-raw, "\
    "format = (string) " + fmt + " , "\
    "width = " + GstVideo.VIDEO_SIZE_RANGE + ", "\
    "height = " + GstVideo.VIDEO_SIZE_RANGE + ", "\
    "framerate = " + GstVideo.VIDEO_FPS_RANGE
                                                                                                                       

class GetObjectDetection(Gst.Element):
    GST_PLUGIN_NAME = 'get_object_detection'

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

      super(GetObjectDetection, self).__init__()

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
      # This function will get classification result from admetadata
      boxes = admeta.get_detection_box(buff,0)
      
      # Iteratively retrieve the content of object detected
      with boxes as det_box :
        if det_box is not None :
            for box in det_box:                
                print('Detection result: prob={:.3f}, coordinate=({:.2f},{:.2f}) to ({:.2f},{:.2f})), Index = {}, Label = {}'.format(box.prob,box.x1,box.y1,box.x2, box.y2, box.obj_id, box.obj_label.decode("utf-8").strip()))
        else:
            print("None")
      
      return self.srcpad.push(buff)
    
    def chainlistfunc(self, pad: Gst.Pad, parent, list: Gst.BufferList) -> Gst.FlowReturn:
      return self.srcpad.push(list.get(0))
    
    def eventfunc(self, pad: Gst.Pad, parent, event: Gst.Event) -> bool:
      return self.srcpad.push_event(event)


GObject.type_register(GetObjectDetection)
__gstelementfactory__ = (GetObjectDetection.GST_PLUGIN_NAME,
                         Gst.Rank.NONE, GetObjectDetection)
