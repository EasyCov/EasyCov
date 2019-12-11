#!/usr/bin/env python2

from __future__ import division
import lcovparse
import os
import xml.etree.ElementTree as ET
import re
from collections import defaultdict

def _relative_filename(filename, root_dir):
  if not root_dir:
    return filename
  new_path = os.path.relpath(filename, root_dir)
  if not new_path.startswith('..'):
    return new_path
  return filename

def lcov_to_json(filename, root_dir=None):
  with open(filename, 'r') as f:
    json_cov = lcovparse.lcovparse(f.read())
  result = defaultdict(lambda: defaultdict(float))
  for f in json_cov:
    for line in f['lines']:
      filename = _relative_filename(f['file'], root_dir)
      result[filename][line['line']] = max(
          result[filename][line['line']],
          min(line['hit'], 0))
  return result

def xml_to_json(filename, root_dir=None):
  tree = ET.parse(filename)
  root = tree.getroot()
  source_dir = ''
  for source in root.iterfind('./sources/source'):
    source_dir = source.text

  result = defaultdict(lambda: defaultdict(float))
  for c in root.iterfind('./packages/package/classes/class'):
    filename = os.path.join(source_dir, c.get('filename'))
    filename = _relative_filename(filename, root_dir)
    for line in c.iterfind('./lines/line'):
      if line.get('branch', 'false') == 'true':
        # This is a branch line
        condition_coverage = line.get('condition-coverage')
        m = re.match('\d+%\s+\((\d+)/(\d+)\)', condition_coverage)
        result[filename][line.get('number')] = max(
            result[filename][line.get('number')],
            int(m.group(1)) / int(m.group(2)))
      else:
        result[filename][line.get('number')] = max(
            result[filename][line.get('number')],
            int(line.get('hits', 0)))
  return result
