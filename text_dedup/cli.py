import argparse
from multiprocessing import cpu_count
from time import time

from .encoder import task_dedup


def main():
    parser = argparse.ArgumentParser(description="Memory-friendly deduplicating text CLI")
    parser.add_argument("-i", "--inputs", type=str, required=True, nargs="+", help="input text files")
    parser.add_argument("-s", "--shard_root", type=str, required=True, help="shard directory")
    parser.add_argument("-o", "--output", type=str, required=True, help="deduplicated text path")
    parser.add_argument("-f", "--hash_func_type", type=str, default="sha1", help="hash function name")
    parser.add_argument(
        "-r", "--hash_func_input_format", type=str, default="0-9가-힣ㄱ-ㅎㅏ-ㅣa-zA-Z",
        help="hash function input format regular expression. (default %(default)s)"
    )
    default_process_count = max(1, cpu_count() - 1)
    parser.add_argument(
        "-p", "--n_processes", type=int, default=default_process_count,
        help="num of multiprocessing pools. (default %(default)s)",
    )
    parser.add_argument(
        "-c", "--chunksize", type=int, default=100000,
        help="multiprocessing chunksize; num lines. (default %(default)s)",
    )
    parser.add_argument(
        "-b", "--max_block_size", type=str, default=None,
        help="maximum output block size. (default %(default)s)"
    )
    parser.add_argument("-t", "--sort", dest="sort", action="store_true", help="sort lines in shard files")
    parser.add_argument("-k", "--keep", dest="keep", action="store_true", help="keep shard files")
    parser.add_argument(
        "-pr", "--prefix_length", type=int, default=4,
        help="shard file name length. (default %(default)s)"
    )

    args = parser.parse_args()
    elapsed_time = time()
    task_dedup(**args.__dict__)
    elapsed_time = time() - elapsed_time
    print(f"elapsed_time = {int(elapsed_time)} seconds")


if __name__ == "__main__":
    main()
