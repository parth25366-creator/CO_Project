import sys

# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────

def sign_extend(val, bits):
    """Interpret val as a signed bits-wide integer."""
    if val & (1 << (bits - 1)):
        val -= (1 << bits)
    return val

def to_bin32(val):
    """Unsigned 32-bit binary string with 0b prefix."""
    return '0b' + format(val & 0xFFFFFFFF, '032b')


# ──────────────────────────────────────────────
#  Simulator
# ──────────────────────────────────────────────

class Simulator:
    # Memory map
    PROG_START  = 0x00000000;  PROG_END  = 0x000000FF
    STACK_START = 0x00000100;  STACK_END = 0x0000017F
    DATA_START  = 0x00010000;  DATA_END  = 0x0001007F

    def __init__(self):
        self.regs    = [0] * 32
        self.regs[2] = 0x0000017C   # sp initialised to 0x17C
        self.memory  = {}           # sparse: addr -> uint32
        self.pc      = 0
        self.program = []           # list of 32-char binary strings
        self.output  = []           # lines written to trace file

    # ── Loading ──────────────────────────────

    def load(self, filename):
        with open(filename, 'r') as f:
            lines = [l.strip() for l in f if l.strip()]
        self.program = lines
        for i, line in enumerate(lines):
            self.memory[i * 4] = int(line, 2)

    # ── Register access ───────────────────────

    def rreg(self, r):
        """Read register (x0 always 0)."""
        return 0 if r == 0 else (self.regs[r] & 0xFFFFFFFF)

    def wreg(self, r, v):
        """Write register (x0 silently discarded)."""
        if r != 0:
            self.regs[r] = v & 0xFFFFFFFF

    # ── Memory access ─────────────────────────

    def _valid_read(self, addr):
        return (self.PROG_START  <= addr <= self.PROG_END  or
                self.STACK_START <= addr <= self.STACK_END or
                self.DATA_START  <= addr <= self.DATA_END)

    def _valid_write(self, addr):
        return (self.STACK_START <= addr <= self.STACK_END or
                self.DATA_START  <= addr <= self.DATA_END)

    def mread(self, addr):
        """Returns (value, error_bool)."""
        addr &= 0xFFFFFFFF
        if not self._valid_read(addr):
            return 0, True
        return self.memory.get(addr, 0), False

    def mwrite(self, addr, val):
        """Returns error_bool."""
        addr &= 0xFFFFFFFF
        if not self._valid_write(addr):
            return True
        self.memory[addr] = val & 0xFFFFFFFF
        return False

    # ── Output helpers ────────────────────────

    def trace_line(self):
        """next_PC + 32 registers, all as 32-bit binary with 0b prefix."""
        regs = ' '.join(to_bin32(self.regs[i]) for i in range(32))
        return to_bin32(self.pc) + ' ' + regs

    def mem_dump(self):
        """32 lines of data memory in 'hex_addr:bin_val' format."""
        lines = []
        for i in range(32):
            addr = self.DATA_START + i * 4
            val  = self.memory.get(addr, 0)
            lines.append(f'0x{addr:08X}:{to_bin32(val)}')
        return lines

    # ── Main execution loop ───────────────────

    def run(self):
        while True:
            idx = self.pc >> 2          # byte-addr → instruction index
            if idx < 0 or idx >= len(self.program):
                print(f"Error: PC {hex(self.pc)} is out of program bounds.")
                break

            instr = self.program[idx]

            # ── Decode common fields ──────────
            opcode = instr[25:32]       # bits [6:0]
            funct3 = instr[17:20]       # bits [14:12]
            funct7 = instr[0:7]         # bits [31:25]
            rd     = int(instr[20:25], 2)   # bits [11:7]
            rs1    = int(instr[12:17], 2)   # bits [19:15]
            rs2    = int(instr[7:12],  2)   # bits [24:20]

            next_pc = self.pc + 4
            error   = False

            # ── Virtual halt: beq zero,zero,0 ──
            # Encoding: 00000000000000000000000001100011
            if instr == '00000000000000000000000001100011':
                # PC stays same (branch to PC+0), update then trace
                self.pc = self.pc  # no change
                self.output.append(self.trace_line())
                self.output.extend(self.mem_dump())
                break

            # ══════════════════════════════════
            #  R-TYPE   opcode 0110011
            # ══════════════════════════════════
            if opcode == '0110011':
                v1  = self.rreg(rs1);  v2  = self.rreg(rs2)
                sv1 = sign_extend(v1, 32); sv2 = sign_extend(v2, 32)

                if   funct3 == '000' and funct7 == '0000000': self.wreg(rd, v1 + v2)          # add
                elif funct3 == '000' and funct7 == '0100000': self.wreg(rd, sv1 - sv2)         # sub
                elif funct3 == '001':                          self.wreg(rd, v1 << (v2 & 0x1F)) # sll
                elif funct3 == '010':                          self.wreg(rd, 1 if sv1 < sv2 else 0)  # slt
                elif funct3 == '011':                          self.wreg(rd, 1 if v1 < v2 else 0)    # sltu
                elif funct3 == '100':                          self.wreg(rd, v1 ^ v2)           # xor
                elif funct3 == '101' and funct7 == '0000000': self.wreg(rd, v1 >> (v2 & 0x1F)) # srl
                elif funct3 == '110':                          self.wreg(rd, v1 | v2)            # or
                elif funct3 == '111':                          self.wreg(rd, v1 & v2)            # and

            # ══════════════════════════════════
            #  I-TYPE ARITHMETIC   opcode 0010011
            # ══════════════════════════════════
            elif opcode == '0010011':
                imm = sign_extend(int(instr[0:12], 2), 12)
                v1  = self.rreg(rs1)
                sv1 = sign_extend(v1, 32)

                if   funct3 == '000': self.wreg(rd, sv1 + imm)                               # addi
                elif funct3 == '011': self.wreg(rd, 1 if v1 < (imm & 0xFFFFFFFF) else 0)     # sltiu

            # ══════════════════════════════════
            #  LOAD   opcode 0000011
            # ══════════════════════════════════
            elif opcode == '0000011':
                imm  = sign_extend(int(instr[0:12], 2), 12)
                addr = (sign_extend(self.rreg(rs1), 32) + imm) & 0xFFFFFFFF
                if addr % 4 != 0:
                    error = True
                else:
                    val, error = self.mread(addr)
                    if not error:
                        self.wreg(rd, val)                                                     # lw

            # ══════════════════════════════════
            #  STORE   opcode 0100011
            # ══════════════════════════════════
            elif opcode == '0100011':
                imm_raw = (int(instr[0:7], 2) << 5) | int(instr[20:25], 2)
                imm     = sign_extend(imm_raw, 12)
                addr    = (sign_extend(self.rreg(rs1), 32) + imm) & 0xFFFFFFFF
                if addr % 4 != 0:
                    error = True
                else:
                    error = self.mwrite(addr, self.rreg(rs2))                                 # sw

            # ══════════════════════════════════
            #  B-TYPE   opcode 1100011
            # ══════════════════════════════════
            elif opcode == '1100011':
                # Reconstruct imm[12:1] → sign-extended 13-bit offset
                imm_raw = int(instr[0] + instr[24] + instr[1:7] + instr[20:24] + '0', 2)
                imm     = sign_extend(imm_raw, 13)

                v1 = self.rreg(rs1);  v2 = self.rreg(rs2)
                sv1 = sign_extend(v1, 32); sv2 = sign_extend(v2, 32)

                taken = False
                if   funct3 == '000': taken = sv1 == sv2   # beq
                elif funct3 == '001': taken = sv1 != sv2   # bne
                elif funct3 == '100': taken = sv1 <  sv2   # blt
                elif funct3 == '101': taken = sv1 >= sv2   # bge
                elif funct3 == '110': taken = v1  <  v2    # bltu
                elif funct3 == '111': taken = v1  >= v2    # bgeu

                if taken:
                    next_pc = (self.pc + imm) & 0xFFFFFFFF

            # ══════════════════════════════════
            #  U-TYPE: LUI   opcode 0110111
            # ══════════════════════════════════
            elif opcode == '0110111':
                imm20 = int(instr[0:20], 2)
                self.wreg(rd, (imm20 << 12) & 0xFFFFFFFF)                                     # lui

            # ══════════════════════════════════
            #  U-TYPE: AUIPC   opcode 0010111
            # ══════════════════════════════════
            elif opcode == '0010111':
                imm20 = int(instr[0:20], 2)
                self.wreg(rd, (self.pc + (imm20 << 12)) & 0xFFFFFFFF)                         # auipc

            # ══════════════════════════════════
            #  J-TYPE: JAL   opcode 1101111
            # ══════════════════════════════════
            elif opcode == '1101111':
                # Reconstruct imm[20:1] → sign-extended 21-bit offset
                imm_raw = int(instr[0] + instr[12:20] + instr[11] + instr[1:11] + '0', 2)
                imm     = sign_extend(imm_raw, 21)
                self.wreg(rd, self.pc + 4)
                next_pc = (self.pc + imm) & 0xFFFFFFFF                                        # jal

            # ══════════════════════════════════
            #  I-TYPE: JALR   opcode 1100111
            # ══════════════════════════════════
            elif opcode == '1100111':
                imm  = sign_extend(int(instr[0:12], 2), 12)
                base = sign_extend(self.rreg(rs1), 32)
                self.wreg(rd, self.pc + 4)
                next_pc = (base + imm) & 0xFFFFFFFE    # clear LSB                            # jalr

            else:
                print(f"Error: Unknown opcode '{opcode}' at PC {hex(self.pc)}.")
                break

            # ── Error check (invalid memory access) ──
            if error:
                print(f"Error: Invalid memory access at PC {hex(self.pc)}.")
                break   # no trace line, no memory dump — terminate immediately

            # ── Advance PC first, then record state ──
            self.pc = next_pc
            self.output.append(self.trace_line())


# ──────────────────────────────────────────────
#  Entry point
# ──────────────────────────────────────────────

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 Simulator.py <input.txt> <output.txt> [readable.txt]")
        sys.exit(1)

    sim = Simulator()

    try:
        sim.load(sys.argv[1])
    except FileNotFoundError:
        print(f"Error: Could not find input file '{sys.argv[1]}'.")
        sys.exit(1)

    sim.run()

    with open(sys.argv[2], 'w') as f:
        for line in sim.output:
            f.write(line + '\n')

    print("Simulation complete.")


if __name__ == '__main__':
    main()
