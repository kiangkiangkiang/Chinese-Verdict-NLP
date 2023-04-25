from base_utils import set_seed, shuffle_data, get_root_dir
from config import DefaultConfig, generate_logger
from typing import List, Tuple
import json
import os
from decimal import Decimal
import argparse

logger = generate_logger(name=__name__)


def add_negative_samples():
    # TODO add negative when result == []
    # duplicate?
    pass


def convert_format(dataset: List[dict], is_shuffle: bool = True) -> List[dict]:
    logger.debug(f"In convert_format, data len = {len(dataset)}")
    results = []
    for data in dataset:
        uie_format = {
            output_type: {"content": data["data"]["text"], "result_list": [], "prompt": output_type}
            for output_type in DefaultConfig.ner_type
        }
        for label_result in data["annotations"][0]["result"]:
            if label_result["type"] != "labels":
                raise ValueError(
                    "Now we only deal with NER tasks, \
                        which means the type of label studio result is 'labels'."
                )

            uie_format[label_result["value"]["labels"][0]]["result_list"].append(
                {
                    "text": label_result["value"]["text"],
                    "start": label_result["value"]["start"],
                    "end": label_result["value"]["end"],
                }
            )
        # add_negative_samples(uie_format)# if result == []
        results.extend(uie_format.values())
    return shuffle_data(results) if is_shuffle else results


def do_split(
    dataset: List[dict],
    split_ratio: List[int] = [0.8, 0.1, 0.1],
    is_shuffle: bool = True,
) -> Tuple[List[dict], List[dict], List[dict]]:

    logger.debug(f"in do_split, len(dataset)={len(dataset)}")

    if is_shuffle:
        dataset = shuffle_data(dataset)

    p1 = int(len(dataset) * split_ratio[0])
    p2 = int(len(dataset) * (split_ratio[0] + split_ratio[1]))

    if p1 <= 0:
        raise ValueError(f"Number of training data is too small {p1} <= 0")

    # TODO check special case: [1, 0, 0]
    return (
        convert_format(dataset[:p1], is_shuffle),
        convert_format(dataset[p1:p2], is_shuffle),
        convert_format(dataset[p2:], is_shuffle),
    )


# main function
def split_labelstudio(
    labelstudio_file: str,
    save_dir: str = "./",
    seed: int = 100,
    split_ratio: List[int] = [0.8, 0.1, 0.1],
    is_shuffle: bool = True,
) -> None:

    logger.info(f"Converting {os.path.basename(labelstudio_file)} into {save_dir}...")
    set_seed(seed)

    if not os.path.exists(labelstudio_file):
        raise ValueError("Label studio file not found. Please input the correct path of label studio file.")

    if not os.path.exists(save_dir):
        logger.warning(f"{save_dir} not found. Automatically making a directory...")
        os.makedirs(save_dir)

    if len(split_ratio) != 3:
        raise ValueError(
            f"Length Error in split_ratio: {len(split_ratio)}. Only accept len(split_ratio)==3 for splits."
        )

    if Decimal(str(split_ratio[0])) + Decimal(str(split_ratio[1])) + Decimal(str(split_ratio[2])) != Decimal("1"):
        raise ValueError("Please set correct split_ratio, sum of elements in split_ratio should be equal to 1.")

    with open(labelstudio_file, "r", encoding="utf-8") as infile:
        for content in infile:
            dataset = json.loads(content)
        splitted_data = do_split(dataset=dataset, split_ratio=split_ratio, is_shuffle=is_shuffle)

    # TODO test work?
    for data, data_name in zip(splitted_data, ("training_data.txt", "eval_data.txt", "testing_data.txt")):
        logger.debug(f"len({data_name}) = {len(data)}")
        with open(save_dir + data_name, "w", encoding="utf-8") as outfile:
            for item in data:
                outline = json.dumps(item, ensure_ascii=False)
                outfile.write(outline + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    try:
        root_dir = get_root_dir()
        default_labelstudio_file = root_dir + DefaultConfig.label_studio_data_path
        default_save_dir = root_dir + DefaultConfig.experiment_data_path
    except:
        logger.error("Fail to get root directory.")
        default_save_dir, default_labelstudio_file = "./", None

    parser.add_argument(
        "--labelstudio_file",
        default=default_labelstudio_file,
        type=str,
        help="The export file path of label studio, only support the JSON format.",
    )
    parser.add_argument("--save_dir", default=default_save_dir, type=str, help="The path of data that you wanna save.")
    parser.add_argument("--seed", type=int, default=1000, help="Random seed for initialization")
    parser.add_argument(
        "--split_ratio",
        default=[0.8, 0.1, 0.1],
        type=float,
        nargs="*",
        help="The ratio of samples in datasets. [0.7, 0.2, 0.1] means 70% samples used for training, 20% for evaluation and 10% for test.",
    )
    parser.add_argument(
        "--is_shuffle",
        choices=["True", "False"],
        default="True",
        type=str,
        help="Whether to shuffle the labeled dataset, defaults to True.",
    )
    args = parser.parse_args()

    if args.labelstudio_file == root_dir + DefaultConfig.label_studio_data_path:
        label_studio_data = os.listdir(args.labelstudio_file)
        if len(label_studio_data) == 1:
            split_labelstudio(
                labelstudio_file=args.labelstudio_file + label_studio_data[0],
                save_dir=args.save_dir,
                seed=args.seed,
                split_ratio=args.split_ratio,
                is_shuffle=eval(args.is_shuffle),
            )
        else:
            logger.info(f"There is/are {len(label_studio_data)} label studio file(s) will be convert...")
            label_studio_file_name = [os.path.splitext(data)[0] for data in label_studio_data]
            for data, name in zip(label_studio_data, label_studio_file_name):
                os.makedirs(args.save_dir + "data_for_" + name)
                args.save_dir = args.save_dir + "data_for_" + name + "/"
                split_labelstudio(
                    labelstudio_file=root_dir + DefaultConfig.label_studio_data_path + data,
                    save_dir=args.save_dir,
                    seed=args.seed,
                    split_ratio=args.split_ratio,
                    is_shuffle=eval(args.is_shuffle),
                )
    else:
        split_labelstudio(
            labelstudio_file=args.labelstudio_file,
            save_dir=args.save_dir,
            seed=args.seed,
            split_ratio=args.split_ratio,
            is_shuffle=eval(args.is_shuffle),
        )
