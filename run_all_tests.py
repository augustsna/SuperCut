#!/usr/bin/env python3
"""
Comprehensive test runner for SuperCut application
Runs all unit tests and provides detailed reporting
"""

import unittest
import sys
import os
import time
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def run_test_suite(test_file, test_name="Test Suite"):
    """Run a specific test suite and return results"""
    print(f"\n{'='*60}")
    print(f"Running {test_name}")
    print(f"{'='*60}")
    
    # Load and run the test
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.dirname(test_file), pattern=os.path.basename(test_file))
    
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    return {
        'name': test_name,
        'tests_run': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0,
        'duration': end_time - start_time,
        'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0,
        'failures_list': result.failures,
        'errors_list': result.errors
    }

def print_test_results(results):
    """Print detailed test results"""
    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE TEST REPORT")
    print(f"{'='*80}")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_duration = 0
    
    for result in results:
        print(f"\n{result['name']}:")
        print(f"  Tests run: {result['tests_run']}")
        print(f"  Failures: {result['failures']}")
        print(f"  Errors: {result['errors']}")
        print(f"  Duration: {result['duration']:.2f}s")
        print(f"  Success rate: {result['success_rate']:.1f}%")
        
        total_tests += result['tests_run']
        total_failures += result['failures']
        total_errors += result['errors']
        total_duration += result['duration']
        
        # Print detailed failure/error information
        if result['failures'] > 0:
            print(f"  Failures:")
            for test, traceback in result['failures_list']:
                print(f"    - {test}: {traceback.split('AssertionError:')[-1].strip()}")
        
        if result['errors'] > 0:
            print(f"  Errors:")
            for test, traceback in result['errors_list']:
                print(f"    - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"OVERALL SUMMARY")
    print(f"{'='*80}")
    print(f"Total tests run: {total_tests}")
    print(f"Total failures: {total_failures}")
    print(f"Total errors: {total_errors}")
    print(f"Total duration: {total_duration:.2f}s")
    
    if total_tests > 0:
        overall_success_rate = ((total_tests - total_failures - total_errors) / total_tests * 100)
        print(f"Overall success rate: {overall_success_rate:.1f}%")
        
        if overall_success_rate >= 90:
            print(f"Status: 🟢 EXCELLENT ({overall_success_rate:.1f}%)")
        elif overall_success_rate >= 80:
            print(f"Status: 🟡 GOOD ({overall_success_rate:.1f}%)")
        elif overall_success_rate >= 70:
            print(f"Status: 🟠 FAIR ({overall_success_rate:.1f}%)")
        else:
            print(f"Status: 🔴 NEEDS IMPROVEMENT ({overall_success_rate:.1f}%)")
    else:
        print(f"Status: ⚠️  NO TESTS RUN")
    
    print(f"{'='*80}")
    
    return total_failures + total_errors == 0

def main():
    """Main test runner function"""
    print("🧪 SuperCut Comprehensive Test Suite")
    print("=" * 60)
    
    # Define test suites to run
    test_suites = [
        ("test_utils.py", "Utility Functions"),
        ("test_video_worker.py", "Video Worker"),
        ("test_template_utils.py", "Template Utils"),
        ("test_main_ui.py", "Main UI"),
        ("test_enhanced_template_manager.py", "Template Manager")
    ]
    
    results = []
    
    for test_file, test_name in test_suites:
        if os.path.exists(test_file):
            try:
                result = run_test_suite(test_file, test_name)
                results.append(result)
            except Exception as e:
                print(f"❌ Error running {test_name}: {e}")
                results.append({
                    'name': test_name,
                    'tests_run': 0,
                    'failures': 0,
                    'errors': 1,
                    'skipped': 0,
                    'duration': 0,
                    'success_rate': 0,
                    'failures_list': [],
                    'errors_list': [f"Test suite failed to load: {e}"]
                })
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    # Print comprehensive results
    all_passed = print_test_results(results)
    
    # Exit with appropriate code
    if all_passed:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please review the results above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 