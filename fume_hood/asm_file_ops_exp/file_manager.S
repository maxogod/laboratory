.extern printf
.extern fopen
.extern fread
.extern fwrite
.extern fclose

.global save_file
.global load_file
.global print_struct

.section .data
	hello: .ascii "hiii!\0"
	format: .ascii "string: %s - Number: %d\n\0"
	
	file_path: .ascii "test_struct.save\0"
	WRITE_MODE: .ascii "wb\0"
	READ_MODE: .ascii "rb\0"

	TEST_STRUCT_SIZE: .word 16
	
.section .bss
	fd: .quad 0 /* File descriptor to be used in file operations */

	.align 8 /* Add padding to align the struct to 8 bytes */
	TestStruct:
		num: .long 0 /* int (4 bytes) */
		char_ptr: .quad 0 /* char* (8 bytes) */

.section .text
save_file:
	// Open file to save to - fopen(char* path, mode)
	movq $file_path, %rdi
	movq $WRITE_MODE, %rsi
	
	subq $8, %rsp
	call fopen
	addq $8, %rsp

	// If no file was open handle error
	test %rax, %rax
	jz handle_error

	// If file was opened correctly save file descriptor
	movq %rax, fd
	
	// Write TestStruct into file - fwrite(void* data, size, n, file)
	movq $TestStruct, %rdi
	movq TEST_STRUCT_SIZE(%rip), %rsi
	movq $1, %rdx
	movq fd(%rip), %rcx
	
	subq $8, %rsp
	call fwrite
	addq $8, %rsp

	// Close file - fclose(file)
	movq fd(%rip), %rdi

	subq $8, %rsp
	call fclose
	addq $8, %rsp
	
	ret

load_file:
	// Open file to load from - fopen(char* path, mode)
	movq $file_path, %rdi
	movq $READ_MODE, %rsi
	
	subq $8, %rsp
	call fopen
	addq $8, %rsp

	// If no file was opened init by default	
	test %rax, %rax
	jz init_if_not_found

	// If it was opened correctly save it to a variable
	movq %rax, fd

	// Read file and put the content into TestStruct - fread(void* container, size, n, file)
	movq $TestStruct, %rdi
	movq TEST_STRUCT_SIZE(%rip), %rsi
	movq $1, %rdx
	movq fd(%rip), %rcx

	subq $8, %rsp
	call fread
	addq $8, %rsp

	// Close the file - fclose(file)
	movq fd(%rip), %rdi

	subq $8, %rsp
	call fclose
	addq $8, %rsp
	
	// Increase struct number to show it was properly loaded
	subq $8, %rsp
	call add_one_to_num
	addq $8, %rsp

	ret

init_if_not_found:
	// Init struct with the string hello and the int 18 (just because)
        xor %rax, %rax
        movl $18, %eax
        movl %eax, TestStruct+0(%rip) /* TestStruct.num */

        lea hello(%rip), %rax
        movq %rax, TestStruct+8(%rip) /* TestStruct.char_ptr */
        ret

print_struct:
	// print the struct into the format - printf(char* format, args...)
	movq $format, %rdi
	movq TestStruct+8(%rip), %rsi /* TestStruct.char_ptr */
	movl TestStruct+0(%rip), %edx /* TestStruct.num */
	subq $8, %rsp
	call printf
	addq $8, %rsp
	ret

add_one_to_num:
	// add one to TestStruct.num
	movl TestStruct+0(%rip), %eax
	incl %eax
	movl %eax, TestStruct+0(%rip)
	ret

handle_error:
	ret

