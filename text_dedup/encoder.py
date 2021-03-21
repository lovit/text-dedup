import math
import os
import re
from collections import defaultdict
from glob import glob
from hashlib import sha1
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
from typing import List, Union


class Normalizer:
    def __init__(self, pattern: str = "0-9가-힣ㄱ-ㅎㅏ-ㅣa-zA-Z"):
        self.pattern = re.compile(f"[^{pattern}]")

    def __call__(self, line: str) -> str:
        return self.pattern.sub("", line)


class Encoder:
    """
    Example:
        >>> normalizer = Normalizer("0-9가-힣ㄱ-ㅎㅏ-ㅣa-zA-Z")
        >>> encoder = Encoder("sha1", normalizer)
        >>> encoder("예문입니다")
        $ ('예문입니다', '93620c8a877cbc8701923138c217c9a8327815e1')
    """
    def __init__(self, hash_func_type, normalizer):
        self.normalizer = normalizer
        if callable(hash_func_type):
            self.hash = hash_func_type
        elif hash_func_type == "sha1":
            self.hash = sha1
        else:
            raise ValueError("Support only `callable` or `sha1`")

    def __call__(self, line: str):
        return self.encode(line)

    def encode(self, line: str):
        norm = self.normalizer(line)
        code = self.hash(norm.encode("utf-8")).hexdigest()
        return line, code

    def encode_batch(self, lines: List[str], n_processes: int, chunksize: int = None):
        with Pool(processes=n_processes) as p:
            out = list(p.imap(self.encode, lines, chunksize=chunksize))
        return out


def encode_a_file(
    inpath: str,
    shard_root: str,
    chunksize: int,
    n_processes: int,
    hash_func: Encoder,
    prefix_length: int = 4
):
    assert chunksize > 0 and n_processes > 0
    n_lines = int(os.popen(f"wc -l {os.path.abspath(inpath)}").read().strip().split()[0])
    batchsize = n_processes * chunksize
    batch_lines = []
    with open(inpath, encoding="utf-8") as f:
        for line in tqdm(f, desc="Encoding", total=n_lines, leave=False):
            line = line.strip()
            if not line:
                continue
            batch_lines.append(line)
            if len(batch_lines) >= batchsize:
                encoded_lines = hash_func.encode_batch(batch_lines, n_processes, chunksize)
                save_shards(shard_root, encoded_lines, prefix_length)
                batch_lines = []
        if batch_lines:
            encoded_lines = hash_func.encode_batch(batch_lines, n_processes, chunksize)
            save_shards(shard_root, encoded_lines, prefix_length)


def task_encode(
    inputs: Union[str, List[str]],
    shard_root: str,
    chunksize: int,
    n_processes: int,
    hash_func_type: str = "sha1",
    hash_func_input_format: str = "0-9가-힣ㄱ-ㅎㅏ-ㅣa-zA-Z",
    prefix_length: int = 4
):
    if isinstance(inputs, str):
        if os.path.isdir(inputs):
            inputs = sorted(glob(f"{inputs}/*"))
        else:
            inputs = sorted(glob(inputs))
    else:
        inputs = [path for input in inputs for path in glob(input)]
    hash_func = Encoder(hash_func_type, Normalizer(hash_func_input_format))
    for inpath in tqdm(inputs, desc="Encode files", total=len(inputs)):
        encode_a_file(
            inpath=inpath,
            shard_root=shard_root,
            chunksize=chunksize,
            n_processes=n_processes,
            hash_func=hash_func,
            prefix_length=prefix_length,
        )


def task_merge(
    output: str,
    shard_root: str,
    prefix_length: int = 4,
    max_block_size: int = None,
    sort: bool = False
):
    depth = math.ceil(prefix_length / 2)
    wildcard = os.path.sep.join(["*"] * depth)
    shards = glob(f"{shard_root}/{wildcard}.shard")
    os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)

    n_duplicated, n_deduplicated = 0, 0

    block_size, block_index = 0, 0
    if max_block_size is None:
        output_path = output
    else:
        output_path = f"{output}.{block_index}"

    for shard in tqdm(shards, desc="Merge", total=len(shards)):
        # loading shard
        with open(shard, encoding="utf-8") as f:
            lines = [line.strip().split(" ", 1) for line in f]
        n_duplicated += len(lines)

        # deduplicating texts
        unique = defaultdict(lambda: [])
        for code, text in lines:
            unique[code].append(text)
        texts = [texts[0] for texts in unique.values()]
        n_deduplicated += len(texts)

        # blocking
        texts_size = sum(len(text.encode("utf-8")) for text in texts) + len(texts)
        if (max_block_size is not None) and ((block_size + texts_size) > max_block_size):
            block_size, block_index = texts_size, (block_index + 1)
            output_path = f"{output}.{block_index}"
        else:
            block_size += texts_size

        # write deduplicated texts
        with open(output_path, "a", encoding="utf-8") as f:
            for text in texts:
                f.write(f"{text}\n")

        # sort lines in shard
        if sort:
            with open(shard, "w", encoding="utf-8") as f:
                for code, texts in sorted(unique.items()):
                    for text in texts:
                        f.write(f"{code} {text}\n")

    percentage = 100 * n_deduplicated / n_duplicated
    print(f"acquired {percentage:.6}% deduplicated texts")


def task_dedup(
    inputs: Union[str, List[str]],
    output: str,
    shard_root: str,
    chunksize: int,
    n_processes: int = None,
    hash_func_type: str = "sha1",
    hash_func_input_format: str = "0-9가-힣ㄱ-ㅎㅏ-ㅣa-zA-Z",
    max_block_size: Union[int, str] = None,
    sort: bool = False,
    keep: bool = False,
    prefix_length: int = 4
):
    if sort and not keep:
        raise ValueError("`sort` is available only when `keep=True`. use `--keep`")

    if n_processes is None:
        n_processes = cpu_count() - 1

    max_block_size = humanized_to_number(max_block_size)

    if isinstance(inputs, str):
        inputs = [inputs]
    filepaths = []
    for input in inputs:
        if os.path.isdir(input):
            filepaths += glob(f"{input}/*")
        else:
            filepaths.append(input)

    task_encode(
        inputs=filepaths,
        shard_root=shard_root,
        chunksize=chunksize,
        n_processes=n_processes,
        hash_func_type=hash_func_type,
        hash_func_input_format=hash_func_input_format,
        prefix_length=prefix_length,
    )

    task_merge(
        output=output,
        shard_root=shard_root,
        prefix_length=prefix_length,
        max_block_size=max_block_size,
        sort=sort
    )

    if not keep:
        os.system(f"rm -r {os.path.abspath(shard_root)}")


def save_shards(
    shard_root: str,
    encoded_lines: List[str],
    prefix_length: int = 4
):
    assert prefix_length >= 2
    shards = defaultdict(lambda: [])
    for line, code in encoded_lines:
        shards[(code[:prefix_length], code)].append(line)
    for (prefix, code), lines in shards.items():
        shard_path = get_shard_path(shard_root, prefix)
        os.makedirs(os.path.dirname(os.path.abspath(shard_path)), exist_ok=True)
        with open(shard_path, "a", encoding="utf-8") as f:
            for line in lines:
                f.write(f"{code} {line}\n")


def get_shard_path(shard_root: str, code: str):
    """
    Example:
        >>> get_shard_path("path/to", "12345678")
        $'path/to/12/34/56/78.shard'
    """
    n_chars = len(code)
    subpath = "/".join([code[b: b + 2] for b in range(0, n_chars, 2)])
    path = f"{shard_root}/{subpath}.shard"
    return path


def humanized_to_number(max_block_size):
    """
    Examples:
        >>> print(humanized_to_number("10"))      # 10
        >>> print(humanized_to_number("10k"))     # 10240
        >>> print(humanized_to_number("10kb"))    # 10240
        >>> print(humanized_to_number("100.5mb")) # 105381888
        >>> print(humanized_to_number("123.Gb"))  # 132070244352
    """
    if max_block_size is None:
        return None
    try:
        max_block_size = int(max_block_size)
        return max_block_size
    except Exception as err:
        max_block_size = max_block_size.lower()
        if ("k" in max_block_size):
            max_block_size = int(float(max_block_size.split("k")[0]) * (1024))
        elif ("m" in max_block_size):
            max_block_size = int(float(max_block_size.split("m")[0]) * (1024 ** 2))
        elif ("g" in max_block_size):
            max_block_size = int(float(max_block_size.split("g")[0]) * (1024 ** 3))
        else:
            raise ValueError("`max_block_size` examples: 10Kb, 23Mb, 4.5Gb")
        return max_block_size
