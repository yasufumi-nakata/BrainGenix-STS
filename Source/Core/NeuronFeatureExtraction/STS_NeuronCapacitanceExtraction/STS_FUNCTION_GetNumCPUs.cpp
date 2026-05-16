//=================================================================//
// This file is part of the BrainGenix-STS Scan Translation System //
//=================================================================//

#include <STS_FUNCTION_GetNumCPUs.h>


// Get Number CPUS, Wraps std::thread::hardware_concurrency
int STS_FUNCTION_GetNumberCPUs() {

    // Get Number
    unsigned int DetectedHardwareThreads = std::thread::hardware_concurrency();
    int NumCPUS = DetectedHardwareThreads == 0 ? 1 : (int)DetectedHardwareThreads;

    // Return 
    return NumCPUS;

}
