# Hard Test 5: Edge case immediates + sw/lw
addi sp, zero, 0
addi t0, zero, 2047
addi t1, zero, -2048
sw t0, 0(sp)
sw t1, 4(sp)
lw t2, 0(sp)
lw t3, 4(sp)
add t4, t2, t3
beq zero, zero, 0
