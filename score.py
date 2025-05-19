import json
from argparse import ArgumentParser


def main(args) -> None:
    with open(args.ground_truth, "r") as fp:
        ground_truth = json.load(fp)
        ground_truth = [x["label"] for x in ground_truth]

    with open(args.predictions, "r") as fp:
        predictions = fp.readlines()
        predictions = list(map(lambda x: int(x), predictions))

    tp = 0
    fp = 0
    fn = 0
    tn = 0
    for g, p in zip(ground_truth, predictions):
        if g == 1 and p == 1:
            tp += 1
        elif g == 0 and p == 1:
            fp += 1
        elif g == 1 and p == 0:
            fn += 1
        elif g == 0 and p == 0:
            tn += 1
        else:
            raise ValueError()
    score = 2 * tp * tn / (2 * tp * tn + fp * tp + tn * fn)
    print(score)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-g", "--ground_truth", default="inputs.json")
    parser.add_argument("-p", "--predictions", default="outputs.txt")
    args = parser.parse_args()
    main(args)