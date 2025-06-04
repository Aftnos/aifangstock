import csv
import os

class BarcodeModel:
    FILENAME = 'barcodes.csv'
    HEADER = ['条形码', '商品名称']

    def __init__(self):
        if not os.path.exists(self.FILENAME):
            with open(self.FILENAME, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.HEADER)
                writer.writeheader()

    def get_all(self) -> list:
        rows = []
        with open(self.FILENAME, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        return rows

    def add(self, barcode: str, name: str) -> bool:
        rows = self.get_all()
        for r in rows:
            if r['条形码'] == barcode:
                return False
        with open(self.FILENAME, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.HEADER)
            writer.writerow({'条形码': barcode, '商品名称': name})
        return True

    def remove(self, barcode: str) -> bool:
        rows = self.get_all()
        new = [r for r in rows if r['条形码'] != barcode]
        if len(new) == len(rows):
            return False
        with open(self.FILENAME, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.HEADER)
            writer.writeheader()
            writer.writerows(new)
        return True

    def get_name(self, barcode: str) -> str:
        for r in self.get_all():
            if r['条形码'] == barcode:
                return r['商品名称']
        return ''
