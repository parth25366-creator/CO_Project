# Hard Test 10: Subroutine call pattern (from spec example)
jal ra, main
func: addi sp, sp, -4
sw ra, 0(sp)
addi a0, a0, 1
lw ra, 0(sp)
addi sp, sp, 4
jalr zero, ra, 0
main: addi sp, zero, 256
addi a0, zero, 21
jal ra, func
beq zero, zero, 0
