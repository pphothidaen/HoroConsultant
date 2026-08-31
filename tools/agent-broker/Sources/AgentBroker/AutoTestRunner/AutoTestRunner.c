#include <stdio.h>
#include <unistd.h>

extern void runAllDiscoveredXCTests(void);

__attribute__((constructor))
static void auto_run_on_bundle_load(void) {
    runAllDiscoveredXCTests();
    _exit(0);
}
