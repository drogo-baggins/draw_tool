#!/usr/bin/env python3
"""
Integration tests for the component library and composition engine.
Tests: workflow composition, people placement, connector alignment, PPTX compatibility, error handling.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import xml.etree.ElementTree as ET
from composition_engine import CompositionEngine


def test_workflow_composition():
    """Test a complete workflow diagram (3 boxes + 2 orthogonal connections + labels)"""
    print("\n" + "=" * 60)
    print("TEST 1: Workflow Composition")
    print("=" * 60)

    composition = {
        "canvas": {"width": 800, "height": 400, "background": "#ffffff"},
        "elements": [
            {
                "id": "box1",
                "component_id": "shape-box-rounded",
                "x": 50,
                "y": 160,
                "width": 160,
                "height": 80,
                "label": "Start",
                "fill": "#2196F3",
            },
            {
                "id": "box2",
                "component_id": "shape-box-rounded",
                "x": 320,
                "y": 160,
                "width": 160,
                "height": 80,
                "label": "Process",
                "fill": "#4CAF50",
            },
            {
                "id": "box3",
                "component_id": "shape-box-rounded",
                "x": 590,
                "y": 160,
                "width": 160,
                "height": 80,
                "label": "End",
                "fill": "#FF5722",
            },
        ],
        "connections": [
            {
                "from": {"element_id": "box1", "anchor": "right"},
                "to": {"element_id": "box2", "anchor": "left"},
                "style": "orthogonal",
                "stroke": "#607D8B",
                "stroke_width": 2,
                "arrow": "end",
            },
            {
                "from": {"element_id": "box2", "anchor": "right"},
                "to": {"element_id": "box3", "anchor": "left"},
                "style": "orthogonal",
                "stroke": "#607D8B",
                "stroke_width": 2,
                "arrow": "end",
            },
        ],
    }

    try:
        engine = CompositionEngine()
        svg_string = engine.compose(composition)

        root = ET.fromstring(svg_string)
        print("✓ Output is valid SVG (parseable by ET)")

        polylines = root.findall(".//{http://www.w3.org/2000/svg}polyline")
        if len(polylines) >= 2:
            print(f"✓ Contains {len(polylines)} polyline elements (orthogonal routing)")
        else:
            print(f"✗ Expected at least 2 polylines, got {len(polylines)}")
            return False

        markers = root.findall(".//{http://www.w3.org/2000/svg}marker")
        if len(markers) > 0:
            print(f"✓ Contains {len(markers)} marker elements (arrows)")
        else:
            print("✗ No marker elements found")
            return False

        texts = root.findall(".//{http://www.w3.org/2000/svg}text")
        if len(texts) >= 3:
            print(f"✓ Contains {len(texts)} text elements (labels)")
        else:
            print(f"✗ Expected at least 3 text elements, got {len(texts)}")
            return False

        svg_width = root.get("width")
        svg_height = root.get("height")
        if svg_width == "800" and svg_height == "400":
            print("✓ SVG width/height match canvas")
        else:
            print(
                f"✗ SVG dimensions {svg_width}x{svg_height} don't match canvas 800x400"
            )
            return False

        print("✓ Workflow composition test PASSED")
        return True
    except Exception as e:
        print(f"✗ Exception: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_people_placement():
    """Test person components are placed and scaled correctly"""
    print("\n" + "=" * 60)
    print("TEST 2: People Placement")
    print("=" * 60)

    composition = {
        "canvas": {"width": 600, "height": 400, "background": "#f5f5f5"},
        "elements": [
            {
                "id": "p1",
                "component_id": "people-person-standing",
                "x": 100,
                "y": 50,
                "width": 96,
                "height": 180,
            },
            {
                "id": "p2",
                "component_id": "people-person-bust",
                "x": 300,
                "y": 100,
                "width": 96,
                "height": 120,
            },
            {
                "id": "p3",
                "component_id": "people-face-smile",
                "x": 500,
                "y": 150,
                "width": 72,
                "height": 72,
            },
        ],
        "connections": [],
    }

    try:
        engine = CompositionEngine()
        svg_string = engine.compose(composition)

        root = ET.fromstring(svg_string)
        print("✓ Output is valid SVG")

        groups = root.findall(".//{http://www.w3.org/2000/svg}g")
        transform_groups = [g for g in groups if g.get("transform")]
        if len(transform_groups) >= 3:
            print(
                f"✓ Contains {len(transform_groups)} groups with transform (placed elements)"
            )
        else:
            print(
                f"✗ Expected at least 3 groups with transform, got {len(transform_groups)}"
            )
            return False

        translate_groups = [
            g for g in transform_groups if "translate" in g.get("transform", "")
        ]
        if len(translate_groups) >= 3:
            print(f"✓ All groups have translate transform")
        else:
            print(f"✗ Expected translate in groups, found only {len(translate_groups)}")
            return False

        print("✓ People placement test PASSED")
        return True
    except Exception as e:
        print(f"✗ Exception: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_connector_alignment():
    """Test that orthogonal routing produces aligned segments (no diagonal lines)"""
    print("\n" + "=" * 60)
    print("TEST 3: Connector Alignment")
    print("=" * 60)

    composition = {
        "canvas": {"width": 600, "height": 300, "background": "#ffffff"},
        "elements": [
            {
                "id": "box-a",
                "component_id": "shape-box-rounded",
                "x": 100,
                "y": 160,
                "width": 100,
                "height": 80,
                "label": "A",
            },
            {
                "id": "box-b",
                "component_id": "shape-box-rounded",
                "x": 400,
                "y": 160,
                "width": 100,
                "height": 80,
                "label": "B",
            },
        ],
        "connections": [
            {
                "from": {"element_id": "box-a", "anchor": "right"},
                "to": {"element_id": "box-b", "anchor": "left"},
                "style": "orthogonal",
                "stroke": "#000000",
                "stroke_width": 2,
                "arrow": "end",
            }
        ],
    }

    try:
        engine = CompositionEngine()
        svg_string = engine.compose(composition)

        root = ET.fromstring(svg_string)

        polylines = root.findall(".//{http://www.w3.org/2000/svg}polyline")
        if not polylines:
            print("✗ No polyline found")
            return False

        points_str = polylines[0].get("points", "")
        points = []
        for pt in points_str.split():
            x, y = pt.split(",")
            points.append((float(x), float(y)))

        print(f"  Polyline points: {len(points)} waypoints")

        has_diagonal = False
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]

            is_horizontal = abs(y2 - y1) < 0.01
            is_vertical = abs(x2 - x1) < 0.01

            if not (is_horizontal or is_vertical):
                print(f"✗ Diagonal segment found: ({x1},{y1}) -> ({x2},{y2})")
                has_diagonal = True

        if has_diagonal:
            return False

        print("✓ All segments are horizontal or vertical (no diagonals)")
        print("✓ Connector alignment test PASSED")
        return True
    except Exception as e:
        print(f"✗ Exception: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_pptx_export_compatibility():
    """Test that composed SVG can be processed by pptx_exporter"""
    print("\n" + "=" * 60)
    print("TEST 4: PPTX Export Compatibility")
    print("=" * 60)

    composition = {
        "canvas": {"width": 400, "height": 300, "background": "#ffffff"},
        "elements": [
            {
                "id": "box",
                "component_id": "shape-box-rounded",
                "x": 100,
                "y": 100,
                "width": 160,
                "height": 80,
                "label": "Test",
                "fill": "#2196F3",
            }
        ],
        "connections": [],
    }

    try:
        engine = CompositionEngine()
        svg_string = engine.compose(composition)

        root = ET.fromstring(svg_string)

        forbidden_tags = {
            "{http://www.w3.org/2000/svg}style",
            "{http://www.w3.org/2000/svg}script",
            "{http://www.w3.org/2000/svg}foreignObject",
        }

        for tag in forbidden_tags:
            if root.findall(f".//{tag}"):
                print(f"✗ Found forbidden tag: {tag}")
                return False

        print("✓ No forbidden tags (<style>, <script>, <foreignObject>)")

        all_elements = root.iter()
        for elem in all_elements:
            if "clip-path" in str(elem.attrib) or "mask" in str(elem.attrib):
                print(f"✗ Found forbidden attribute (clip-path or mask) in {elem.tag}")
                return False

        print("✓ No clip-path or mask attributes")

        allowed_tags = {
            "svg",
            "rect",
            "circle",
            "ellipse",
            "path",
            "polygon",
            "polyline",
            "line",
            "g",
            "text",
            "defs",
            "marker",
            "tspan",
        }

        for elem in root.iter():
            tag_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if tag_name not in allowed_tags:
                print(f"✗ Found unsupported tag: {tag_name}")
                return False

        print("✓ All elements are PPTX-compatible")

        try:
            from pptx_exporter import PPTXNativeExporter

            pptx_bytes = PPTXNativeExporter.generate_pptx_from_data(svg_string)
            if pptx_bytes:
                print(f"✓ PPTXNativeExporter generated PPTX: {len(pptx_bytes)} bytes")
            else:
                print("✗ PPTXNativeExporter returned no data")
                return False
        except ImportError:
            print(
                "⚠ pptx_exporter not importable (dependency missing), skipping PPTX generation test"
            )
        except Exception as e:
            print(f"✗ PPTXNativeExporter rejected SVG: {e}")
            return False

        print("✓ PPTX export compatibility test PASSED")
        return True
    except Exception as e:
        print(f"✗ Exception: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_graceful_error_handling():
    """Test that unknown component_id doesn't crash"""
    print("\n" + "=" * 60)
    print("TEST 5: Graceful Error Handling")
    print("=" * 60)

    composition = {
        "canvas": {"width": 400, "height": 300, "background": "#ffffff"},
        "elements": [
            {
                "id": "bad",
                "component_id": "nonexistent-component",
                "x": 100,
                "y": 100,
                "width": 100,
                "height": 100,
            },
            {
                "id": "good",
                "component_id": "shape-box-rounded",
                "x": 200,
                "y": 100,
                "width": 160,
                "height": 80,
                "label": "OK",
            },
        ],
        "connections": [
            {
                "from": {"element_id": "bad", "anchor": "right"},
                "to": {"element_id": "good", "anchor": "left"},
                "style": "orthogonal",
                "arrow": "end",
            }
        ],
    }

    try:
        engine = CompositionEngine()
        svg_string = engine.compose(composition)
        print("✓ No exception thrown (graceful error handling)")

        root = ET.fromstring(svg_string)
        print("✓ Output is valid SVG")

        texts = root.findall(".//{http://www.w3.org/2000/svg}text")
        has_ok_label = any("OK" in t.text for t in texts if t.text)
        if has_ok_label:
            print("✓ Good element (OK label) is present in output")
        else:
            print("✗ Good element not found in output")
            return False

        print("✓ Graceful error handling test PASSED")
        return True
    except Exception as e:
        print(f"✗ Exception during composition: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_pose_components():
    """Test that all 8 new pose components load and compose correctly"""
    print("\n" + "=" * 60)
    print("TEST 6: Pose Component Composition")
    print("=" * 60)

    new_pose_ids = [
        "people-person-walking",
        "people-person-running",
        "people-person-presenting",
        "people-person-raising-hand",
        "people-person-working-desk",
        "people-person-pointing-right",
        "people-person-waving",
        "people-person-group",
    ]

    try:
        engine = CompositionEngine()

        # Verify all 8 pose components are in the manifest
        summary = engine.get_component_summary()
        missing = []
        for pid in new_pose_ids:
            if pid not in summary:
                missing.append(pid)
        if missing:
            print(f"✗ Missing from component summary: {missing}")
            return False
        print(f"✓ All {len(new_pose_ids)} new pose components found in manifest")

        # Compose a scene using multiple poses
        composition = {
            "canvas": {"width": 900, "height": 400, "background": "#ffffff"},
            "elements": [
                {
                    "id": "walker",
                    "component_id": "people-person-walking",
                    "x": 50,
                    "y": 140,
                    "width": 64,
                    "height": 120,
                },
                {
                    "id": "presenter",
                    "component_id": "people-person-presenting",
                    "x": 200,
                    "y": 140,
                    "width": 80,
                    "height": 120,
                },
                {
                    "id": "desk-worker",
                    "component_id": "people-person-working-desk",
                    "x": 400,
                    "y": 150,
                    "width": 120,
                    "height": 100,
                },
                {
                    "id": "group",
                    "component_id": "people-person-group",
                    "x": 650,
                    "y": 140,
                    "width": 140,
                    "height": 120,
                },
            ],
            "connections": [
                {
                    "from": {"element_id": "presenter", "anchor": "right"},
                    "to": {"element_id": "desk-worker", "anchor": "left"},
                    "style": "orthogonal",
                    "stroke": "#607D8B",
                    "stroke_width": 2,
                    "arrow": "end",
                }
            ],
        }

        svg_string = engine.compose(composition)
        root = ET.fromstring(svg_string)
        print("✓ Multi-pose scene composes to valid SVG")

        # Verify 4 elements placed (4 groups with transform)
        groups = root.findall(".//{http://www.w3.org/2000/svg}g")
        transform_groups = [
            g
            for g in groups
            if g.get("transform") and "translate" in g.get("transform", "")
        ]
        if len(transform_groups) >= 4:
            print(f"✓ {len(transform_groups)} groups placed with translate transforms")
        else:
            print(
                f"✗ Expected at least 4 translated groups, got {len(transform_groups)}"
            )
            return False

        # Verify the connection using presenter's right anchor exists
        polylines = root.findall(".//{http://www.w3.org/2000/svg}polyline")
        if len(polylines) >= 1:
            print(f"✓ Connection rendered ({len(polylines)} polyline(s))")
        else:
            print("✗ No polyline connection found")
            return False

        # Test each remaining pose individually composes without error
        remaining_poses = [
            "people-person-running",
            "people-person-raising-hand",
            "people-person-pointing-right",
            "people-person-waving",
        ]
        for pid in remaining_poses:
            single = {
                "canvas": {"width": 200, "height": 200, "background": "#ffffff"},
                "elements": [
                    {
                        "id": "solo",
                        "component_id": pid,
                        "x": 50,
                        "y": 20,
                        "width": 80,
                        "height": 120,
                    }
                ],
                "connections": [],
            }
            svg_out = engine.compose(single)
            ET.fromstring(svg_out)  # Validate parse
        print(f"✓ All {len(remaining_poses)} remaining poses compose individually")

        print("✓ Pose component composition test PASSED")
        return True
    except Exception as e:
        print(f"✗ Exception: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all composition tests"""
    print("\n" + "🎨" * 30)
    print("COMPONENT COMPOSITION TEST SUITE")
    print("🎨" * 30)

    results = {}

    try:
        results["workflow_composition"] = test_workflow_composition()
    except Exception as e:
        print(f"✗ Test crashed: {e}")
        import traceback

        traceback.print_exc()
        results["workflow_composition"] = False

    try:
        results["people_placement"] = test_people_placement()
    except Exception as e:
        print(f"✗ Test crashed: {e}")
        import traceback

        traceback.print_exc()
        results["people_placement"] = False

    try:
        results["connector_alignment"] = test_connector_alignment()
    except Exception as e:
        print(f"✗ Test crashed: {e}")
        import traceback

        traceback.print_exc()
        results["connector_alignment"] = False

    try:
        results["pptx_export_compatibility"] = test_pptx_export_compatibility()
    except Exception as e:
        print(f"✗ Test crashed: {e}")
        import traceback

        traceback.print_exc()
        results["pptx_export_compatibility"] = False

    try:
        results["graceful_error_handling"] = test_graceful_error_handling()
    except Exception as e:
        print(f"✗ Test crashed: {e}")
        import traceback

        traceback.print_exc()
        results["graceful_error_handling"] = False

    try:
        results["pose_components"] = test_pose_components()
    except Exception as e:
        print(f"✗ Test crashed: {e}")
        import traceback

        traceback.print_exc()
        results["pose_components"] = False

    print("\n" + "=" * 60)
    print("COMPONENT COMPOSITION TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    total_passed = sum(1 for v in results.values() if v)
    total_tests = len(results)

    print(f"\nTotal: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 ALL COMPONENT COMPOSITION TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
