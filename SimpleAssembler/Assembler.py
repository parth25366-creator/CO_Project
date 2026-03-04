import sys

REGISTER_MAP = {
    **{f"x{i}": format(i, "05b") for i in range(32)},
    "zero": format(0, "05b"), "ra": format(1, "05b"), "sp": format(2, "05b"),
    "gp": format(3, "05b"), "tp": format(4, "05b"),
    "t0": format(5, "05b"), "t1": format(6, "05b"), "t2": format(7, "05b"),
    "s0": format(8, "05b"), "fp": format(8, "05b"), "s1": format(9, "05b"),
    "a0": format(10, "05b"), "a1": format(11, "05b"), "a2": format(12, "05b"),
    "a3": format(13, "05b"), "a4": format(14, "05b"), "a5": format(15, "05b"),
    "a6": format(16, "05b"), "a7": format(17, "05b"),
    "s2": format(18, "05b"), "s3": format(19, "05b"), "s4": format(20, "05b"),
    "s5": format(21, "05b"), "s6": format(22, "05b"), "s7": format(23, "05b"),
    "s8": format(24, "05b"), "s9": format(25, "05b"), "s10": format(26, "05b"),
    "s11": format(27, "05b"),
    "t3": format(28, "05b"), "t4": format(29, "05b"),
    "t5": format(30, "05b"), "t6": format(31, "05b"),
}

OPCODE_TABLE = {
    "add":  {"type": "R", "opcode": "0110011", "funct3": "000", "funct7": "0000000"},
    "sub":  {"type": "R", "opcode": "0110011", "funct3": "000", "funct7": "0100000"},
    "slt":  {"type": "R", "opcode": "0110011", "funct3": "010", "funct7": "0000000"},
    "srl":  {"type": "R", "opcode": "0110011", "funct3": "101", "funct7": "0000000"},
    "addi": {"type": "I", "opcode": "0010011", "funct3": "000"},
    "lw":   {"type": "I", "opcode": "0000011", "funct3": "010"},
    "jalr": {"type": "I", "opcode": "1100111", "funct3": "000"},
    "sw":   {"type": "S", "opcode": "0100011", "funct3": "010"},
    "beq":  {"type": "B", "opcode": "1100011", "funct3": "000"},
    "bne":  {"type": "B", "opcode": "1100011", "funct3": "001"},
    "lui":  {"type": "U", "opcode": "0110111"},
    "auipc":{"type": "U", "opcode": "0010111"},
    "jal":  {"type": "J", "opcode": "1101111"},
}

def to_binary(a, b):
    a = int(a)
    if a < 0:
        a = (1 << b) + a
    return format(a, f"0{b}b")

def clean_line(a):
    a = a.split("#")[0]
    return a.strip()

def first_pass(a):
    s = {}
    p = 0
    for l in a:
        if ":" in l:
            x, y = l.split(":")
            s[x.strip()] = p
            if y.strip() != "":
                p += 4
        else:
            p += 4
    return s

def encode_R(a):
    i = OPCODE_TABLE[a[0]]
    d = REGISTER_MAP[a[1]]
    s1 = REGISTER_MAP[a[2]]
    s2 = REGISTER_MAP[a[3]]
    return i["funct7"] + s2 + s1 + i["funct3"] + d + i["opcode"]

def encode_I(a):
    i = OPCODE_TABLE[a[0]]
    d = REGISTER_MAP[a[1]]
    if a[0] == "lw":
        im, s1 = a[2].split("(")
        s1 = REGISTER_MAP[s1.replace(")", "")]
    else:
        s1 = REGISTER_MAP[a[2]]
        im = a[3]
    b = to_binary(im, 12)
    return b + s1 + i["funct3"] + d + i["opcode"]

def encode_S(a):
    i = OPCODE_TABLE[a[0]]
    s2 = REGISTER_MAP[a[1]]
    im, s1 = a[2].split("(")
    s1 = REGISTER_MAP[s1.replace(")", "")]
    b = to_binary(im, 12)
    return b[:7] + s2 + s1 + i["funct3"] + b[7:] + i["opcode"]

def encode_B(a, p, s):
    i = OPCODE_TABLE[a[0]]
    s1 = REGISTER_MAP[a[1]]
    s2 = REGISTER_MAP[a[2]]
    o = s[a[3]] - p if a[3] in s else int(a[3])
    b = to_binary(o, 13)
    return b[0] + b[2:8] + s2 + s1 + i["funct3"] + b[8:12] + b[1] + i["opcode"]

def encode_U(a):
    i = OPCODE_TABLE[a[0]]
    d = REGISTER_MAP[a[1]]
    b = to_binary(a[2], 20)
    return b + d + i["opcode"]

def encode_J(a, p, s):
    i = OPCODE_TABLE[a[0]]
    d = REGISTER_MAP[a[1]]
    o = s[a[2]] - p if a[2] in s else int(a[2])
    b = to_binary(o, 21)
    return b[0] + b[10:20] + b[9] + b[1:9] + d + i["opcode"]

def second_pass(a, s):
    p = 0
    o = []
    for l in a:
        try:
            if ":" in l:
                if l.strip().endswith(":"):
                    continue
                else:
                    l = l.split(":")[1].strip()
            l = l.replace(",", " ")
            x = l.split()
            if x[0] not in OPCODE_TABLE:
                print("Error"); sys.exit()
            t = OPCODE_TABLE[x[0]]["type"]
            if t == "R":
                b = encode_R(x)
            elif t == "I":
                b = encode_I(x)
            elif t == "S":
                b = encode_S(x)
            elif t == "B":
                b = encode_B(x, p, s)
            elif t == "U":
                b = encode_U(x)
            elif t == "J":
                b = encode_J(x, p, s)
            o.append(b)
            p += 4
        except:
            print("Error"); sys.exit()
    return o

def main():
    try:
        i = sys.argv[1]
        o = sys.argv[2]
        with open(i, "r") as f:
            r = f.readlines()
        a = []
        for l in r:
            c = clean_line(l)
            if c:
                a.append(c)
        s = first_pass(a)
        b = second_pass(a, s)
        with open(o, "w") as f:
            f.write("\n".join(b))
    except:
        print("Error"); sys.exit()

if __name__ == "__main__":
    main()
