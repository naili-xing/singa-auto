from examples.models.image_object_detection.food_detection.food_objection_base_model import FoodDetectionBase
from keras.applications.xception import Xception


class FoodDetection101(FoodDetectionBase):

    def __init__(self, **knobs):

        super().__init__(clf_model_class_name=Xception, **knobs)

        # pre config
        self.classes = 101
        self.image_size = 299

        # preload files
        self.yolo_cfg_name = "yolov3-food.cfg"
        self.yolo_weight_name = "yolov3-food_final.weights"
        self.food_name = "food.names"

        # this is the model file downloaded from internet,
        # can choose download locally and upload , or download from server
        # if download at server side, leave it to none
        self.preload_clf_model_weights_name = None

        # this is the trained model
        self.trained_clf_model_weights_name = "xception-F101-0.85.h5"

        self._npy_index_name = "food101.npy"
