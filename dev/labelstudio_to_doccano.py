import os
import json
import argparse
from base_utils import get_root_dir
from exceptions import ConvertingError
from typing import List
from config import generate_logger, BaseConfig

logger = generate_logger(__name__)


def do_convert(dataset: dict) -> List[dict]:
    """將label studio output對齊doccano格式的邏輯程式

    Args:
        dataset (dict): 用json.load進來的檔案（only for the following format
            1. output of label studio.
            2. json format.
            3. relation extraction task.
            ）

    Raises:
        ConvertingError: 轉換前後長度不一致

    Returns:
        List[dict]: doccano format of the output of label studio.
    """

    results = []
    outer_id = 0
    label_id = 0
    for data in dataset:
        outer_id += 1
        item = {"id": outer_id, "text": data["data"]["text"], "entities": [], "relations": []}
        for anno in data["annotations"][0]["result"]:
            if anno["type"] == "labels":
                label_id += 1
                item["entities"].append(
                    {
                        "id": label_id,
                        "label": anno["value"]["labels"][0],
                        "start_offset": anno["value"]["start"],
                        "end_offset": anno["value"]["end"],
                    }
                )
        results.append(item)
    if len(dataset) != len(results):
        raise ConvertingError("Length is not equal after convert.")
    return results


def convert_to_doccano(
    labelstudio_file: str,
    doccano_file: str,
) -> None:

    """把labelstudio的output（only json）轉換成paddleNLP內所使用的doccano格式，並寫出檔案（doccano_file）

    Args:
        labelstudio_file (str): The export file path of label studio, only support the JSON format.
        doccano_file (str, optional): Saving path in doccano format.. Defaults to "doccano_ext.jsonl".

    Raises:
        ValueError: 找不到labelstudio_file檔案
    """

    logger.info(f"Converting {os.path.basename(labelstudio_file)} into {os.path.basename(doccano_file)}...")
    if not os.path.exists(labelstudio_file):
        raise ValueError("Label studio file not found. Please input the correct path of label studio file.")

    with open(labelstudio_file, "r", encoding="utf-8") as infile:
        for content in infile:
            dataset = json.loads(content)
        results = do_convert(dataset)

    with open(doccano_file, "w", encoding="utf-8") as outfile:
        for item in results:
            outline = json.dumps(item, ensure_ascii=False)
            outfile.write(outline + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    logger.debug("Now os.getcwd()=" + os.getcwd())
    root_dir = None
    try:
        root_dir = get_root_dir()
        default_doccano_file = root_dir + BaseConfig.doccano_data_path + "doccano_ext.jsonl"
    except:
        logger.error("Fail to get root directory.")
        default_doccano_file = "./doccano_ext.jsonl"

    parser.add_argument(
        "--labelstudio_file",
        type=str,
        help="The export file path of label studio, only support the JSON format.",
    )
    parser.add_argument("--doccano_file", type=str, help="Saving path in doccano format.")
    args = parser.parse_args()

    if args.labelstudio_file:
        args.doccano_file = default_doccano_file if args.doccano_file is None else args.doccano_file
        convert_to_doccano(args.labelstudio_file, args.doccano_file)
    else:
        if root_dir is not None:
            data_path = root_dir + BaseConfig.label_studio_data_path
            label_studio_data = os.listdir(data_path)
            logger.info(f"{len(label_studio_data)} label studio file will be convert...")
            if args.doccano_file is None:
                args.doccano_file = [os.path.splitext(data)[0] + "_doccano.jsonl" for data in label_studio_data]
                for data, output_file in zip(label_studio_data, args.doccano_file):
                    convert_to_doccano(data_path + data, root_dir + BaseConfig.doccano_data_path + output_file)
            else:
                for data in label_studio_data:
                    convert_to_doccano(data_path + data, args.doccano_file)
        else:
            raise ValueError("Label studio file not found. Please input the correct path of label studio file.")


def _get_root_dir(self, root_dir_name: str = self.root_dir_name, limits: int = 10) -> str:
    """
    找到根目錄root_dir_name的完整路徑

    Args:
        root_dir_name (str, optional): 根目錄資料夾名稱. Defaults to base_config.root_dir.
        limits (int, optional): 找根目錄的上限次數. Defaults to 10.

    Returns:
        str: root dir of root_dir_name, if it found, else raise ValueError.
    """

    # setup root dir
    now_folder = os.path.dirname(os.path.realpath(__file__))
    now_folder_name = os.path.basename(now_folder)
    for _ in range(limits):
        if now_folder_name != root_dir_name:
            now_folder = os.path.dirname(now_folder)
            now_folder_name = os.path.basename(now_folder)
        else:
            # os.chdir(now_folder)
            return now_folder

    # if root_dir_name not found
    raise ValueError(
        f"{root_dir_name} not found or path error. \
                Please make sure {root_dir_name} is the parent folder of {os.path.basename(__file__)}."
    )