import os
import re
import math

import cv2

import gst_helper
import gst_cv_helper

from gi.repository import Gst, GObject, GLib, GstVideo

def draw_boxs(img, boxs, labels=[]):
  h, w, c = img.shape
  face = cv2.FONT_HERSHEY_COMPLEX
  scale = 1.5
  thickness = 2
  baseline = 0
  for idx, cls, x1, y1, x2, y2 in boxs:
    l = labels[cls] if cls < len(labels) else str(cls)
    size = cv2.getTextSize(l, face, scale, thickness+1)
    x1, x2, y1, y2 = int(x1*w), int(x2*w), int(y1*h), int(y2*h)
    cv2.rectangle(img, (x1, y1), (x2, y2), (255, 255, 0), thickness)
    cv2.rectangle(img, (x1, y1), (x1+size[0][0], y1+size[0][1]+size[1]), (255, 255, 255), -1)
    cv2.putText(img, l, (x1, y1 + size[0][1]), face, scale, (0, 0, 255), thickness+1)

##### Analyze inference result context #####

def analyze_blob_size(val):
  blob_size = []
  try:
    for s in map(lambda b: b.strip(), val.split(",")):
      if "x" in s:
        w, h = s.split("x")
        blob_size.append((int(w), int(h)))
      else:
        blob_size.append((int(s), int(s)))
    return blob_size
  except:
    pass

  return

def analyze_mask(s):
  try:
    mask_format = re.compile("\((?:\d+,)*\d+\)")
    mask = []
    for m in mask_format.findall(s.replace(" ", "")):
      mask.append(tuple(map(int, m.replace("(", "").replace(")", "").split(","))))
    return mask
  except:
    pass

  return

def analyze_anchor(s):
  try:
    anchor_format = re.compile("\((?:\d+,)?\d+\)")
    anchor = []
    for a in anchor_format.findall(s.replace(" ", "")):
      _anchor = tuple(map(int, a.replace("(", "").replace(")", "").split(",")))
      if len(_anchor) == 1:
        _anchor = (_anchor[0], _anchor[0])
      elif len(_anchor) > 2:
        _anchor = tuple(_anchor[:2])
      anchor.append(_anchor)
    return anchor
  except:
    pass

  return

def parse_yolo_output_blob(blob, iw, ih, mask, anchor, threshold=0.8):
  boxs = []
  flat_blob = blob.reshape(-1)
  b, c, h, w = blob.shape
  mask_channel = int(c / 3)
  coords = 4
  classes = mask_channel - coords - 1
  num = len(mask)
  def entry_index(side_square, mask_channels, n, loc, entry):
    return n * side_square * mask_channel + entry * side_square + loc;

  side = h
  side_square = h * w
  i = 0
  for row in range(h):
    for col in range(w):
      for n in range(num):
        obj_index = entry_index(side_square, mask_channel, n, i, coords)
        box_index = entry_index(side_square, mask_channel, n, i, 0)
        scale = flat_blob[obj_index]
        if scale < threshold:
          continue;
        x = (col + flat_blob[box_index + 0 * side_square]) / side * iw
        y = (row + flat_blob[box_index + 1 * side_square]) / side * ih
        aw, ah = anchor[n]
        height = math.exp(flat_blob[box_index + 3 * side_square]) * ah
        width = math.exp(flat_blob[box_index + 2 * side_square]) * aw

        for j in range(classes):
          class_index = entry_index(side_square, mask_channel, n, i, coords + 1 + j)
          prob = scale * flat_blob[class_index]
          if prob < threshold:
            continue
          boxs.append((obj_index, j,
                       max(0.0, (x - width / 2) / iw), max(0.0, (y - height / 2) / ih),
                       min(1.0, (x + width / 2) / ih), min(1.0, (y + height / 2) / ih)))
      i+=1
  return boxs

############################################

##### GStreamer python plugin context #####

def gst_video_caps_make(fmt):
  return  "video/x-raw, "\
    "format = (string) " + fmt + " , "\
    "width = " + GstVideo.VIDEO_SIZE_RANGE + ", "\
    "height = " + GstVideo.VIDEO_SIZE_RANGE + ", "\
    "framerate = " + GstVideo.VIDEO_FPS_RANGE

class AdYoloPy(Gst.Element):
  GST_PLUGIN_NAME = 'adsample_yolo_py'

  __gstmetadata__ = ("AdYolo",
                     "GstElement",
                     "This is yolo interpret python sample.",
                     "Lyan")

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

  __gproperties__ = {
    "class-num": (int,  # type
                  "class-num",  # nick
                  "Class number",  # blurb
                  1, 65536, 80,
                  GObject.ParamFlags.READWRITE  # flags
    ),
    "batch-num": (int, "batch-num", "Batch number",
                  1, 256, 1, GObject.ParamFlags.READWRITE),
    "blob-size": (str, "blob-size", """OpenVINO inference output blob's output width and height, can using comma to define multiple output blob's size. for example: "26,52,13" is three output blob's size. 
    You can also define blob's size by WxH, for example: "26x42,52x68,13x19".
    Default value is 26,52,13""",
                   "26,52,13", GObject.ParamFlags.READWRITE),
    "mask": (str, "mask", "Yolo mask",
             "(3,4,5),(0,1,2),(6,7,8)", GObject.ParamFlags.READWRITE),
    "anchor": (str, "anchor", "Yolo anchor",
               "(10,13),(16,30),(33,23),(30,61),(62,45),(59,119),(116,90),(156,198),(373,326)", GObject.ParamFlags.READWRITE),
    "label-file": (str, "label-file", "Label file",
                   "", GObject.ParamFlags.READWRITE),
    "input-width": (int, "input-width", "Input width of inference",
                    1, 65536, 416, GObject.ParamFlags.READWRITE),
    "input-height": (int, "input-height", "Input height of inference",
                     1, 65536, 416, GObject.ParamFlags.READWRITE),
    "threshold": (float, "threshold", "Threshold of box confidence",
                     0.0, 1.0, 0.8, GObject.ParamFlags.READWRITE),
    "label-file": (str, "label-file", "Label file",
                  "", GObject.ParamFlags.READWRITE),
  }

  def __init__(self):
    # Initialize properties before Base Class initialization
    self.class_num, self.batch_num, self.input_width, self.input_height, self.threshold = 80, 1, 416, 416, 0.8
    self.blob_size_str = "26,52,13"
    self.blob_size = analyze_blob_size(self.blob_size_str)
    self.mask_str = "(3,4,5),(0,1,2),(6,7,8)"
    self.mask = analyze_mask(self.mask_str)
    self.anchor_str = "(10,13),(16,30),(33,23),(30,61),(62,45),(59,119),(116,90),(156,198),(373,326)"
    self.anchor = analyze_anchor(self.anchor_str)
    self.label_file, self.labels = "", []

    super(AdYoloPy, self).__init__()

    self.sinkpad = Gst.Pad.new_from_template(self._sinkpadtemplate, 'sink')

    self.sinkpad.set_chain_function_full(self.chainfunc, None)

    self.sinkpad.set_chain_list_function_full(self.chainlistfunc, None)

    self.sinkpad.set_event_function_full(self.eventfunc, None)
    self.add_pad(self.sinkpad)

    self.srcpad = Gst.Pad.new_from_template(self._srcpadtemplate, 'src')

    self.srcpad.set_event_function_full(self.srceventfunc, None)

    self.srcpad.set_query_function_full(self.srcqueryfunc, None)
    self.add_pad(self.srcpad)

  def do_get_property(self, prop: GObject.GParamSpec):
    if prop.name == 'class-num':
      return self.class_num
    elif prop.name == 'batch-num':
      return self.batch_num
    elif prop.name == 'blob-size':
      return self.blob_size_str
    elif prop.name == 'mask':
      return self.mask_str
    elif prop.name == 'anchor':
      return self.anchor_str
    elif prop.name == 'input-width':
      return self.input_width
    elif prop.name == 'input-height':
      return self.input_height
    elif prop.name == 'threshold':
      return self.threshold
    elif prop.name == 'label-file':
      return self.label_file
    else:
      raise AttributeError('unknown property %s' % prop.name)

  def do_set_property(self, prop: GObject.GParamSpec, value):
    if prop.name == 'class-num':
      self.class_num = int(value)
    elif prop.name == 'batch-num':
      self.batch_num = int(value)
    elif prop.name == 'blob-size':
      blob_size = analyze_blob_size(str(value))
      if blob_size is None:
        raise AttributeError('Incurrect blob size format %s' % value)
      self.blob_size_str, self.blob_size = str(value), blob_size
    elif prop.name == 'mask':
      mask = analyze_mask(str(value))
      if mask is None:
        raise AttributeError('Incurrect mask format %s' % value)
      self.mask_str, self.mask = str(value), mask
    elif prop.name == 'anchor':
      anchor = analyze_anchor(str(value))
      if anchor is None:
        raise AttributeError('Incurrect anchor format %s' % value)
      self.anchor_str, self.anchor = str(value), anchor
    elif prop.name == 'input-width':
      self.input_width = int(value)
    elif prop.name == 'input-height':
      self.input_height = int(value)
    elif prop.name == 'threshold':
      self.threshold = float(value)
    elif prop.name == 'label-file':
      self.label_file = str(value)
      if os.path.isfile(self.label_file):
        with open(self.label_file, 'r') as f:
          self.labels = list(map(lambda l: l.strip(), f))
    else:
      raise AttributeError('unknown property %s' % prop.name)

  def chainfunc(self, pad: Gst.Pad, parent, buff: Gst.Buffer) -> Gst.FlowReturn:
    return self.srcpad.push(buff)

  def chainlistfunc(self, pad: Gst.Pad, parent, buff_list: Gst.BufferList) -> Gst.FlowReturn:
    class_coord_dim = (self.class_num + 5) * 3
    out_sizes = list(map(lambda bs: self.batch_num * class_coord_dim * bs[0] * bs[1], self.blob_size))
    boxs = []
    with gst_helper.get_inference_data_to_numpy(buff_list, (sum(out_sizes))) as data:
      offset = 0
      for idx, s in enumerate(out_sizes):
        blob = data[offset:offset+s].reshape(self.batch_num, class_coord_dim,
                                             *self.blob_size[idx])
        mask = self.mask[idx]
        anchor = list(map(lambda m: self.anchor[m], mask))
        _boxs = parse_yolo_output_blob(blob, self.input_width, self.input_height, mask, anchor, threshold=self.threshold)
        boxs += _boxs
        offset += s


    buf = gst_helper._gst_get_buffer_list_writable_buffer(buff_list, 0)
    img = gst_cv_helper.pad_and_buffer_to_numpy(pad, buf, ro=False)
    # Draw yolo results
    draw_boxs(img, boxs, self.labels)

    buff_list.remove(1, 1)

    return self.srcpad.push(buff_list.get(0))

  def eventfunc(self, pad: Gst.Pad, parent, event: Gst.Event) -> bool:
    return self.srcpad.push_event(event)

  def srcqueryfunc(self, pad: Gst.Pad, parent, query: Gst.Query) -> bool:
    return self.sinkpad.query(query)

  def srceventfunc(self, pad: Gst.Pad, parent, event: Gst.Event) -> bool:
    return self.sinkpad.push_event(event)


GObject.type_register(AdYoloPy)
__gstelementfactory__ = (AdYoloPy.GST_PLUGIN_NAME,
                         Gst.Rank.NONE, AdYoloPy)

###########################################
