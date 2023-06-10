#!/usr/bin/env python3


import os, hashlib, sys, datetime, time
PWD = os.getcwd()

def compute_hash(content):
  hasher = hashlib.md5()
  hasher.update(str.encode(content))
  return hasher.hexdigest()


# staleness of file versus source files
def is_stale(derived_file, src_files):

  def dt2str(dt):
    return datetime.datetime.fromtimestamp(dt).strftime('%Y-%m-%d %H:%M:%S')

  def t2str(ts):
    return time.strftime("%Y-%m-%d %H:%M:%S", ts)

  derived_file = os.path.expanduser(derived_file)
  if not os.path.exists(derived_file):
    return True

  for src_file in src_files: # This could be considered an exception condition
    if not os.path.exists(os.path.expanduser(src_file)):
      raise ValueError(f'File {src_file} does not exist')

  derived_file_time = time.localtime(os.path.getmtime(derived_file))
  for src_file in src_files:
    src_file_time = time.localtime(os.path.getmtime(src_file))
    if src_file_time > derived_file_time:
      return True

  return False


def ensure_dir(dir):
  dir = os.path.expanduser(dir)
  if not os.path.exists(dir):
    os.makedirs(dir)
  return dir


def ensure_parent(file_path):
  dir = os.path.dirname(file_path)
  return ensure_dir(dir)


def log(*args, **kwargs):
  frame = sys._getframe(1)
  if frame.f_code.co_filename.startswith(PWD):
    rel_cwd = frame.f_code.co_filename[len(PWD):]
  else:
    rel_cwd = frame.f_code.co_filename
  print(f'File "{rel_cwd}", line {frame.f_lineno}', end=': ')
  print(*args, **kwargs)
  sys.stdout.flush()


if __name__ == "__main__":
  der_file = "/tmp/cache/my_filter/5fb4935e8cc63f9e578089a5f1b8b184.pickle"
  src_files = ["/tmp/test.parquet"]

  b = is_stale(der_file, src_files)
  print(b)
