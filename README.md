# good_cache
`good_cache` is a Python library that caches the output of your functions. If your function has to read large files as its input or if it has to read files in a directory, and optionally some non-file function parameter values such as a str, int, bool, etc. values then `good_cache` can remember the input combination and return the ouput to the caller as long as the input combination has been seen (and cached) by `good_cache` previously.

### Medium.com article that goes into some detail about `good_cache`:
- <https://medium.com/@arunsundaramco/boost-your-python-efficiency-with-good-cache-file-and-directory-based-caching-made-simple-d2218365b3ca>


### GitHub repo:
- <https://github.com/arunsundaram50/good-cache>

### pip command to install it:
```
pip install good_cache
```


### A simple example of how you might use good_cache:
Sum up all the numbers in the given list of files

```
from good_cache import fs_files_cache

@fs_files_cache(files='filenames')
def sum_numbers_in_files(filenames):
    result = 0
    for filename in filenames:
        with open(filename, 'rt') as file:
            numbers = list(map(int, file.readlines()))
            result += sum(numbers)
    return result

total = sum_numbers_in_files(['a.txt', 'b.txt'])
```


### You can evict (remove) a previous cache for a particular parameter(s)
evicted = sum_numbers_in_files.evict(['a.txt', 'b.txt'])
