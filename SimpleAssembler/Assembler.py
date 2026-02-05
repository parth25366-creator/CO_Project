import sys

REG={
"x0":"00000","zero":"00000",
"x1":"00001","ra":"00001",
"x2":"00010","sp":"00010",
"x3":"00011","gp":"00011",
"x4":"00100","tp":"00100",
"x5":"00101","t0":"00101",
"x6":"00110","t1":"00110",
"x7":"00111","t2":"00111",
"x8":"01000","s0":"01000","fp":"01000",
"x9":"01001","s1":"01001",
"x10":"01010","a0":"01010",
"x11":"01011","a1":"01011",
"x12":"01100","a2":"01100",
"x13":"01101","a3":"01101",
"x14":"01110","a4":"01110",
"x15":"01111","a5":"01111",
"x16":"10000","a6":"10000",
"x17":"10001","a7":"10001",
"x18":"10010","s2":"10010",
"x19":"10011","s3":"10011",
"x20":"10100","s4":"10100",
"x21":"10101","s5":"10101",
"x22":"10110","s6":"10110",
"x23":"10111","s7":"10111",
"x24":"11000","s8":"11000",
"x25":"11001","s9":"11001",
"x26":"11010","s10":"11010",
"x27":"11011","s11":"11011",
"x28":"11100","t3":"11100",
"x29":"11101","t4":"11101",
"x30":"11110","t5":"11110",
"x31":"11111","t6":"11111"
}

def error(msg,line):
    print(f"Error at line {line+1}: {msg}")
    sys.exit(0)

def to_bin(n,bits):
    if n<0:n=(1<<bits)+n
    return format(n,f'0{bits}b')

# ---------- R TYPE ----------
R_TYPE={
"add":("000","0000000"),
"sub":("000","0100000"),
"and":("111","0000000"),
"or":("110","0000000"),
"slt":("010","0000000"),
"srl":("101","0000000")
}

def encode_r(op,rd,rs1,rs2):
    f3,f7=R_TYPE[op]
    return f7+REG[rs2]+REG[rs1]+f3+REG[rd]+"0110011"

# ---------- I TYPE ----------
def encode_i(op,rd,rs1,imm):
    OPC={"addi":"0010011","lw":"0000011","jalr":"1100111"}
    F3={"addi":"000","lw":"010","jalr":"000"}
    return to_bin(int(imm),12)+REG[rs1]+F3[op]+REG[rd]+OPC[op]

# ---------- S TYPE ----------
def encode_sw(rs1,rs2,imm):
    imm=to_bin(int(imm),12)
    return imm[:7]+REG[rs2]+REG[rs1]+"010"+imm[7:]+"0100011"

# ---------- B TYPE ----------
def encode_b(op,rs1,rs2,offset):
    F3={"beq":"000","bne":"001","blt":"100","bge":"101"}
    offset//=2
    imm=to_bin(offset,13)
    return imm[0]+imm[2:8]+REG[rs2]+REG[rs1]+F3[op]+imm[8:12]+imm[1]+"1100011"

# ---------- J TYPE ----------
def encode_jal(rd,offset):
    offset//=2
    imm=to_bin(offset,21)
    return imm[0]+imm[10:20]+imm[9]+imm[1:9]+REG[rd]+"1101111"

# ---------- PREPROCESS ----------
def preprocess(lines):
    code=[]
    labels={}
    pc=0

    for i,l in enumerate(lines):
        l=l.strip()
        if not l:continue

        if ":" in l:
            lab,rest=l.split(":",1)
            labels[lab.strip()]=pc
            l=rest.strip()
            if not l:continue

        code.append((i,l))
        pc+=4

    return code,labels

def tokenize(line):
    for c in ",()":line=line.replace(c," ")
    return line.split()

# ---------- ASSEMBLE ----------
def assemble(code,labels):
    out=[]
    pc=0
    halt=False

    for i,l in code:
        p=tokenize(l)
        op=p[0]

        if op in R_TYPE:
            out.append(encode_r(op,p[1],p[2],p[3]))

        elif op in ["addi","jalr"]:
            out.append(encode_i(op,p[1],p[2],p[3]))

        elif op=="lw":
            out.append(encode_i("lw",p[1],p[3],p[2]))

        elif op=="sw":
            out.append(encode_sw(p[3],p[1],p[2]))

        elif op in ["beq","bne","blt","bge"]:
            if p[3] not in labels:error("Undefined label",i)
            off=labels[p[3]]-pc
            out.append(encode_b(op,p[1],p[2],off))

            if p[1]=="zero" and p[2]=="zero" and off==0:
                halt=True
                if pc!=(len(code)-1)*4:
                    error("Virtual Halt not last instruction",i)

        elif op=="jal":
            if p[2] not in labels:error("Undefined label",i)
            off=labels[p[2]]-pc
            out.append(encode_jal(p[1],off))

        else:
            error("Invalid syntax",i)

        pc+=4

    if not halt:error("Missing Virtual Halt",code[-1][0])
    return out

# ---------- MAIN ----------
def main():
    lines=sys.stdin.read().splitlines()
    if not lines:return

    code,labels=preprocess(lines)
    machine=assemble(code,labels)

    sys.stdout.write("\n".join(machine))

if __name__=="__main__":
    main()
