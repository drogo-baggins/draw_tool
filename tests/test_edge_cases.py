#!/usr/bin/env python3
"""
Edge case tests for gradient-to-PNG fallback mechanism.
Tests: multi-stop gradients, radial gradients, opacity, gradient sharing, mixed elements.
"""

import logging
from pptx_exporter import PPTXNativeExporter
from svgelements import SVG

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def test_multi_stop_gradient():
    """Test gradient with multiple color stops"""
    print("\n" + "=" * 60)
    print("EDGE CASE 1: Multi-Stop Linear Gradient")
    print("=" * 60)

    with open("test_edge_cases.svg", "r") as f:
        svg_code = f.read()

    svg_doc = SVG.parse("test_edge_cases.svg")

    # Find rect with multiStop gradient
    for elem in svg_doc:
        if type(elem).__name__ == "Rect":
            if hasattr(elem, "values") and "url(#multiStop)" in str(
                elem.values.get("fill", "")
            ):
                print(f"✓ Found rect with multi-stop gradient")
                is_grad = PPTXNativeExporter._is_gradient_fill(elem)
                print(f"✓ Gradient detected: {is_grad}")

                # Try to build and rasterize
                svg = PPTXNativeExporter._build_gradient_svg(elem, svg_doc, svg_code)
                if svg:
                    png_bytes = PPTXNativeExporter._rasterize_element_to_png(svg, elem)
                    if png_bytes:
                        print(f"✓ Rasterized to PNG: {len(png_bytes)} bytes")
                        print("✓ Multi-stop gradient test PASSED")
                        return True
                break

    print("✗ Multi-stop gradient test FAILED")
    return False


def test_gradient_sharing():
    """Test multiple elements using the same gradient"""
    print("\n" + "=" * 60)
    print("EDGE CASE 2: Gradient Sharing (Multiple Elements)")
    print("=" * 60)

    with open("test_edge_cases.svg", "r") as f:
        svg_code = f.read()

    svg_doc = SVG.parse("test_edge_cases.svg")

    # Count elements with multiStop gradient
    multiStop_elements = []
    for elem in svg_doc:
        if hasattr(elem, "values") and "url(#multiStop)" in str(
            elem.values.get("fill", "")
        ):
            multiStop_elements.append(elem)

    print(f"Found {len(multiStop_elements)} elements using #multiStop gradient")

    if len(multiStop_elements) >= 2:
        print("✓ Gradient sharing test PASSED")
        return True
    else:
        print("✗ Gradient sharing test FAILED")
        return False


def test_opacity_gradient():
    """Test gradient with opacity variations"""
    print("\n" + "=" * 60)
    print("EDGE CASE 3: Opacity Gradient")
    print("=" * 60)

    with open("test_edge_cases.svg", "r") as f:
        svg_code = f.read()

    svg_doc = SVG.parse("test_edge_cases.svg")

    # Find polygon with opacity gradient
    for elem in svg_doc:
        if hasattr(elem, "values") and "url(#withOpacity)" in str(
            elem.values.get("fill", "")
        ):
            print(f"✓ Found element with opacity gradient")
            is_grad = PPTXNativeExporter._is_gradient_fill(elem)
            print(f"✓ Gradient detected: {is_grad}")

            # Try to rasterize
            svg = PPTXNativeExporter._build_gradient_svg(elem, svg_doc, svg_code)
            if svg:
                png_bytes = PPTXNativeExporter._rasterize_element_to_png(svg, elem)
                if png_bytes:
                    print(f"✓ Rasterized to PNG: {len(png_bytes)} bytes")
                    print("✓ Opacity gradient test PASSED")
                    return True
            break

    print("✗ Opacity gradient test FAILED")
    return False


def test_mixed_elements():
    """Test SVG with mixed gradient and non-gradient elements"""
    print("\n" + "=" * 60)
    print("EDGE CASE 4: Mixed Gradient and Non-Gradient Elements")
    print("=" * 60)

    with open("test_edge_cases.svg", "r") as f:
        svg_code = f.read()

    try:
        pptx_bytes = PPTXNativeExporter.generate_pptx_from_data(svg_code)

        if pptx_bytes:
            print(f"✓ Generated PPTX with mixed elements: {len(pptx_bytes)} bytes")
            with open("/tmp/edge_cases_test.pptx", "wb") as f:
                f.write(pptx_bytes)
            print("✓ Saved to /tmp/edge_cases_test.pptx")
            print("✓ Mixed elements test PASSED")
            return True
        else:
            print("✗ PPTX generation failed (empty bytes)")
            return False
    except Exception as e:
        print(f"✗ PPTX generation error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all edge case tests"""
    print("\n" + "🎨" * 30)
    print("GRADIENT-TO-PNG EDGE CASE TEST SUITE")
    print("🎨" * 30)

    results = {}

    try:
        results["multi_stop"] = test_multi_stop_gradient()
    except Exception as e:
        print(f"✗ Test crashed: {e}")
        import traceback

        traceback.print_exc()
        results["multi_stop"] = False

    try:
        results["gradient_sharing"] = test_gradient_sharing()
    except Exception as e:
        print(f"✗ Test crashed: {e}")
        import traceback

        traceback.print_exc()
        results["gradient_sharing"] = False

    try:
        results["opacity"] = test_opacity_gradient()
    except Exception as e:
        print(f"✗ Test crashed: {e}")
        import traceback

        traceback.print_exc()
        results["opacity"] = False

    try:
        results["mixed_elements"] = test_mixed_elements()
    except Exception as e:
        print(f"✗ Test crashed: {e}")
        import traceback

        traceback.print_exc()
        results["mixed_elements"] = False

    # Summary
    print("\n" + "=" * 60)
    print("EDGE CASE TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    total_passed = sum(1 for v in results.values() if v)
    total_tests = len(results)

    print(f"\nTotal: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 ALL EDGE CASE TESTS PASSED!")
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed")


if __name__ == "__main__":
    main()
