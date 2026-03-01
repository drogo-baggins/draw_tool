import zipfile
import re


def extract_slide_xml(pptx_path):
    try:
        with zipfile.ZipFile(pptx_path, "r") as z:
            slide_files = [
                f
                for f in z.namelist()
                if f.startswith("ppt/slides/slide") and f.endswith(".xml")
            ]
            slide_files.sort()
            if not slide_files:
                return "No slide found"
            xml_content = z.read(slide_files[0]).decode("utf-8")
            return xml_content
    except Exception as e:
        return f"Error reading {pptx_path}: {e}"


xml_fixed = extract_slide_xml("debug_output_fixed.pptx")
print("--- Check XML Structure for Fragmentation ---")
shapes = re.findall(r"<a:path .*?>.*?</a:path>", xml_fixed, re.DOTALL)

for i, shape_xml in enumerate(shapes):
    print(f"\nShape {i + 1}:")
    # Check for interlaced close/lnTo
    lines = shape_xml.count("<a:lnTo>")
    closes = shape_xml.count("<a:close/>")
    print(f"  Total Line Segments: {lines}")
    print(f"  Total Closes: {closes}")

    if closes > 1:
        print("  WARNING: Multiple closures found! Still fragmented?")
        # Print sample to see structure
        print(shape_xml[:500] + "...")
    else:
        print("  OK: Single closure (or none) found.")
