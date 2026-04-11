import zipfile
import xml.etree.ElementTree as ET

docx_path = r"C:\Users\PC\Documents\AI Sales OS\AI_Sales_OS_Analysis_Report_Branded.docx"

with zipfile.ZipFile(docx_path) as z:
    xml_content = z.read('word/document.xml')
    root = ET.fromstring(xml_content)
    text_list = [elem.text for elem in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if elem.text]
    full_text = ''.join(text_list)
    
with open(r"C:\Users\PC\Documents\AI Sales OS\extracted_text.txt", 'w', encoding='utf-8') as f:
    f.write(full_text)

print("Extracted text saved to extracted_text.txt")
print(f"Total length: {len(full_text)} characters")
print("\nFirst 2000 characters:")
print(full_text[:2000])
