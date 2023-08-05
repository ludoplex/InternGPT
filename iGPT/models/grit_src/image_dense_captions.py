import argparse
import multiprocessing as mp
import os
import time
import cv2
import tqdm
import sys

from detectron2.config import get_cfg
from detectron2.data.detection_utils import read_image
from detectron2.utils.logger import setup_logger

sys.path.insert(0, 'iGPT/models/grit_src/third_party/CenterNet2/projects/CenterNet2/')
from centernet.config import add_centernet_config
from ..grit_src.grit.config import add_grit_config

from ..grit_src.grit.predictor import VisualizationDemo


# constants
WINDOW_NAME = "GRiT"


def dense_pred_to_caption(predictions):
    boxes = predictions["instances"].pred_boxes if predictions["instances"].has("pred_boxes") else None
    object_description = predictions["instances"].pred_object_descriptions.data
    return "".join(
        f"{object_description[i]}: {[int(a) for a in boxes[i].tensor.cpu().detach().numpy()[0]]}; "
        for i in range(len(object_description))
    )

def dense_pred_to_caption_only_name(predictions):
    # boxes = predictions["instances"].pred_boxes if predictions["instances"].has("pred_boxes") else None
    object_description = predictions["instances"].pred_object_descriptions.data
    del predictions
    return ",".join(object_description)

def setup_cfg(args):
    cfg = get_cfg()

    add_centernet_config(cfg)
    add_grit_config(cfg)
    cfg.merge_from_file(args["config_file"])
    cfg.merge_from_file(args["config_file"])
    cfg.merge_from_list(args["opts"])
    # Set score_threshold for builtin models
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = args["confidence_threshold"]
    cfg.MODEL.PANOPTIC_FPN.COMBINE.INSTANCES_CONFIDENCE_THRESH = args["confidence_threshold"]
    if args["test_task"]:
        cfg.MODEL.TEST_TASK = args["test_task"]
    cfg.MODEL.BEAM_SIZE = 1
    cfg.MODEL.ROI_HEADS.SOFT_NMS_ENABLED = False
    cfg.USE_ACT_CHECKPOINT = False
    if args["device"]=="cpu":
        cfg.MODEL.DEVICE="cpu"
    cfg.freeze()
    return cfg

def get_parser(device):
    return {
        'config_file': "iGPT/models/grit_src/configs/GRiT_B_DenseCap_ObjectDet.yaml",
        'device': device,
        'confidence_threshold': 0.5,
        'test_task': 'DenseCap',
        'opts': ["MODEL.WEIGHTS", "model_zoo/grit_b_densecap_objectdet.pth"],
    }

def image_caption_api(image_src, device):
    args2 = get_parser(device)
    cfg = setup_cfg(args2)
    demo = VisualizationDemo(cfg)
    if image_src:
        img = read_image(image_src, format="BGR")
        predictions, visualized_output = demo.run_on_image(img)
        new_caption = dense_pred_to_caption(predictions)
    return new_caption

def init_demo(device):
    args2 = get_parser(device)
    cfg = setup_cfg(args2)
    return VisualizationDemo(cfg)

if __name__=="__main__":
    import os
    os.environ['CUDA_VISIBLE_DEVICES']='7'
    print(image_caption_api("images/dancing_example_4.mp4_20230417_135359.263.jpg",'cuda'))