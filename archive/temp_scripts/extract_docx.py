#!/usr/bin/env python
import zipfile
import xml.etree.ElementTree as ET
import sys

docx_path = r"C:\Users\PC\Documents\AI Sales OS\AI_Sales_OS_Analysis_Report_Branded.docx"

try:
    with zipfile.ZipFile(docx_path, 'r') as z:
        xml_content = z.read('word/document.xml')
        root = ET.fromstring(xml_content)
        
        # Extract all text
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        for elem in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
            if elem.text:
                print(elem.text)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
