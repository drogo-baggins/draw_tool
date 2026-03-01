import zipfile
import re
import os


def extract_slide_xml(pptx_path):
    try:
        with zipfile.ZipFile(pptx_path, "r") as z:
            # Slides are usually at ppt/slides/slide1.xml
            # We want the first slide.
            slide_files = [
                f
                for f in z.namelist()
                if f.startswith("ppt/slides/slide") and f.endswith(".xml")
            ]
            slide_files.sort()

            if not slide_files:
                return "No slide found"

            xml_content = z.read(slide_files[0]).decode("utf-8")
            # Pretty print XML (simple indent)
            import xml.dom.minidom

            dom = xml.dom.minidom.parseString(xml_content)
            return dom.toprettyxml(indent="  ")
    except Exception as e:
        return f"Error reading {pptx_path}: {e}"


def compare_pptx_xml(file1, file2):
    xml1 = extract_slide_xml(file1)
    xml2 = extract_slide_xml(file2)

    with open("debug_xml1.xml", "w") as f:
        f.write(xml1)
    with open("debug_xml2.xml", "w") as f:
        f.write(xml2)

    print(f"Extracted XML to debug_xml1.xml and debug_xml2.xml")

    # Simple check for key structural differences in shapes (sp)
    # Looking for <a:custGeom> vs <a:prstGeom> or similar

    # Extract just the shape definitions to compare
    def extract_shapes(xml):
        shapes = re.findall(r"<p:sp>.*?</p:sp>", xml, re.DOTALL)
        return shapes

    shapes1 = extract_shapes(xml1)
    shapes2 = extract_shapes(xml2)

    print(f"\nFile 1 ({file1}): Found {len(shapes1)} shapes")
    if shapes1:
        print("--- Shape 1 Sample (File 1) ---")
        print(shapes1[0][:500] + "..." if len(shapes1[0]) > 500 else shapes1[0])

    print(f"\nFile 2 ({file2}): Found {len(shapes2)} shapes")
    if shapes2:
        print("--- Shape 1 Sample (File 2) ---")
        print(shapes2[0][:500] + "..." if len(shapes2[0]) > 500 else shapes2[0])


if __name__ == "__main__":
    if os.path.exists("debug_output.pptx") and os.path.exists("debug_output2.pptx"):
        compare_pptx_xml("debug_output.pptx", "debug_output2.pptx")
    else:
        print("One or both PPTX files missing.")
