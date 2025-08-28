"""
E-commerce inventory overselling scenario.
Tests race conditions in inventory management that lead to overselling.
"""

import thinking_sdk_client as thinking
import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, List
import json

thinking.start(config_file="thinkingsdk.yaml")

@dataclass
class Product:
    id: str
    name: str
    price: float
    inventory_count: int

@dataclass
class Order:
    order_id: str
    user_id: str
    product_id: str
    quantity: int
    timestamp: float
    status: str = "pending"

class InventoryManager:
    """Inventory management with race condition vulnerabilities"""
    
    def __init__(self):
        self.products = {
            "laptop_001": Product("laptop_001", "Gaming Laptop", 1299.99, 5),
            "phone_002": Product("phone_002", "Smartphone", 899.99, 3),
            "tablet_003": Product("tablet_003", "Tablet", 499.99, 2),
            "headphones_004": Product("headphones_004", "Wireless Headphones", 199.99, 10)
        }
        self.orders = []
        self.lock = threading.Lock()  # Available but not always used correctly
        
    def get_product_inventory(self, product_id: str) -> int:
        """Get current inventory count"""
        product = self.products.get(product_id)
        return product.inventory_count if product else 0
    
    def reserve_inventory_unsafe(self, product_id: str, quantity: int) -> bool:
        """Unsafe inventory reservation with race condition"""
        print(f"🔍 Checking inventory for {product_id}: {quantity} units")
        
        # Race condition: Check and update are not atomic
        current_inventory = self.get_product_inventory(product_id)
        
        if current_inventory >= quantity:
            print(f"✅ Inventory available: {current_inventory} >= {quantity}")
            
            # Simulate processing delay (network call, validation, etc.)
            time.sleep(random.uniform(0.01, 0.1))
            
            # Another thread might have modified inventory here!
            product = self.products[product_id]
            product.inventory_count -= quantity
            
            print(f"📦 Reserved {quantity} units of {product_id}. New inventory: {product.inventory_count}")
            
            # Detect overselling
            if product.inventory_count < 0:
                raise ValueError(f"OVERSELLING DETECTED: {product_id} inventory is now {product.inventory_count}!")
            
            return True
        else:
            print(f"❌ Insufficient inventory: {current_inventory} < {quantity}")
            return False
    
    def reserve_inventory_safe(self, product_id: str, quantity: int) -> bool:
        """Safe inventory reservation with proper locking"""
        with self.lock:
            current_inventory = self.get_product_inventory(product_id)
            
            if current_inventory >= quantity:
                # Simulate processing delay even inside lock (not ideal, but safer)
                time.sleep(random.uniform(0.001, 0.01))
                
                product = self.products[product_id]
                product.inventory_count -= quantity
                
                print(f"🔒 Safe reservation: {quantity} units of {product_id}. New inventory: {product.inventory_count}")
                return True
            else:
                print(f"❌ Safe check - insufficient inventory: {current_inventory} < {quantity}")
                return False
    
    def create_order(self, user_id: str, product_id: str, quantity: int, use_safe_reservation: bool = False) -> Order:
        """Create order with inventory reservation"""
        order_id = f"order_{len(self.orders)}_{user_id}_{int(time.time())}"
        
        print(f"🛒 Creating order {order_id}: {quantity}x {product_id} for user {user_id}")
        
        try:
            # Choose reservation method
            if use_safe_reservation:
                reserved = self.reserve_inventory_safe(product_id, quantity)
            else:
                reserved = self.reserve_inventory_unsafe(product_id, quantity)
            
            if reserved:
                order = Order(order_id, user_id, product_id, quantity, time.time(), "confirmed")
                self.orders.append(order)
                print(f"✅ Order {order_id} confirmed")
                return order
            else:
                order = Order(order_id, user_id, product_id, quantity, time.time(), "failed_insufficient_inventory")
                self.orders.append(order)
                print(f"❌ Order {order_id} failed - insufficient inventory")
                return order
                
        except ValueError as e:
            print(f"🚨 Order {order_id} caused overselling: {e}")
            
            # Create failed order
            order = Order(order_id, user_id, product_id, quantity, time.time(), "failed_overselling")
            self.orders.append(order)
            
            raise
    
    def get_inventory_report(self) -> Dict:
        """Get current inventory status"""
        report = {
            "products": {},
            "orders": {
                "total": len(self.orders),
                "confirmed": len([o for o in self.orders if o.status == "confirmed"]),
                "failed": len([o for o in self.orders if o.status.startswith("failed")])
            }
        }
        
        for product_id, product in self.products.items():
            report["products"][product_id] = {
                "name": product.name,
                "current_inventory": product.inventory_count,
                "orders_for_product": len([o for o in self.orders if o.product_id == product_id and o.status == "confirmed"])
            }
        
        return report

def simulate_flash_sale_customer(customer_id: int, inventory_manager: InventoryManager, 
                                target_product: str, use_safe_method: bool = False):
    """Simulate customer trying to buy during flash sale"""
    
    try:
        # Random delay to simulate different arrival times
        time.sleep(random.uniform(0, 0.5))
        
        # Try to buy 1-2 items
        quantity = random.choice([1, 1, 1, 2])  # Mostly 1 item, sometimes 2
        
        print(f"🛍️ Customer-{customer_id}: Attempting to buy {quantity}x {target_product}")
        
        order = inventory_manager.create_order(
            user_id=f"user_{customer_id}",
            product_id=target_product,
            quantity=quantity,
            use_safe_reservation=use_safe_method
        )
        
        return order
        
    except Exception as e:
        print(f"🚨 Customer-{customer_id} exception: {e}")
        raise

def run_flash_sale_simulation(product_id: str, num_customers: int, use_safe_method: bool = False):
    """Run flash sale simulation"""
    
    method_name = "SAFE" if use_safe_method else "UNSAFE"
    print(f"\n🔥 Flash Sale Simulation ({method_name}): {num_customers} customers for {product_id}")
    
    inventory_manager = InventoryManager()
    initial_inventory = inventory_manager.get_product_inventory(product_id)
    
    print(f"📦 Initial inventory for {product_id}: {initial_inventory} units")
    print(f"👥 {num_customers} customers will attempt to purchase")
    
    # Run concurrent customers
    orders = []
    exceptions = []
    
    with ThreadPoolExecutor(max_workers=min(num_customers, 20)) as executor:
        futures = []
        
        for customer_id in range(num_customers):
            future = executor.submit(
                simulate_flash_sale_customer,
                customer_id,
                inventory_manager,
                product_id,
                use_safe_method
            )
            futures.append(future)
        
        # Collect results
        for future in as_completed(futures):
            try:
                order = future.result()
                orders.append(order)
            except Exception as e:
                exceptions.append(e)
    
    # Analysis
    final_inventory = inventory_manager.get_product_inventory(product_id)
    report = inventory_manager.get_inventory_report()
    
    confirmed_orders = [o for o in orders if o.status == "confirmed"]
    failed_orders = [o for o in orders if o.status.startswith("failed")]
    
    total_units_sold = sum(o.quantity for o in confirmed_orders)
    
    print(f"\n📊 Flash Sale Results ({method_name}):")
    print(f"   Initial inventory: {initial_inventory}")
    print(f"   Final inventory: {final_inventory}")
    print(f"   Total units sold: {total_units_sold}")
    print(f"   Orders confirmed: {len(confirmed_orders)}")
    print(f"   Orders failed: {len(failed_orders)}")
    print(f"   Exceptions: {len(exceptions)}")
    
    # Check for overselling
    expected_final_inventory = initial_inventory - total_units_sold
    actual_inventory_discrepancy = final_inventory - expected_final_inventory
    
    if actual_inventory_discrepancy != 0:
        print(f"🚨 Inventory discrepancy detected: {actual_inventory_discrepancy}")
    
    if final_inventory < 0:
        print(f"🚨 OVERSELLING CONFIRMED: Final inventory is {final_inventory}")
        raise ValueError(f"Overselling detected in {method_name} method: final inventory {final_inventory}")
    
    if len(exceptions) > 0:
        print(f"🚨 {len(exceptions)} exceptions during flash sale:")
        for i, exc in enumerate(exceptions[:3]):  # Show first 3
            print(f"   {i+1}. {exc}")
        
        # Re-raise first exception for ThinkingSDK to capture
        raise exceptions[0]
    
    return {
        "method": method_name,
        "initial_inventory": initial_inventory,
        "final_inventory": final_inventory,
        "units_sold": total_units_sold,
        "confirmed_orders": len(confirmed_orders),
        "failed_orders": len(failed_orders),
        "exceptions": len(exceptions)
    }

def main():
    print("🚨 Starting e-commerce inventory overselling scenario...")
    
    try:
        # Test 1: Unsafe method (should cause overselling)
        print("\n=== Test 1: Unsafe Inventory Reservation ===")
        
        try:
            unsafe_results = run_flash_sale_simulation(
                product_id="laptop_001",
                num_customers=15,  # More customers than inventory
                use_safe_method=False
            )
            print(f"❓ Unsafe method completed without overselling: {unsafe_results}")
            
        except ValueError as e:
            if "overselling" in str(e).lower():
                print(f"✅ Overselling properly detected in unsafe method: {e}")
            else:
                raise
        
        # Brief pause between tests
        time.sleep(2)
        
        # Test 2: Safe method (should prevent overselling)
        print("\n=== Test 2: Safe Inventory Reservation ===")
        
        try:
            safe_results = run_flash_sale_simulation(
                product_id="phone_002", 
                num_customers=10,  # More customers than inventory (3 units)
                use_safe_method=True
            )
            print(f"✅ Safe method completed successfully: {safe_results}")
            
            if safe_results["final_inventory"] < 0:
                raise ValueError("Safe method still caused overselling!")
                
        except Exception as e:
            print(f"🚨 Safe method failed: {e}")
            raise
        
        # Test 3: Extreme concurrency test
        print("\n=== Test 3: Extreme Concurrency Test ===")
        
        try:
            extreme_results = run_flash_sale_simulation(
                product_id="tablet_003",
                num_customers=50,  # Many more customers than inventory (2 units)
                use_safe_method=False
            )
            
            if extreme_results["final_inventory"] < 0:
                raise ValueError(f"Extreme concurrency caused overselling: {extreme_results}")
                
        except ValueError as e:
            if "overselling" in str(e).lower():
                print(f"✅ Extreme concurrency overselling detected: {e}")
            else:
                raise
    
    except Exception as e:
        print(f"🚨 E-commerce scenario exception: {e}")
        time.sleep(2)
        raise

if __name__ == "__main__":
    try:
        main()
        print("✅ E-commerce inventory overselling scenario completed!")
    except Exception as e:
        print(f"🚨 E-commerce scenario failed: {e}")
    finally:
        print("Stopping ThinkingSDK...")
        thinking.stop()
        print("Check ThinkingSDK server for inventory overselling analysis!")