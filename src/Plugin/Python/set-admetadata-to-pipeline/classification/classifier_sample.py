"""
    gst-launch-1.0 videotestsrc ! video/x-raw, width=640, height=480 ! classifier_sample ! adroi_draw ! videoconvert ! ximagesink
"""

import ctypes
import numpy as np
import random
import time
import gst_helper
import adroi
from gi.repository import Gst, GObject, GstVideo


def gst_video_caps_make(fmt):
  return  "video/x-raw, "\
    "format = (string) " + fmt + " , "\
    "width = " + GstVideo.VIDEO_SIZE_RANGE + ", "\
    "height = " + GstVideo.VIDEO_SIZE_RANGE + ", "\
    "framerate = " + GstVideo.VIDEO_FPS_RANGE


class ClassifierSamplePy(Gst.Element):
    # MODIFIED - Gstreamer plugin name
    GST_PLUGIN_NAME = 'classifier_sample'

    __gstmetadata__ = ("Metadata addition",
                       "GstElement",
                       "Python based example for adding classification results",
                       "Lyan Hung <lyan.hung@adlinktech.com>, Dr. Paul Lin <paul.lin@adlinktech.com>")

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
      # MODIFIED - Setting gstreamer plugin properties default value
      # Note - Initialize properties before Base Class initialization
      self.labels = ['water bottle', 'camera', 'chair', 'person', 'slipper', 'mouse', 'Triceratops', 'woodpecker']
      self.duration = 2
      self.time = time.time()
      self.class_id = 0
      self.class_prob = 0.5

      super(ClassifierSamplePy, self).__init__()

      self.sinkpad = Gst.Pad.new_from_template(self._sinkpadtemplate, 'sink')
      self.sinkpad.set_chain_function_full(self.chainfunc, None)
      self.sinkpad.set_chain_list_function_full(self.chainlistfunc, None)
      self.sinkpad.set_event_function_full(self.eventfunc, None)
      self.add_pad(self.sinkpad)
      self.srcpad = Gst.Pad.new_from_template(self._srcpadtemplate, 'src')
      self.add_pad(self.srcpad)

    def do_get_property(self, prop: GObject.GParamSpec):
        raise AttributeError('unknown property %s' % prop.name)

    def do_set_property(self, prop: GObject.GParamSpec, value):
        raise AttributeError('unknown property %s' % prop.name)

    def eventfunc(self, pad: Gst.Pad, parent, event: Gst.Event) -> bool:
      return self.srcpad.push_event(event)

    def chainfunc(self, pad: Gst.Pad, parent, buff: Gst.Buffer) -> Gst.FlowReturn:
      # initial related meta
      f_meta = adroi.gst_buffer_acquire_adroi_frame_meta(hash(buff), hash(pad))
      if f_meta is None:
          print("Can not get adlink ROI frame metadata")
          return self.srcpad.push(buff)
      
      b_meta = adroi.gst_buffer_acquire_adroi_batch_meta(hash(buff));
      if b_meta is None:
          print("Can not get adlink ROI batch metadata")
          return self.srcpad.push(buff)
      
      qrs = f_meta.frame.query('//')
      if qrs is None or len(qrs) == 0:
          print("query is empty from frame meta in classifier_sample.")
          return self.srcpad.push(buff)
      
      # generate reandom data, Change random data every self.duration time
      cls = []
      if time.time() - self.time > self.duration:
          self.class_id = random.randrange(len(self.labels))
          self.class_prob = random.uniform(0, 1)
          self.time = time.time()
      
      # add data
      if len(qrs[0].rois) > 0:
          qrs[0].rois[0].add_classification('sample-engine', '', self.class_prob, self.labels[self.class_id], self.class_id)
      
      return self.srcpad.push(buff)

    def chainlistfunc(self, pad: Gst.Pad, parent, list: Gst.BufferList) -> Gst.FlowReturn:
      return self.srcpad.push(list.get(0))

# Register plugin to use it from command line
GObject.type_register(ClassifierSamplePy)
__gstelementfactory__ = (ClassifierSamplePy.GST_PLUGIN_NAME,
                         Gst.Rank.NONE, ClassifierSamplePy)
