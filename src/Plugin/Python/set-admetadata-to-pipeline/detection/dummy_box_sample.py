"""
    gst-launch-1.0 videotestsrc ! adinfer ! dummy_box_sample ! admetadrawer ! ximagesink

"""

import ctypes
import numpy as np
from random import random as rand, randint as rint

import gst_helper
import gst_admeta as admeta

from gi.repository import Gst, GObject

BOX_NUM = 5
DUMMY_BOXS = [[rand(), rand(), rand(), rand()] for i in range(BOX_NUM)]
def parse_inference_data_to_boxs(data):
  # Generate dummy box here, please implement your own parse algorithm
  boxs = []
  for b in DUMMY_BOXS:
    for j in range(len(b)):
      b[j] += 0.01 if rint(0, 1) == 0 else -0.01
      b[j] = max(0, b[j])
      b[j] = min(1, b[j])

    boxs.append((max(0, min(b[0], b[1])),
                 max(0, min(b[2], b[3])),
                 min(1, max(b[0], b[1])),
                 min(1, max(b[2], b[3]))))

  return boxs

class DummyBoxSamplePy(Gst.Element):

    # MODIFIED - Gstreamer plugin name
    GST_PLUGIN_NAME = 'dummy_box_sample'

    __gstmetadata__ = ("Name",
                       "Transform",
                       "Description",
                       "Author")

    __gsttemplates__ = (Gst.PadTemplate.new("src",
                                            Gst.PadDirection.SRC,
                                            Gst.PadPresence.ALWAYS,
                                            Gst.Caps.new_any()),
                        Gst.PadTemplate.new("sink",
                                            Gst.PadDirection.SINK,
                                            Gst.PadPresence.ALWAYS,
                                            Gst.Caps.new_any()))

    _sinkpadtemplate = __gsttemplates__[1]
    _srcpadtemplate = __gsttemplates__[0]

    # MODIFIED - Gstreamer plugin properties
    __gproperties__ = {
    }

    def __init__(self):
      super(DummyBoxSamplePy, self).__init__()

      self.sinkpad = Gst.Pad.new_from_template(self._sinkpadtemplate, 'sink')

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

    def chainlistfunc(self, pad: Gst.Pad, parent, list: Gst.BufferList) -> Gst.FlowReturn:
      """
      :param parent: GstPluginPy
      """

      ##################
      #     BEGINE     #
      ##################

      arr = []
      with gst_helper.get_inference_data_to_numpy(list, (1)) as data:
        boxs = parse_inference_data_to_boxs(data)
        for i, box in enumerate(boxs):
          arr.append(admeta._DetectionBox(i, i, i, i,
                                          box[0],
                                          box[1],
                                          box[2],
                                          box[3],
                                          rand()))

      ##################
      #      END       #
      ##################

      buf = gst_helper._gst_get_buffer_list_writable_buffer(list, 0)
      admeta.set_detection_box(buf, pad, arr)

      list.remove(1, 1)

      return self.srcpad.push(list.get(0))

# Register plugin to use it from command line
GObject.type_register(DummyBoxSamplePy)
__gstelementfactory__ = (DummyBoxSamplePy.GST_PLUGIN_NAME,
                         Gst.Rank.NONE, DummyBoxSamplePy)

