.extern save_file
.extern load_file
.extern print_struct

.global main

.section .text
main:
	subq $8, %rsp
	call load_file
	addq $8, %rsp

	subq $8, %rsp
	call print_struct
	addq $8, %rsp

	subq $8, %rsp
	call save_file
	addq $8, %rsp

	movq $0, %rax
	ret
	
