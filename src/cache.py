#!/usr/bin/env python3

import os, pickle, utils, tempfile, threading, timeit, traceback, shutil
from send2trash import send2trash
from inspect import getfullargspec

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


"""
Usecase: when the output is dependant on the modified-time of muliple files [specified in the input]
Output is kept in file system
"""
def fs_files_cache(*dec_args, **dec_kwargs):
  files_arg_name = dec_kwargs['files'] if 'files' in dec_kwargs else None
  
  def f_args_to_str(files):
    return ';'.join(files)

  def inner(f):
    argspec = getfullargspec(f)
    files_arg_pos = argspec.args.index(files_arg_name)
    def wrapper(*args, **kwargs):
      files_arg_val = args[files_arg_pos]
      arg_as_str = f_args_to_str(files_arg_val)
      arg_hash = utils.compute_hash(arg_as_str)
      cache_file = f'{tempfile.gettempdir()}/cache/{f.__name__}/{arg_hash}.pickle'

      # recreate stale file
      ret = None
      if utils.is_stale(cache_file, files_arg_val):
        utils.ensure_parent(cache_file)
        try:
          ret = f(*args)
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


"""
Usecase: when the output is dependant on the modified-time of the dir [specified in the input].
Output is kept in file system
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
  shutil.rmtree(dir)


if __name__ == "__main__":
  
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
