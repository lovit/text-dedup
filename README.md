# De-duplicate texts

This package remove duplicating texts as memory-friendly way.
It first encodes texts to sha1 hash code, and then store each text according prefix of the code.
For example, the `sha1` hash code of string `Say hello` is `979e25dd9941e53784ce56e98842f95b8f7fd026` in hex-digit way.

```python
from hashlib import sha1

sha1("Say hello".encode("utf-8")).hexdigest()
# '979e25dd9941e53784ce56e98842f95b8f7fd026'
```

Therefore the string `Say hello` is saved to `path/to/shard/97/9e.shard` with corresponding hash code when length of prefix is set to 4.

```
(head of path/to/shard/97/9e.shard)

979e25dd9941e53784ce56e98842f95b8f7fd026 Say hello
```

After partitioning texts to shards, it removes duplicating texts in each shard (partition file).
And then it merges deduplicated texts.

## Install

```
git clone https://github.com/lovit/text-dedup.git
cd text-dedup
python setup.py install
```

## Usage

If not set `--max_block_size (-b)` it merges all deduplicated texts into a file `path/to/deduplicated.text`.
Or it attaches block index at the end of `output`, for example, `path/to/deduplicated.text.0` and `path/to/deduplicated.text.1`.

Very similar strings have different sha1 hash code value (`Say hello` and `Say hello.`).
To consider only meaningful characters, you can set `--hash_func_input_format (-r)` which is regular expression of input normalizer.
`0-9가-힣ㄱ-ㅎㅏ-ㅣa-zA-Z` means that the white space ` ` and the character `.` are ignored.
And the sha1 inputs of two strings are transformed to `Sayhello`.

It also provides multiprocessing.
Default value is `cpu_count - 1`.
Or you can set it manually with `-p` or `--n_processes` argument.

After merging, the `--shard` directory is removed.
If you want to keep the directory, use `--keep` argument.

**TIPS**: Python file I/O is slow, so applying this package to a lots of small text files is slower than applying it to a few of large text files. Therefore, concatenate some small files into a file and then apply this package to the merged files.

```
text-dedup \
  --inputs path/to/textfile [path/to/or/directory] [path/to/wildcard*] \
  --shard path/to/shard-directory \
  --output path/to/deduplicated.text \
  --max_block_size 10Mb \
  --hash_func_input_format 0-9가-힣ㄱ-ㅎㅏ-ㅣa-zA-Z \
  --prefix_length 4
```

## Performance

Elapsed times in i7-5820

| num lines / num tokens | file size | prefix length | elapsed time | max shard size |
| --- | --- | --- | --- | --- |
| 1,607,769 / 18,923,834 | 209MB (a single text file) | 2 | 01:34 | 1.2MB |
| 1,607,769 / 18,923,834 | 209MB (a single text file) | 4 | 01:50 | 28KB |
| 33,884,047 / 607,593,167 | 6.0GB (166 text files) | 2 | 27:18 | 107MB |
| 33,884,047 / 607,593,167 | 6.0GB (166 text files) | 4 | 49:02 | 208KB |
