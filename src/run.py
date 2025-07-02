'''
Test suite for RMI Calculator Service
This script tests the connectivity and communication between the server and client
for the RMI calculator implementation.
'''
import unittest
from calcObject import calcObject

class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.calc = calcObject()
    
    def test_addition(self):
        """Test addition operation"""
        result, _ = self.calc.add(5, 3)
        self.assertEqual(result, 8)
        
        result, _ = self.calc.add(-1, -1)
        self.assertEqual(result, -2)
        
        result, _ = self.calc.add(0, 0)
        self.assertEqual(result, 0)
    
    def test_subtraction(self):
        """Test subtraction operation"""
        result, _ = self.calc.subtract(10, 4)
        self.assertEqual(result, 6)
        
        result, _ = self.calc.subtract(5, -3)
        self.assertEqual(result, 8)
    
    def test_multiplication(self):
        """Test multiplication operation"""
        result, _ = self.calc.multiply(3, 4)
        self.assertEqual(result, 12)
        
        result, _ = self.calc.multiply(-2, 5)
        self.assertEqual(result, -10)
        
        result, _ = self.calc.multiply(0, 100)
        self.assertEqual(result, 0)
    
    def test_division(self):
        """Test division operation"""
        result, _, _ = self.calc.divide(10, 2)
        self.assertEqual(result, 5.0)
        
        result, _, _ = self.calc.divide(1, 4)
        self.assertEqual(result, 0.25)
    
    def test_division_by_zero(self):
        """Test division by zero error case"""
        result, error, _ = self.calc.divide(10, 0)
        self.assertIsNone(result)
        self.assertEqual(error, "Division by zero is not allowed")
    
    def test_usage_counter(self):
        """Test that usage counter increments with each operation"""
        # Reset counter
        initial_count, _ = self.calc.usage()
        
        # Perform some operations
        self.calc.add(1, 1)
        self.calc.subtract(5, 3)
        self.calc.multiply(2, 2)
        
        # Check counter increased by 3
        count, _ = self.calc.usage()
        self.assertEqual(count, initial_count + 3)

if __name__ == '__main__':
    unittest.main()