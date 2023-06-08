import os, hashlib, sys
PWD = os.getcwd()

def compute_hash(content):
  hasher = hashlib.md5()
  hasher.update(str.encode(content))
  return hasher.hexdigest()


# staleness of file versus source files
def is_stale(derived_file, src_files):
  derived_file = os.path.expanduser(derived_file)
  if not os.path.exists(derived_file):
    return True

  for src_file in src_files:
    if not os.path.exists(os.path.expanduser(src_file)):
      return False

  src_file_times = map(lambda src_file: os.path.getmtime(os.path.expanduser(src_file)), src_files)

  derived_file_time = os.path.getmtime(derived_file)
  for src_file_time in src_file_times:
    if derived_file_time < src_file_time:
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
