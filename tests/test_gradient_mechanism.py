#!/usr/bin/env python3
"""
Test script for gradient-to-PNG fallback mechanism.
Tests individual helper functions and end-to-end flow.
"""

import logging
from io import BytesIO
from pptx_exporter import PPTXNativeExporter
from svgelements import SVG

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_gradient_detection():
    """Test _is_gradient_fill() function"""
    print("\n" + "=" * 60)
    print("TEST 1: Gradient Detection")
    print("=" * 60)

    # Load test SVG
    svg_doc = SVG.parse("test_gradients.svg")

    gradient_elements = []
    non_gradient_elements = []

    for element in svg_doc:
        is_grad = PPTXNativeExporter._is_gradient_fill(element)
        if is_grad:
            gradient_elements.append(element)
            print(f"✓ Found gradient element: {type(element).__name__}")
        elif hasattr(element, "fill") and element.fill:
            non_gradient_elements.append(element)

    print(f"\nDetected {len(gradient_elements)} gradient elements")
    if gradient_elements:
        print("✓ Gradient detection PASSED")
        return True
    else:
        print("✗ Gradient detection FAILED")
        return False


def test_gradient_extraction():
    """Test _extract_gradient_from_svg_code() function"""
    print("\n" + "=" * 60)
    print("TEST 2: Gradient Extraction from SVG Code")
    print("=" * 60)

    # Read SVG code
    with open("test_gradients.svg", "r") as f:
        svg_code = f.read()

    # Test extracting both gradients
    grad1 = PPTXNativeExporter._extract_gradient_from_svg_code("grad1", svg_code)
    grad2 = PPTXNativeExporter._extract_gradient_from_svg_code("grad2", svg_code)

    if grad1:
        print(f"✓ Extracted grad1: {grad1[:80]}...")
    else:
        print("✗ Failed to extract grad1")

    if grad2:
        print(f"✓ Extracted grad2: {grad2[:80]}...")
    else:
        print("✗ Failed to extract grad2")

    passed = grad1 is not None and grad2 is not None
    if passed:
        print("\n✓ Gradient extraction PASSED")
    else:
        print("\n✗ Gradient extraction FAILED")

    return passed


def test_gradient_svg_build():
    """Test _build_gradient_svg() function"""
    print("\n" + "=" * 60)
    print("TEST 3: Minimal Gradient SVG Construction")
    print("=" * 60)

    svg_doc = SVG.parse("test_gradients.svg")

    # Read SVG code
    with open("test_gradients.svg", "r") as f:
        svg_code = f.read()

    gradient_elements = [
        e for e in svg_doc if PPTXNativeExporter._is_gradient_fill(e)
    ]

    if not gradient_elements:
        print("✗ No gradient elements found")
        return False

    element = gradient_elements[0]
    print(f"Building gradient SVG for element: {type(element).__name__}")

    result_svg = PPTXNativeExporter._build_gradient_svg(element, svg_doc, svg_code)

    if result_svg:
        print(f"✓ Built gradient SVG: {result_svg[:150]}...")
        print("\n✓ Gradient SVG construction PASSED")
        return True
    else:
        print("✗ Failed to build gradient SVG")
        print("\n✗ Gradient SVG construction FAILED")
        return False


def test_png_rasterization():
    """Test _rasterize_element_to_png() function"""
    print("\n" + "=" * 60)
    print("TEST 4: SVG to PNG Rasterization")
    print("=" * 60)

    svg_doc = SVG.parse("test_gradients.svg")

    # Read SVG code
    with open("test_gradients.svg", "r") as f:
        svg_code = f.read()

    gradient_elements = [
        e for e in svg_doc if PPTXNativeExporter._is_gradient_fill(e)
    ]

    if not gradient_elements:
        print("✗ No gradient elements found")
        return False

    element = gradient_elements[0]

    # Build gradient SVG first
    gradient_svg = PPTXNativeExporter._build_gradient_svg(element, svg_doc, svg_code)
    if not gradient_svg:
        print("✗ Failed to build gradient SVG")
        return False

    # Try to rasterize
    png_bytes = PPTXNativeExporter._rasterize_element_to_png(gradient_svg, element)

    if png_bytes:
        print(f"✓ Rasterized to PNG: {len(png_bytes)} bytes")
        print("✓ PNG rasterization PASSED")
        return True
    else:
        print("✗ Failed to rasterize to PNG")
        print("✗ PNG rasterization FAILED")
        return False


def test_full_pptx_generation():
    """Test full PPTX generation with gradients"""
    print("\n" + "=" * 60)
    print("TEST 5: Full PPTX Generation with Gradients")
    print("=" * 60)

    with open("test_gradients.svg", "r") as f:
        svg_code = f.read()

    try:
        pptx_bytes = PPTXNativeExporter.generate_pptx_from_data(svg_code)

        if pptx_bytes:
            # Save to file for manual inspection
            with open("/tmp/gradient_test.pptx", "wb") as f:
                f.write(pptx_bytes)
            print(f"✓ Generated PPTX: {len(pptx_bytes)} bytes")
            print(f"✓ Saved to /tmp/gradient_test.pptx for inspection")
            print("\n✓ Full PPTX generation PASSED")
            return True
        else:
            print("✗ PPTX generation returned empty bytes")
            return False
    except Exception as e:
        print(f"✗ PPTX generation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "🎨" * 30)
    print("GRADIENT-TO-PNG FALLBACK MECHANISM - TEST SUITE")
    print("🎨" * 30)

    results = {}

    try:
        results["detection"] = test_gradient_detection()
    except Exception as e:
        print(f"✗ Gradient detection test crashed: {e}")
        import traceback

        traceback.print_exc()
        results["detection"] = False

    try:
        results["extraction"] = test_gradient_extraction()
    except Exception as e:
        print(f"✗ Gradient extraction test crashed: {e}")
        import traceback

        traceback.print_exc()
        results["extraction"] = False

    try:
        results["svg_build"] = test_gradient_svg_build()
    except Exception as e:
        print(f"✗ Gradient SVG build test crashed: {e}")
        import traceback

        traceback.print_exc()
        results["svg_build"] = False

    try:
        results["rasterization"] = test_png_rasterization()
    except Exception as e:
        print(f"✗ PNG rasterization test crashed: {e}")
        import traceback

        traceback.print_exc()
        results["rasterization"] = False

    try:
        results["pptx"] = test_full_pptx_generation()
    except Exception as e:
        print(f"✗ Full PPTX generation test crashed: {e}")
        import traceback

        traceback.print_exc()
        results["pptx"] = False

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    total_passed = sum(1 for v in results.values() if v)
    total_tests = len(results)

    print(f"\nTotal: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed")


if __name__ == "__main__":
    main()
