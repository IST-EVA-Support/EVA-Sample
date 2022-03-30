"""
    gst-launch-1.0 videotestsrc ! adinfer ! segment_sample ! admetadrawer ! ximagesink

"""

import ctypes
import numpy as np

import gst_helper
import gst_admeta as admeta

from gi.repository import Gst, GObject

class SegmentSamplePy(Gst.Element):

    # MODIFIED - Gstreamer plugin name
    GST_PLUGIN_NAME = 'segment_sample'

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
                      "If inference will only return maximum probability of class then setting this value to 1. ",  # blurb
                      1,  # min
                      65536,  # max
                      1,  # default
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
      "blob-width": (int,  # type
                     "blob Width",  # nick
                     "Blob width",  # blurb
                     1,  # min
                     65536,  # max
                     416,  # default
                     GObject.ParamFlags.READWRITE  # flags
      ),
      "blob-height": (int,  # type
                      "blob-height",  # nick
                      "Blob height",  # blurb
                      1,  # min
                      65536,  # max
                      416,  # default
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
      self.class_num = 1
      self.batch_num = 1
      self.blob_width = 416
      self.blob_height = 416
      self.label = ""
      self.labels = None

      super(SegmentSamplePy, self).__init__()

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
      elif prop.name == 'blob-width':
        return self.blob_width
      elif prop.name == 'blob-height':
        return self.blob_height
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
      elif prop.name == 'blob-width':
        self.blob_width = int(value)
      elif prop.name == 'blob-height':
        self.blob_height = int(value)
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
      blob_shape = (self.batch_num, self.class_num, self.blob_height, self.blob_width)
      with gst_helper.get_inference_data_to_numpy(list, blob_shape) as data:

        # MODIFIED - Modify parse content depend on your deep leanring model

        ##################
        #     BEGINE     #
        ##################
        segs = []
        max_cls = np.argmax(data, axis=1) if self.class_num != 1 else None
        for b in range(self.batch_num):
          b_segs = []
          for r in range(self.blob_height):
            for c in range(self.blob_width):
              if self.class_num == 1:
                label_id = int(data[b][0][r][c])
              else:
                label_id = int(max_cls[b][r][c])
              label_str = self.labels[label_id] if self.labels is not None and label_id < len(self.labels) else str(label_id)

              b_segs.append(admeta._Segmentation(label_id, label_str))
          segs.append(b_segs)
        ##################
        #      END       #
        ##################
        # Write segmentation result into metadata
        buf = gst_helper._gst_get_buffer_list_writable_buffer(list, 0)
        for b in range(self.batch_num):
          admeta.set_segmentation(buf, pad, segs[b], (blob_shape[2], blob_shape[3]), frame_idx=b)

      list.remove(1, 1)

      return self.srcpad.push(list.get(0))

# Register plugin to use it from command line
GObject.type_register(SegmentSamplePy)
__gstelementfactory__ = (SegmentSamplePy.GST_PLUGIN_NAME,
                         Gst.Rank.NONE, SegmentSamplePy)
