"""
    gst-launch-1.0 videotestsrc ! adinfer ! classifier_sample ! admetadrawer ! ximagesink

"""

import ctypes
import numpy as np

import gst_helper
import gst_admeta as admeta

from gi.repository import Gst, GObject

class ClassifierSamplePy(Gst.Element):

    # MODIFIED - Gstreamer plugin name
    GST_PLUGIN_NAME = 'classifier_sample'

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
      "class-num": (int,  # type
                    "class-num",  # nick
                    "Class number",  # blurb
                    1,  # min
                    65536,  # max
                    1001,  # default
                    GObject.ParamFlags.READWRITE  # flags
      ),
      "batch-num": (int,  # type
                    "batch-num",  # nick
                    "Batch number",  # blurb
                    1,  # min
                    65536,  # max
                    1,  # default
                    GObject.ParamFlags.READWRITE  # flags
      ),
      "label": (str,  # type
                "label",  # nick
                "Label file",  # blurb
                "",
                GObject.ParamFlags.READWRITE  # flags
      ),
    }

    def __init__(self):
      # MODIFIED - Setting gstreamer plugin properties default value
      # Note - Initialize properties before Base Class initialization
      self.class_num = 1001
      self.batch_num = 1
      self.label = ""
      self.labels = None

      super(ClassifierSamplePy, self).__init__()

      self.sinkpad = Gst.Pad.new_from_template(self._sinkpadtemplate, 'sink')

      self.sinkpad.set_chain_list_function_full(self.chainlistfunc, None)

      self.sinkpad.set_event_function_full(self.eventfunc, None)

      self.add_pad(self.sinkpad)

      self.srcpad = Gst.Pad.new_from_template(self._srcpadtemplate, 'src')

      self.add_pad(self.srcpad)


    def do_get_property(self, prop: GObject.GParamSpec):
      # MODIFIED - Gstreamer plugin properties getting
      if prop.name == 'class-num':
        return self.class_num
      elif prop.name == 'batch-num':
        return self.batch_num
      elif prop.name == 'label':
        return self.label
      else:
        raise AttributeError('unknown property %s' % prop.name)

    def do_set_property(self, prop: GObject.GParamSpec, value):
      # MODIFIED - Gstreamer plugin properties setting
      if prop.name == 'class-num':
        self.class_num = int(value)
      elif prop.name == 'batch-num':
        self.batch_num = int(value)
      elif prop.name == 'label':
        self.label = str(value)
        with open(self.label, 'r') as f:
          self.labels = [l.strip() for l in f]
      else:
        raise AttributeError('unknown property %s' % prop.name)

    def eventfunc(self, pad: Gst.Pad, parent, event: Gst.Event) -> bool:
      return self.srcpad.push_event(event)

    def chainlistfunc(self, pad: Gst.Pad, parent, list: Gst.BufferList) -> Gst.FlowReturn:
      """
      :param parent: GstPluginPy
      """

      # Get inference result raw data from second gst buffer in gst buffer list
      with gst_helper.get_inference_data_to_numpy(list, (self.batch_num, self.class_num)) as data:

        # MODIFIED - Modify parse content depend on your deep leanring model
        cls = []

        ##################
        #     BEGINE     #
        ##################

        for b in range(self.batch_num):
          max_idx = np.argmax(data)
          max_prob = data[b][max_idx]
          label = self.labels[max_idx] if self.labels is not None and max_idx < len(self.labels) else str(max_idx)
          cls.append(admeta._Classification(0, '', label, max_prob))

        ##################
        #      END       #
        ##################

        # Write classification result into metadata
        buf = gst_helper._gst_get_buffer_list_writable_buffer(list, 0)
        admeta.set_classification(buf, pad, cls)

      list.remove(1, 1)

      return self.srcpad.push(list.get(0))

# Register plugin to use it from command line
GObject.type_register(ClassifierSamplePy)
__gstelementfactory__ = (ClassifierSamplePy.GST_PLUGIN_NAME,
                         Gst.Rank.NONE, ClassifierSamplePy)
