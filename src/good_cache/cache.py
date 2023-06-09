#!/usr/bin/env python3

import os, pickle, tempfile, threading, timeit, traceback, shutil
from . import utils
# import utils # for local testing
from send2trash import send2trash
from inspect import getfullargspec
import pandas as pd


def find_storage(file_with_no_ext):
  for ext in ['parquet', 'pickle']:
    if os.path.exists(f'{file_with_no_ext}.{ext}'):
      return ext, f'{file_with_no_ext}.{ext}'
  return None, None


def get_storage(obj, file_with_no_ext):
  if isinstance(obj, pd.DataFrame):
    return "parquet", f'{file_with_no_ext}.parquet'
  return "pickle", f'{file_with_no_ext}.pickle'


def save_object(obj, filename):
  if filename.endswith(".parquet"):
    obj.to_parquet(filename)
  else:
    with open_and_lock_cache_file(filename, 'wb') as f:
      pickle.dump(obj, f)


def read_object(filename):
  _, extension = os.path.splitext(filename)

  if extension == '.parquet':
    return pd.read_parquet(filename)
  else:
    with open_and_lock_cache_file(filename, 'rb') as f:
      return pickle.load(f)


cache_file_locks = {}

def get_cache_file_lock(filename):
  # Get or create a lock for the given filename
  with cache_file_locks.setdefault(filename, threading.Lock()):
    # Return the lock associated with the filename
    return cache_file_locks[filename]


def open_and_lock_cache_file(filename, mode):
  with get_cache_file_lock(filename):
    file_handle = open(filename, mode)
    return file_handle


def default_f_args_to_str(*dec_args, **dec_kwargs):
  args_as_str = ", ".join([repr(arg) for arg in dec_args] +
    [f"{key}={repr(value)}" for key, value in dec_kwargs.items()])
  return args_as_str


"""
Usecase: when the output is dependant on muliple files and any parameters passed to the function.
Output is kept in file system and is reused if the files and if the paramerers were used previously
"""
def fs_files_cache(*dec_args, **dec_kwargs):
  files_arg_name = dec_kwargs['files'] if 'files' in dec_kwargs else None
  shorten_cache_file = dec_kwargs['shorten_cache_file'] if 'shorten_cache_file' in dec_kwargs else True
  f_args_to_str = dec_kwargs['args_to_str'] if 'args_to_str' in dec_kwargs else default_f_args_to_str
  f_is_content_cacheable = dec_kwargs['is_content_cacheable'] if 'is_content_cacheable' in dec_kwargs else lambda f: True

  def inner(f):
    argspec = getfullargspec(f)
    if files_arg_name:
      files_arg_pos = argspec.args.index(files_arg_name)
    else:
      files_arg_pos = None

    def get_cache_file(*args, **kwargs):
      if files_arg_pos!=None:
        files_arg_val = args[files_arg_pos]
      else:
        files_arg_val = ''
      args_as_str = f_args_to_str(*args, **kwargs)
      if shorten_cache_file:
        dyn_part = utils.compute_hash(args_as_str)
      else:
        dyn_part = args_as_str
      file_stem = f'{tempfile.gettempdir()}/cache/{f.__name__}/{dyn_part}'
      storage_type, cache_file = find_storage(file_stem)
      return storage_type, cache_file, files_arg_val, file_stem

    def evict(*args, **kwargs):
      _, cache_file, *_ = get_cache_file(*args, **kwargs)
      if os.path.exists(cache_file):
        try:
          send2trash(cache_file)
          return True
        except:
          os.unlink(cache_file)
          return True
      return False

    def wrapper(*args, **kwargs):
      storage_type, cache_file, files_arg_val, file_stem = get_cache_file(*args, **kwargs)

      # recreate stale file
      ret = None
      if storage_type == None or utils.is_stale(cache_file, files_arg_val):
        try:
          ret = f(*args)
          if not f_is_content_cacheable(ret):
            return ret
          storage_type, cache_file = get_storage(ret, file_stem)
          utils.ensure_parent(cache_file)
          save_object(ret, cache_file)
        except:
          if cache_file!=None and os.path.exists(cache_file):
            send2trash(cache_file)
          raise ValueError(f"Error invoking {f.__name__}")

      # load file
      try:
        ret = read_object(cache_file)
      except:
        utils.log(traceback.format_exc(0))
        if cache_file!=None and os.path.exists(cache_file):
          send2trash(cache_file)
        raise ValueError(f"Error reading previous result of {f.__name__}")

      return ret

    wrapper.get_cache_file = get_cache_file
    wrapper.evict = evict
    return wrapper
  return inner


"""
Usecase: when the output is dependant on dir and the optional parameters passed to the function.
Output is kept in file system and reused if the dir was not modified and if the paramerers were used previously
"""
def fs_dir_cache(*dec_args, **dec_kwargs):
  dir_arg_name = dec_kwargs['dir'] if 'dir' in dec_kwargs else None
  shorten_cache_file = dec_kwargs['shorten_cache_file'] if 'shorten_cache_file' in dec_kwargs else True
  f_args_to_str = dec_kwargs['args_to_str'] if 'args_to_str' in dec_kwargs else lambda f: ''
  f_is_content_cacheable = dec_kwargs['is_content_cacheable'] if 'is_content_cacheable' in dec_kwargs else lambda f: True

  def inner(f):
    argspec = getfullargspec(f)
    dir_arg_pos = argspec.args.index(dir_arg_name)

    def wrapper(*args, **kwargs):
      dir_arg_val = args[dir_arg_pos]
      arg_str = f_args_to_str(*args, **kwargs)
      dyn_part = f'{dir_arg_val}/{arg_str}'
      if shorten_cache_file:
        dyn_part = utils.compute_hash(dyn_part)
      cache_file = f'{tempfile.gettempdir()}/cache/{f.__name__}/{dyn_part}.pickle'

      # recreate stale file
      ret = None
      if utils.is_stale(cache_file, [dir_arg_val]):
        utils.ensure_parent(cache_file)
        try:
          ret = f(*args)
          if not f_is_content_cacheable(ret):
            return ret
          with open_and_lock_cache_file(cache_file, 'wb') as fp:
            pickle.dump(ret, fp)
        except:
          if os.path.exists(cache_file):
            send2trash(cache_file)
          raise ValueError(f"Error invoking {f.__name__}")

      # load file
      try:
        with open_and_lock_cache_file(cache_file, 'rb') as fp:
          ret = pickle.load(fp)
      except:
        utils.log(traceback.format_exc(0))
        if os.path.exists(cache_file):
          send2trash(cache_file)
        raise ValueError(f"Error reading previous result of {f.__name__}")

      return ret

    return wrapper
  return inner


def evict_all_cache_for(func_name):
  dir = f'{tempfile.gettempdir()}/cache/{func_name}'
  if os.path.exists(dir):
    shutil.rmtree(dir)


if __name__ == "__main__1":
  ## Example where input is a list of files
  @fs_files_cache(files='filenames')
  def my_large_computation(filenames):
    print(f'my_large_computation(): summing {len(filenames)} files...')
    sum = 0
    for filename in filenames:
      with open(filename, 'rt') as fp:
        lines = fp.readlines()
        numbers = list(map(lambda line: int(line), lines))
        for number in numbers:
          sum += number
    return sum

  def create_and_get_input_files():
    filenames = []
    for i in range(0, 100000):
      filename = f'{tempfile.gettempdir()}/f_{i}.txt'
      if not os.path.exists(filename):
        with open(filename, 'wt') as fp:
          fp.write(f'{i*10}')
      filenames.append(filename)
    return filenames

  # Deleting the cache directory for the given function.
  evict_all_cache_for('my_large_computation')
  filenames = create_and_get_input_files()

  print("\nPerforming summation without using cache...")
  start = timeit.default_timer()
  sum = my_large_computation(filenames)
  end = timeit.default_timer()
  t1 = end-start
  print(f'{sum=}, took {t1} without using cache')

  print("\nPerforming summation while using cache...")
  start = timeit.default_timer()
  sum = my_large_computation(filenames)
  end = timeit.default_timer()
  t2 = end-start
  print(f'{sum=}, took {t2} while using cache')

  print(f'\nCaching was {t1/t2} times faster')


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

  file_a = '/tmp/a.txt'
  file_b = '/tmp/b.txt'
  if not os.path.exists(file_a):
    with open(file_a, 'wt') as fp:
      print(1, file=fp)
      print(2, file=fp)
      print(3, file=fp)

  if not os.path.exists(file_b):
    with open(file_b, 'wt') as fp:
      print(1, file=fp)

  storage_type, cache_file, *_ = only_params_with_files_custom.get_cache_file([file_a, file_b], 1, 25)
  print(f'{storage_type=}, {cache_file=}')
  # only_params_with_files_custom.evict([file_a, file_b], 1, 25)
  print(only_params_with_files_custom([file_a, file_b], 1, 25))

 