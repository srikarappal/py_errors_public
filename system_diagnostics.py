#!/usr/bin/env python3
"""
ThinkingSDK System Diagnostics
Runs individual diagnostics, categories, or all diagnostics with exception counting and validation.
"""

import sys
import os
import subprocess
import time
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
import json

# Scenario categories and their expected exception counts
DIAGNOSTIC_CATEGORIES = {
    "basic_errors": {
        "path": "basic_errors/",
        "diagnostics": [
            ("json_file_processing_scenario.py", 1),
            ("unbound_local_variable_scenario.py", 1),
            ("nonetype_attribute_error_scenario.py", 1),
            ("regex_processing_error_scenario.py", 1),
            ("array_index_out_of_bounds_scenario.py", 1)
        ],
        "total_expected": "5 exceptions"
    },
    "database_issues": {
        "path": "database_issues/",
        "diagnostics": [
            ("sqlite_wrong_placeholder_scenario.py", 1),
            ("postgresql_failed_transaction_scenario.py", 1),
            ("database_pool_exhaustion_scenario.py", "2-5")
        ],
        "total_expected": "4-7 exceptions"
    },
    "api_networking": {
        "path": "api_networking/",
        "diagnostics": [
            ("api_rate_limiting_scenario.py", "3-5")
        ],
        "total_expected": "3-5 exceptions"
    },
    "memory_management": {
        "path": "memory_management/",
        "diagnostics": [
            ("memory_leak_patterns_scenario.py", 6),
            ("thread_leak_scenario.py", "1-2")
        ],
        "total_expected": "7-8 exceptions"
    },
    "concurrency": {
        "path": "concurrency/",
        "diagnostics": [
            ("threading_worker_scenario.py", "1-2"),
            ("threading_deadlock_scenario.py", "1-2"),
            ("threading_condition_variable_scenario.py", "1-2"),
            ("race_condition_scenario.py", 1),
            ("enhanced_ninth_scenario.py", "1-2"),
            ("enhanced_tenth_scenario.py", "1-2")
        ],
        "total_expected": "6-12 exceptions"
    },
    "multiprocessing": {
        "path": "multiprocessing/",
        "diagnostics": [
            ("basic_multiprocess_scenario.py", "1-3"),
            ("process_communication_scenario.py", "2-4"),
            ("enhanced_multiprocess_support.py", "1-3")
        ],
        "total_expected": "4-10 exceptions"
    },
    "long_running_servers": {
        "path": "long_running_servers/",
        "diagnostics": [
            ("long_running_server_scenario.py", "2-5")
        ],
        "total_expected": "2-5 exceptions"
    },
    "business_logic": {
        "path": "business_logic/",
        "diagnostics": [
            ("ecommerce_inventory_overselling_scenario.py", "1-3")
        ],
        "total_expected": "1-3 exceptions"
    },
    "security": {
        "path": "security/",
        "diagnostics": [
            ("security_vulnerabilities_scenario.py", "3-6")
        ],
        "total_expected": "3-6 exceptions"
    }
}

class ScenarioRunner:
    def __init__(self):
        self.results = []
        self.start_time = None
        self.total_diagnostics = 0
        self.successful_runs = 0
        self.failed_runs = 0

    def print_header(self):
        """Print the runner header"""
        print("=" * 70)
        print("🧪 ThinkingSDK System Diagnostics")
        print("=" * 70)
        print(f"📁 Working Directory: {os.getcwd()}")
        print(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

    def print_category_info(self, category: str):
        """Print category information"""
        category_info = DIAGNOSTIC_CATEGORIES[category]
        scenario_count = len(category_info["diagnostics"])
        expected_exceptions = category_info["total_expected"]
        
        print(f"📂 Category: {category.replace('_', ' ').title()}")
        print(f"📊 Scenarios: {scenario_count}")
        print(f"🎯 Expected Exceptions: {expected_exceptions}")
        print("-" * 50)

    def run_scenario(self, category: str, scenario_file: str, expected_exceptions) -> Dict:
        """Run a single scenario and capture results"""
        category_path = DIAGNOSTIC_CATEGORIES[category]["path"]
        scenario_path = Path(category_path) / scenario_file
        
        print(f"🚀 Running: {scenario_path}")
        print(f"   Expected exceptions: {expected_exceptions}")
        
        start_time = time.time()
        result = {
            "category": category,
            "scenario": scenario_file,
            "path": str(scenario_path),
            "expected_exceptions": expected_exceptions,
            "start_time": start_time,
            "success": False,
            "duration": 0,
            "output": "",
            "error": ""
        }
        
        try:
            # Run the scenario
            process = subprocess.run(
                [sys.executable, str(scenario_path)],
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            duration = time.time() - start_time
            result.update({
                "success": process.returncode == 0 or "ThinkingSDK stopped" in process.stdout,
                "duration": duration,
                "output": process.stdout,
                "error": process.stderr,
                "return_code": process.returncode
            })
            
            # Print result
            status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
            print(f"   {status} ({duration:.2f}s)")
            
            if result["success"]:
                self.successful_runs += 1
                if "exception" in process.stdout.lower() or process.returncode != 0:
                    print("   🎯 Exceptions detected (check ThinkingSDK server logs)")
            else:
                self.failed_runs += 1
                if process.stderr:
                    print(f"   ⚠️  Error: {process.stderr.strip()[:100]}...")
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            result.update({
                "success": False,
                "duration": duration,
                "error": "Scenario timed out after 60 seconds"
            })
            print(f"   ❌ TIMEOUT ({duration:.2f}s)")
            self.failed_runs += 1
            
        except Exception as e:
            duration = time.time() - start_time
            result.update({
                "success": False,
                "duration": duration,
                "error": str(e)
            })
            print(f"   ❌ ERROR: {str(e)}")
            self.failed_runs += 1
        
        print()
        self.results.append(result)
        return result

    def run_category(self, category: str) -> List[Dict]:
        """Run all diagnostics in a category"""
        if category not in DIAGNOSTIC_CATEGORIES:
            print(f"❌ Unknown category: {category}")
            return []
        
        self.print_category_info(category)
        category_results = []
        
        category_info = DIAGNOSTIC_CATEGORIES[category]
        for scenario_file, expected_exceptions in category_info["diagnostics"]:
            result = self.run_scenario(category, scenario_file, expected_exceptions)
            category_results.append(result)
            
            # Brief pause between diagnostics
            time.sleep(1)
        
        return category_results

    def run_all_categories(self) -> List[Dict]:
        """Run all diagnostics in all categories"""
        all_results = []
        
        for category in DIAGNOSTIC_CATEGORIES.keys():
            print(f"\n{'='*20} {category.replace('_', ' ').title()} {'='*20}")
            category_results = self.run_category(category)
            all_results.extend(category_results)
            
            # Longer pause between categories
            print("⏳ Pausing 3 seconds between categories...")
            time.sleep(3)
        
        return all_results

    def print_summary(self):
        """Print execution summary"""
        total_duration = sum(r["duration"] for r in self.results)
        
        print("=" * 70)
        print("📊 EXECUTION SUMMARY")
        print("=" * 70)
        print(f"⏱️  Total Duration: {total_duration:.2f} seconds")
        print(f"📈 Total Scenarios: {self.total_diagnostics}")
        print(f"✅ Successful: {self.successful_runs}")
        print(f"❌ Failed: {self.failed_runs}")
        print(f"📊 Success Rate: {(self.successful_runs/self.total_diagnostics*100):.1f}%")
        print()
        
        # Print category summary
        print("📂 CATEGORY SUMMARY:")
        category_summary = {}
        for result in self.results:
            cat = result["category"]
            if cat not in category_summary:
                category_summary[cat] = {"total": 0, "success": 0, "expected": ""}
            category_summary[cat]["total"] += 1
            if result["success"]:
                category_summary[cat]["success"] += 1
            category_summary[cat]["expected"] = DIAGNOSTIC_CATEGORIES[cat]["total_expected"]
        
        for category, stats in category_summary.items():
            success_rate = (stats["success"] / stats["total"]) * 100
            print(f"   {category.replace('_', ' ').title()}: {stats['success']}/{stats['total']} "
                  f"({success_rate:.0f}%) - Expected: {stats['expected']}")
        
        print()
        print("🔍 VALIDATION INSTRUCTIONS:")
        print("1. Check ThinkingSDK server logs for captured exceptions")
        print("2. Compare actual exception counts with expected counts above")
        print("3. Verify exception details: type, message, stack trace")
        print("4. Failed diagnostics may still generate valid exceptions")
        print()

    def save_results(self, filename: str = "scenario_results.json"):
        """Save results to JSON file"""
        results_data = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "total_diagnostics": self.total_diagnostics,
            "successful_runs": self.successful_runs,
            "failed_runs": self.failed_runs,
            "total_duration": sum(r["duration"] for r in self.results),
            "results": self.results
        }
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"💾 Results saved to: {filename}")

def main():
    parser = argparse.ArgumentParser(
        description="Run ThinkingSDK diagnostics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_diagnostics.py all                    # Run all diagnostics
  python run_diagnostics.py basic_errors          # Run basic error diagnostics
  python run_diagnostics.py memory_management     # Run memory management diagnostics
  python run_diagnostics.py --list               # List available categories
  
Available categories:
  - basic_errors (5 diagnostics, 5 expected exceptions)
  - database_issues (3 diagnostics, 4-7 expected exceptions)
  - api_networking (1 scenario, 3-5 expected exceptions)
  - memory_management (2 diagnostics, 7-8 expected exceptions)
  - concurrency (6 diagnostics, 6-12 expected exceptions)
  - multiprocessing (3 diagnostics, 4-10 expected exceptions)
  - long_running_servers (1 scenario, 2-5 expected exceptions)
  - business_logic (1 scenario, 1-3 expected exceptions)
  - security (1 scenario, 3-6 expected exceptions)
        """
    )
    
    parser.add_argument(
        "target",
        nargs="?",
        choices=["all"] + list(DIAGNOSTIC_CATEGORIES.keys()),
        help="Category to run or 'all' for all categories"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available categories and exit"
    )
    
    parser.add_argument(
        "--save-results",
        metavar="FILENAME",
        default="scenario_results.json",
        help="Save results to JSON file (default: scenario_results.json)"
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("Available categories:")
        for category, info in DIAGNOSTIC_CATEGORIES.items():
            scenario_count = len(info["diagnostics"])
            expected = info["total_expected"]
            print(f"  {category:<20} - {scenario_count} diagnostics, {expected}")
        return
    
    if not args.target:
        parser.print_help()
        return
    
    runner = ScenarioRunner()
    runner.print_header()
    
    # Check if ThinkingSDK config exists
    if not Path("thinkingsdk.yaml").exists():
        print("⚠️  Warning: thinkingsdk.yaml not found")
        print("   Make sure ThinkingSDK server is running and configured")
        print()
    
    try:
        if args.target == "all":
            print("🎯 Running ALL diagnostics...")
            print(f"📊 Total diagnostics: {sum(len(cat['diagnostics']) for cat in DIAGNOSTIC_CATEGORIES.values())}")
            print()
            runner.total_diagnostics = sum(len(cat['diagnostics']) for cat in DIAGNOSTIC_CATEGORIES.values())
            runner.run_all_categories()
        else:
            print(f"🎯 Running category: {args.target}")
            runner.total_diagnostics = len(DIAGNOSTIC_CATEGORIES[args.target]["diagnostics"])
            runner.run_category(args.target)
        
        runner.print_summary()
        
        if args.save_results:
            runner.save_results(args.save_results)
    
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        print(f"📊 Completed {len(runner.results)} diagnostics before interruption")
        if runner.results:
            runner.print_summary()
    except Exception as e:
        print(f"\n❌ Runner error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()