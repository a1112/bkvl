import argparse

from BKVisionListener import resolver

parser = argparse.ArgumentParser(description="BKVision Test program description")

# 添加参数
parser.add_argument('--config', type=str,default="listener.yaml", help='yaml config file')
args = parser.parse_args()


def main(args_):
    resolver(args_.config)


if __name__ == "__main__":
    main(args)
