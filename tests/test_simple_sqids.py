#!/usr/bin/env python3
"""
Simple test for Laravel-style Sqids helper.
Tests encode/decode without API server.
"""

from app.utils.sqids_helper import get_sqids_helper

def main():
    print("="*70)
    print("SIMPLE LARAVEL-STYLE SQIDS TEST")
    print("="*70)
    print()
    
    helper = get_sqids_helper()
    
    # Test data
    test_cases = [
        (1, 'customer'),
        (2, 'package'),
        (3, 'payment'),
        (4, 'user'),
    ]
    
    print("Testing Encode/Decode Cycle:")
    print("-"*70)
    
    all_passed = True
    
    for number, model in test_cases:
        # Encode
        sqid = helper.encode_with_prefix(number, model)
        
        # Check prefix
        expected_prefix = helper._get_prefix(model)
        has_prefix = sqid.startswith(expected_prefix)
        
        # Decode
        try:
            decoded_id, decoded_model = helper.decode_with_prefix(sqid)
            decode_success = (decoded_id == number and decoded_model == model)
        except Exception as e:
            decoded_id, decoded_model = None, None
            decode_success = False
        
        # Results
        status = "✓" if (has_prefix and decode_success) else "✗"
        print(f"{status} {model:12} ID={number}")
        print(f"   Encoded: {sqid}")
        print(f"   Prefix:  {expected_prefix} - {'OK' if has_prefix else 'FAIL'}")
        print(f"   Decoded: ID={decoded_id}, Model={decoded_model} - {'OK' if decode_success else 'FAIL'}")
        print()
        
        if not (has_prefix and decode_success):
            all_passed = False
    
    print("="*70)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print()

if __name__ == "__main__":
    main()
