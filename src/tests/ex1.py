#!/usr/bin/env python3

USE_LOCAL_GOOD_CACHE = True
if USE_LOCAL_GOOD_CACHE:
  import sys
  sys.path = [p for p in sys.path if not p.endswith('site-packages/good_cache')]
  sys.path.insert(0, "/home/asundaram/apps/good-cache/src")

from good_cache.cache import fs_files_cache
import pandas as pd, os


if __name__ == "__main__1":
  ## Example where input has no filenames, but just parameters, and uses 
  ## custom implementation of args_to_str

  def my_args_to_str(*args, **kwargs):
    a = [repr(arg) for arg in args]
    b = [f"{key}={repr(value)}" for key, value in kwargs.items()]
    return ", ".join(a + b)

  @fs_files_cache(files="filenames", args_to_str=my_args_to_str)
  def only_params_with_files_custom(filenames, a, b):
    print('processing a+b')
    return str(a+b)+str(filenames)

  print(only_params_with_files_custom(['a.txt, b.txt'], 1, 25))


if __name__ == "__main__2":
  ## Example where input has no filenames, but just parameters

  @fs_files_cache()
  def only_params(a, b):
    print('processing a+b')
    return a+b

  print(only_params(1, 24))


if __name__ == "__main__3":
  ## Example where input has filenames, and parameters, but uses default 
  ## implementation of args_to_str

  @fs_files_cache(files='filenames')
  def only_params_with_files_arguments(filenames, a, b):
    print('processing a+b')
    return a+b

  print(only_params_with_files_arguments(['a.txt', 'b.txt'], 1, 24))


if __name__ == "__main__4":
  ## Example where input has no filenames, and parameters, and uses 
  ## custom implementation of args_to_str

  def my_args_to_str(*args, **kwargs):
    return ", ".join([repr(arg) for arg in args])

  @fs_files_cache(args_to_str=my_args_to_str)
  def only_params_custom(a, b):
    print('processing a+b')
    return a+b

  print(only_params_custom(1, 25))


if __name__ == "__main__":

  @fs_files_cache(files='parquet_filenames')
  def my_filter(parquet_filenames, odd_or_even):
    df = pd.read_parquet(parquet_filenames[0])
    print(f"\t\tmy_filter({odd_or_even=})")
    if odd_or_even == 'odd':
      return df[df['numbers']%2 != 0]
    else:
      return df[df['numbers']%2 == 0]

  PARQUET_FILENAME = os.path.expanduser('/tmp/test.parquet')
  if not os.path.exists(PARQUET_FILENAME):
    df = pd.DataFrame([1, 2, 3, 4, 5, 6], columns=['numbers'])
    df.to_parquet(PARQUET_FILENAME)

  df_odd = my_filter([PARQUET_FILENAME], 'odd')
  df_even = my_filter([PARQUET_FILENAME], 'even')

  print(df_odd)
  print(df_even)
