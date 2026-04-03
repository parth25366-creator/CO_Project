# Hard Test 7: auipc - PC-relative address loading
auipc t0, 1
auipc t1, 4
add t2, t0, t1
beq zero, zero, 0
