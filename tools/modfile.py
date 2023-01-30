#!/usr/bin/pypy3 -O
"""
Generate a modified version of an input file.

This will read an input file and output a modified version that is sequences
of copied, inserted, and deleted data. The copied, inserted, and deleted data
have exponentially distributed random lengths with the specified average
lengths. The lengths can be specified with optional 'k' 'm' or 'g' suffixes.

Usage: %(cmd)s <copy-len> [<insert_len>] [<delete_len>] < infile > outfile

Where:
  <copy-len> is the average length of copied data.
  <insert_len> is the average length of inserted data (default: copy_len).
  <delete_len> is the average length of deleted data (default: insert_len).
"""
import os
import random
import sys
from stats1 import Sample


class ModifiedFileData(object):
  """ Modified data from a base file.

  It simulates a stream of data that copies an existing file with
  modifications. The modifications are cycles of copied, inserted, and deleted
  data. The copy, insert, and delete have exponentially distributed random
  lengths with averages of clen, ilen, and dlen respectively.

  It keeps counts of the number of input bytes, output bytes and duplicate
  bytes, as well as stats on the lengths of copied, inserted, and deleted
  sections, which are output to stderr at the end.
  """

  def __init__(self, infile, clen, ilen=None, dlen=None, seed=1):
    if ilen is None:
      ilen = clen
    if dlen is None:
      dlen = clen
    self.dat = infile
    self.ins = open('/dev/urandom','rb')
    self.clen = clen
    self.ilen = ilen
    self.dlen = dlen
    self.seed = seed
    # exponential distribution lambda parameters for clen/ilen/dlen.
    self.clambd = 1.0/clen
    self.ilambd = ilen and 1.0/ilen
    self.dlambd = dlen and 1.0/dlen
    self.reset()

  def reset(self):
    # Initialize the random generator.
    self.mod = random.Random(self.seed)
    self.cpystats = Sample()
    self.insstats = Sample()
    self.delstats = Sample()
    self.initcycle()

  def initcycle(self):
    # Note we always copy at least one byte.
    self.cpy_n = max(1, int(self.mod.expovariate(self.clambd)))
    self.ins_n = self.ilen and int(self.mod.expovariate(self.ilambd))
    self.del_n = self.dlen and int(self.mod.expovariate(self.dlambd))

  def getdata(self):
    # Output copied data.
    data = self.dat.read(self.cpy_n)
    if data:
      self.cpystats.add(len(data))
      # Output inserted data.
      data += self.ins.read(self.ins_n)
      self.insstats.add(self.ins_n)
      # Skip over deleted data.
      skip = self.dat.read(self.del_n)
      self.delstats.add(len(skip))
      # Setup next cycle.
      self.initcycle()
    return data

  @property
  def inp_c(self):
    return self.cpystats.sum + self.delstats.sum

  @property
  def tot_c(self):
    return self.cpystats.sum + self.insstats.sum

  @property
  def dup_c(self):
    return self.cpystats.sum

  def __repr__(self):
    return "Data(<file>, clen=%s, ilen=%s, dlen=%s, seed=%s)" % (
        self.clen, self.ilen, self.dlen, self.seed)

  def __str__(self):
    return "%r: inp=%d tot=%d dup=%d(%4.1f%%)\n  cpy: %s\n  ins: %s\n  del: %s" % (
        self, self.inp_c, self.tot_c, self.dup_c, 100.0 * self.dup_c / self.tot_c,
        self.cpystats, self.insstats, self.delstats)


def usage(code, error=None, *args):
  if error:
    print(error % args)
  print(__doc__ % dict(cmd=os.path.basename(sys.argv[0])))
  sys.exit(code)


def getarg(n, default=None):
  return sys.argv[n] if len(sys.argv) > n else default


def getlen(arg):
  if arg[-1] in 'kK':
    return int(arg[:-1]) * 1024
  elif arg[-1] in 'mM':
    return int(arg[:-1]) * 1024 * 1024
  elif arg[-1] in 'gG':
    return int(arg[:-1]) * 1024 * 1024 * 1024
  return int(arg)

if __name__ == '__main__':
  arg1 = getarg(1)
  if arg1 in ("-?", "-h", "--help", None):
    usage(0)
  arg2=getarg(2, arg1)
  arg3=getarg(3, arg2)
  clen=getlen(arg1)
  ilen=getlen(arg2)
  dlen=getlen(arg3)
  infile = sys.stdin.buffer
  outfile = sys.stdout.buffer
  gen = ModifiedFileData(infile, clen, ilen, dlen)
  data = gen.getdata()
  while data:
    outfile.write(data)
    data = gen.getdata()
  sys.stderr.write(str(gen))
