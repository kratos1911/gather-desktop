/* Regression for failed direct writes; never performs an out-of-bounds write.
 * gzguts.h is from the exact reviewed zlib source, not a public API contract. */
#include "gzguts.h"
#include <assert.h>
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>

int main(void) {
    unsigned char input[65536];
    memset(input, 'x', sizeof(input));
    int fd = open("/dev/null", O_RDONLY);
    assert(fd >= 0);
    gzFile file = gzdopen(fd, "wb0");
    assert(file != NULL);
    assert(gzbuffer(file, 128) == 0);
    assert(gzwrite(file, input, sizeof(input)) == 0);
    int error;
    gzerror(file, &error);
    assert(error == Z_ERRNO);
    gz_statep state = (gz_statep)file;
    int safe = state->strm.avail_in == 0 && state->strm.next_in == state->in;
    /* Stop before following the stale pointer in the vulnerable control. */
    if (!safe) {
        puts("FAIL: failed direct write retains external input state");
        gzclose(file);
        return 42;
    }
    gzclearerr(file);
    assert(gzprintf(file, "%s", "safe") == 4);
    gzclose(file);
    puts("PASS: error state reset; subsequent formatting safe");
    return 0;
}
