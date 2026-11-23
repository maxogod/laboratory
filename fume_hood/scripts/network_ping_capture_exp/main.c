#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

int main(int argc, char* argv[]) {
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <hostname> <output-file> <seconds>\n",
                argv[0]);
        exit(EXIT_FAILURE);
    }

    char* hostname = argv[1];
    char* output_filename = argv[2];
    char* seconds = argv[3];

    int output_fd = open(output_filename, O_RDWR | O_CREAT | O_TRUNC, 0644);
    if (output_fd < 0) {
        perror("open");
        exit(EXIT_FAILURE);
    }

    char* ping_cmd = "ping";
    char* ping_count = "-c";
    char* ping_args[] = {ping_cmd, hostname, ping_count, seconds, NULL};

    pid_t ping_pid = fork();
    if (ping_pid == 0) {
        // Child process
        int new_fd = dup2(output_fd, STDOUT_FILENO);
        if (new_fd < 0) {
            perror("dup2");
            exit(EXIT_FAILURE);
        }

        execvp(ping_cmd, ping_args);
        perror("execvp");
        exit(EXIT_FAILURE);
    } else if (ping_pid > 0) {
        // Parent process
        close(output_fd);
        waitpid(ping_pid, NULL, 0);
    } else {
        perror("fork");
        exit(EXIT_FAILURE);
    }

    // Notify pings are done
    system("notify-send '✗ Ping Capture - Done' 'Ping capture has finished. "
           "Data was exported to given file.'");

    return EXIT_SUCCESS;
}
