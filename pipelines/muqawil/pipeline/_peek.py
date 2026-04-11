import json
with open(r"C:\Users\PC\Documents\AI Sales OS\muqawil_pipeline\cleaned_contractors.json", encoding="utf-8") as f:
    data = json.load(f)
print("COUNT:", len(data))
print("KEYS:", list(data[0].keys()))
print("SAMPLE:")
import pprint
pprint.pprint(data[0])
