import sys
import shlex
import argparse

ar = shlex.split(' '.join(sys.argv[1:]))
print(ar)
