import sys
from datetime import datetime

# You're welcome to use this code but please leave my copyright notice and the
# citation directing others to my GitHub repository for this code in place.
#
# Copyright 2021, Chris Larsen

dt = datetime.today().strftime("%m/%d/%Y %I:%M:%S %p")

def usage(msg):
  print(msg, file=sys.stderr)
  print("Usage: %s [-o | --overflow] <number of bits>" % (sys.argv[0]), file=sys.stderr)
  sys.exit(1)

Overflow = False
CountNotFound = True

if len(sys.argv) == 1:
  usage("ERROR: No arguments given")
elif len(sys.argv) < 4:
  for arg in sys.argv[1:]:
    if arg == "--overflow" or arg == "-o":
      Overflow = True
    else:
      try:
        count = int(arg)
        CountNotFound = False
      except ValueError:
        usage("ERROR: Input value is not a valid integer: %s" % (arg))

  if CountNotFound:
    usage("ERROR: Missing count argument")
  elif count <= 0:
    usage("ERROR: Number of bits must be a positive number: %d" % (count))
else:
  usage("ERROR: Too many command line arguments")

#Header info
print(
'''
`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Copyright: Chris Larsen, 2021
// Engineer: Chris Larsen
//
// Create Date: %s
// Design Name:
// Module Name: padder%d
// Project Name:
// Target Devices:
// Tool Versions:
// Description: %d-bit Integer Prefix Adder with Carry In/Carry Out
//
//       This adder was generated by a Python script written by Chris Larsen.
//       The adders generated by the Python script are all prefix adders.
//       Since this code was machine generated, in general you shouldn't be
//       editing this code by hand.
//
//       If bugs are found in the script I (Chris Larsen) would ask that you
//       send your bug fixes, and or other improvements, back so I can include
//       them in the git repository for the padder.py script.
//
//       Prefix adders are described in the book "Digital Design and Computer
//       Architecture, Second Edition" by David Money Harris & Sarah L. Harris.
//       To write this code I started by studying their diagram of a 16-bit
//       prefix adder, and extrapolated it to 32-bits, etc. I'm not an expert
//       in prefix adders. So if you have questions, please don't ask me;
//       please buy their fine book! :-)
//
//       The Python script used to generate this code can be downloaded from
//       https://github.com/crlarsen/padder/
//
// Dependencies: None
//
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
//
//////////////////////////////////////////////////////////////////////////////////

'''[1:] % (dt, count, count))

print(
'''
module padder%d(A, B, Cin, S, Cout%s);
  localparam N = %d;
  input [N-1:0] A, B;
  input Cin;
  output [N-1:0] S;
  output Cout;
%s
  // P[i] is an alias for Pi:i, likewise G[i] is an alias for Gi:i
  wire [N-2:-1] P, G;
'''[1:] % (count, (", OVF" if Overflow else ""), count, ("  output OVF;\n" if Overflow else "")))

if count == 1:
  print(
'''
  assign P[-1] = 1'b0;
  assign G[-1] = Cin;
'''[1:])
else:
  print(
'''
  assign P = {A[N-2:0] | B[N-2:0], 1'b0};
  assign G = {A[N-2:0] & B[N-2:0], Cin};
'''[1:])
#Header info

# Compute the next node in the net.
def node(i, j, l, r):
  if i == j:
    p1Input = "P[%d]" % (i)
    g1Input = "G[%d]" % (i)
  else:
    p1Input = "\\P%d:%d " % (i, j)
    g1Input = "\\G%d:%d " % (i, j)

  if (l == r):
    p2Input = "P[%d]" % (l)
    g2Input = "G[%d]" % (l)
  else:
    p2Input = "\\P%d:%d " % (l, r)
    g2Input = "\\G%d:%d " % (l, r)

  pOutput = "\\P%d:%d " % (i, r)
  gOutput = "\\G%d:%d " % (i, r)

  if r == -1:
    # We don't need to compute \Pi:-1 because it will never be used.
    # This keeps the Verilog compiler from complaining that we have
    # outputs not connected to inputs.
    print("  wire %s;\n" % (gOutput))
    #print("  Gij \\%d:%d (%s, %s, %s, %s);" % (i, r, p1Input, g1Input, g2Input, gOutput))
    print("  assign %s = %s | (%s  & %s );\n" % (gOutput, g1Input, p1Input, g2Input))
  else:
    print("  wire %s, %s;\n" % (pOutput, gOutput))
    print("  PijGij \\%d:%d (%s, %s, %s, %s, %s, %s);\n" % (i, r, p1Input, p2Input, g1Input, g2Input, pOutput, gOutput))
    #print("  assign %s = %s | (%s  & %s );" % (gOutput, g1Input, p1Input, g2Input))
    #print("  assign %s = %s & %s;\n" % (pOutput, p1Input, p2Input)

masks = []

for i in range(-1, count-1):
  masks.append([i, i]) # Push new node onto stack.

  # Merge and print top 2 stack items as long as the last N bits of i
  # are equal to 2**N - 2.
  m, v = 1, 0 # Start with N = 1
  while (i & m) == v:
    [i, j] = masks.pop()
    [l, r] = masks[-1]
    node(i, j, l, r)
    masks[-1][0] = i # Merge the 2 top nodes.
    m, v = ((m << 1) | 1), ((v << 1) | 2) # N = N + 1

  # Perform the rest of the work needed to compute Gi:-1
  [i, j] = masks[-1]
  for k in range(len(masks)-2, -1, -1):
    [l, r] = masks[k]
    node(i, j, l, r)
    j = r

  # Use Gi:-1 to propagate carry to compute bit i+1 of the sum.
  if i == -1:
    #print("  Sum s%d(G[%d], A[%d], B[%d], S[%d]);" % (i+1, i, i+1, i+1, i+1));
    print("  assign S[%d] = A[%d] ^ G[%d];\n" % (i+1, i+1, i));
  else:
    #print("  Sum s%d(\\G%d:-1 , A[%d], B[%d], S[%d]);" % (i+1, i, i+1, i+1, i+1));
    print("  assign S[%d] = A[%d] ^ \\G%d:-1 ;\n" % (i+1, i+1, i));

# Compute Cout
if count == 1:
  print("  assign Cout = (G[%d] & A[%d]) | (\\G%d:-1 & B[%d]) | (A[%d] & B[%d]);\n" % (count-2, count-1, count-2, count-1, count-1, count-1))
else:
  print("  assign Cout = (\\G%d:-1 & A[%d]) | (\\G%d:-1 & B[%d]) | (A[%d] & B[%d]);\n" % (count-2, count-1, count-2, count-1, count-1, count-1))

# If needed, compute the overflow flag
if Overflow:
  print("  assign OVF = Cout ^ %s;\n" % (("\\G%d:-1 " % (count-2)) if count > 1 else "G[-1]"));

# End the module
print("endmodule");
