import os
import contextlib
import ctypes

def _byteify(value):
  if isinstance(value, bytes):
    return value
  elif value is None:
    return b''
  elif isinstance(value, str):
    return value.encode()

  try:
    value = str(value)
  except ValueError:
    return value
  return value.encode()

class _Classification(ctypes.Structure):
  _fields_ = [
    ('index', ctypes.c_uint),
    ('output', ctypes.c_char_p),
    ('label', ctypes.c_char_p),
    ('prob', ctypes.c_float),
  ]

  def __setattr__(self, attr, value):
    if attr in ['output', 'label']:
      value = _byteify(value)
    super().__setattr__(attr, value)

class _DetectionBox(ctypes.Structure):
  _fields_ = [
    ('obj_id', ctypes.c_uint),
    ('obj_label', ctypes.c_char_p),
    ('class_id', ctypes.c_uint),
    ('class_label', ctypes.c_char_p),
    ('x1', ctypes.c_float),
    ('y1', ctypes.c_float),
    ('x2', ctypes.c_float),
    ('y2', ctypes.c_float),
    ('prob', ctypes.c_float),
    ('meta', ctypes.c_char_p),
  ]

  def __setattr__(self, attr, value):
    if attr in ['obj_label', 'class_label', 'meta']:
      value = _byteify(value)
    super().__setattr__(attr, value)

class _Segmentation(ctypes.Structure):
  _fields_ = [
    ('label_id', ctypes.c_uint),
    ('label', ctypes.c_char_p),
  ]

  def __setattr__(self, attr, value):
    if attr in ['label']:
      value = _byteify(value)
    super().__setattr__(attr, value)

CLASSIFICATION_POINTER = ctypes.POINTER(_Classification)
DETECTION_BOX_POINTER = ctypes.POINTER(_DetectionBox)
SEGMENTATION_POINTER = ctypes.POINTER(_Segmentation)

# ctypes imports for missing or broken introspection APIs.
libmeta = ctypes.CDLL('gstadmeta.dll') if os.name =='nt' else ctypes.CDLL('/opt/adlink/eva/lib/libgstadmeta.so')

libmeta.gst_metadata_frames.restype = ctypes.c_uint
libmeta.gst_metadata_frames.argtypes = [ctypes.c_void_p]

libmeta.gst_metadata_get_classification.restype = CLASSIFICATION_POINTER
libmeta.gst_metadata_get_classification.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]

libmeta.gst_metadata_get_detection_box.restype = DETECTION_BOX_POINTER
libmeta.gst_metadata_get_detection_box.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]

libmeta.gst_metadata_get_segmentation.restype = SEGMENTATION_POINTER
libmeta.gst_metadata_get_segmentation.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                                  ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint)]

libmeta.gst_metadata_set_classification.restype = ctypes.c_bool
libmeta.gst_metadata_set_classification.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint,
                                                    CLASSIFICATION_POINTER, ctypes.c_uint]

libmeta.gst_metadata_set_detection_box.restype = ctypes.c_bool
libmeta.gst_metadata_set_detection_box.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint,
                                                   DETECTION_BOX_POINTER, ctypes.c_uint]

libmeta.gst_metadata_set_segmentation.restype = ctypes.c_bool
libmeta.gst_metadata_set_segmentation.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint,
                                                  SEGMENTATION_POINTER, ctypes.c_uint, ctypes.c_uint]

def frames(buf):
  if buf is None:
    return 0

  return libmeta.gst_metadata_frames(hash(buf))

@contextlib.contextmanager
def get_inference_result(buf, frame_idx, cls, func):
  if buf is None:
    yield None
    return

  item_size = ctypes.c_uint(0)
  results = func(hash(buf), ctypes.c_uint(frame_idx), ctypes.pointer(item_size))
  if item_size.value == 0 or ctypes.cast(results, ctypes.c_void_p).value is None:
    yield None
    return

  try:
    yield ctypes.cast(results, ctypes.POINTER(cls * item_size.value)).contents
  finally:
    pass

def get_classification(buf, frame_idx):
  return get_inference_result(buf, frame_idx, _Classification, libmeta.gst_metadata_get_classification)

def get_detection_box(buf, frame_idx):
  return get_inference_result(buf, frame_idx, _DetectionBox, libmeta.gst_metadata_get_detection_box)

@contextlib.contextmanager
def get_seg_inference_result(buf, frame_idx):
  if buf is None:
    yield None
    return

  width = ctypes.c_uint(0)
  height = ctypes.c_uint(0)
  results = libmeta.gst_metadata_get_segmentation(hash(buf), ctypes.c_uint(frame_idx),
                                                  ctypes.pointer(width), ctypes.pointer(height))
  if width.value == 0 or height.value == 0 or ctypes.cast(results, ctypes.c_void_p).value is None:
    yield None
    return

  try:
    yield (width.value, height.value, ctypes.cast(results, ctypes.POINTER(_Segmentation * (width.value * height.value))).contents)
  finally:
    pass

def get_segmentation(buf, frame_idx):
  return get_seg_inference_result(buf, frame_idx)

CLASS_MAP = {
  _Classification: CLASSIFICATION_POINTER,
  _DetectionBox: DETECTION_BOX_POINTER,
}

def check_results(arr):
  for item in arr:
    for attr, _type in item._fields_:
      val = getattr(item, attr, None)
      if val is None:
        setattr(item, attr, val)

def set_inference_result(buf, pad, frame_idx, arr, func):
  if buf is None or pad is None or len(arr) == 0:
    return False

  if not all(filter(lambda item: item.__class__ in CLASS_MAP, arr)):
    return False

  check_results(arr)

  arr_type = (arr[0].__class__ * len(arr))
  arr_ptr = arr_type(*arr)
  return func(hash(buf), hash(pad), frame_idx,
              ctypes.cast(arr_ptr, CLASS_MAP[arr[0].__class__]), len(arr))

def set_classification(buf, pad, arr, frame_idx=0):
  return set_inference_result(buf, pad, frame_idx, arr,
                              libmeta.gst_metadata_set_classification)

def set_detection_box(buf, pad, arr, frame_idx=0):
  return set_inference_result(buf, pad, frame_idx, arr,
                              libmeta.gst_metadata_set_detection_box)

def set_segmentation(buf, pad, arr, shape, frame_idx=0):
  if buf is None or pad is None or len(arr) == 0:
    return False

  check_results(arr)

  h, w = shape

  arr_type = (arr[0].__class__ * (w * h))
  arr_ptr = arr_type(*arr)
  return libmeta.gst_metadata_set_segmentation(hash(buf), hash(pad), frame_idx,
                                               ctypes.cast(arr_ptr, SEGMENTATION_POINTER), w, h)
